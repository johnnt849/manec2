import boto3
import json
import os
import time
import subprocess

import manec2
from manec2.ec2.instance_type import Instance


def query_ctx_instance_info(region, ctx, ssh_user='ubuntu', ssh_key='~/.ssh/virginia.pem'):
	ec2_cli = boto3.client('ec2', region_name=region)
	response = ec2_cli.describe_instances(
		Filters=[
			{
				"Name": 'tag:Name',
				"Values": [ctx]
			},
			{
				"Name": 'instance-state-name',
				"Values": ['stopped', 'stopping', 'pending', 'running']
			}
		]
	)

	instances = []
	for res in response['Reservations']:
		for inst in res['Instances']:
			inst_id = inst['InstanceId']
			inst_type = inst['InstanceType']
			inst_place = inst['Placement']['AvailabilityZone']
			state = inst['State']['Name']
			prip = '0'
			pubip = '0'
			dns = '0'
			prip = inst['PrivateIpAddress']
			if state ==  'running':
				pubip = inst['PublicIpAddress']
				dns = inst['PublicDnsName']
			instances.append(Instance(inst_id, inst_type, inst_place, prip, pubip,
				dns, state, ssh_user, ssh_key))

	instances.sort(key=lambda x : x.id)
	return instances

def get_contexts(options):
	ec2_cli = boto3.client('ec2', region_name=options.region)
	response = ec2_cli.describe_instances(
		Filters=[
			{
				"Name": 'instance-state-name',
				"Values": ['stopped', 'stopping', 'pending', 'running']
			}
		]
	)

	contexts = set()
	for res in response['Reservations']:
		for inst in res['Instances']:
			if 'Tags' in inst:
				for pair in inst['Tags']:
					if pair['Key'] == 'Name':
						contexts.add(pair['Value'])

	print('Contexts:')
	for i, ctx in enumerate(contexts):
		print(f'  {i:2d}  {ctx}')

def create_instances(options):
	if options.ctx == 'all':
		print("Context name 'all' is reserved. Choose another name")
		exit(17)

	ec2 = boto3.resource('ec2', region_name=options.region)

	if options.json:
		launch_params = json.load(open(options.json, 'r'))
		print(f'Launching with args {launch_params}')

		response = ec2.create_instances(**launch_params)
		instance_ids = [inst.id for inst in response]
		print("Created instances", instance_ids)

		return

	if options.ami == None:
		print("Please provide an AMI")
		exit(13)

	args = {
		'ImageId': options.ami,
		'InstanceType': options.type,
		'MinCount': options.cnt,
		'MaxCount': options.cnt,
		'KeyName': options.key_pair,
		'TagSpecifications': [
			{
				'ResourceType': 'instance',
				'Tags': [
					{
						'Key': 'Name',
						'Value': options.ctx
					}
				]
			}
		]
	}

	if options.type != 't2.micro':
		args['EbsOptimized'] = True

	if options.region == 'us-east-1':
		args['SecurityGroupIds'] = ['sg-098524cf5a5d0011f']
	elif options.region == 'us-east-2':
		args['SecurityGroupIds'] = ['sg-0a98f6952f8c78610']
	elif options.region == 'us-west-2':
		args['SecurityGroupIds'] = ['sg-087e10932df344958']
	
	if options.az != None:
		args['Placement'] = { 'AvailabilityZone': options.az }

	if options.pg != None:
		if 'Placement' not in args:
			args['Placement'] = { }

		args['Placement'].update({ 'GroupName' : options.pg })

	if options.spot:
		args['InstanceMarketOptions'] = {
			'MarketType': 'spot',
			'SpotOptions': {
				'SpotInstanceType': 'one-time',
				'InstanceInterruptionBehavior': 'terminate',
			}
		}

	print(f'Launching with args {args}')

	response = ec2.create_instances(**args)
	instance_ids = [inst.id for inst in response]
	print("Created instances", instance_ids)

def terminate_instances(options):
	for ctx in options.ctx:
		current_instances = query_ctx_instance_info(options.region, ctx)

		ec2_cli = boto3.client('ec2', region_name=options.region)
		msg = f"Are you sure you want to terminate " + \
			f"{'**ALL** instances' if options.indices == -1 else f'instances {options.indices}'} " \
			+ f"in context '{options.ctx}'?\nType 'terminate' to confirm\n"
		confirm = input(msg)

		if confirm != 'terminate':
			return

		instance_ids = [inst.id for inst in current_instances] if options.indices == -1 \
			else [current_instances[i].id for i in options.indices]
		if options.indices != -1:
			ec2_cli.terminate_instances(InstanceIds=instance_ids)
			print("Terminating instances", ", ".join([str(id) for id in instance_ids]))
		else:
			ec2_cli.terminate_instances(InstanceIds=instance_ids)
			print("Terminating instances", ", ".join([str(id) for id in instance_ids]))

def start_instances(options):
	for ctx in options.ctx:
		current_instances = query_ctx_instance_info(options.region, ctx)
		ec2_cli = boto3.client('ec2', region_name=options.region)
		instance_ids = [inst.id for inst in current_instances]
		if options.indices != -1:
			instance_ids = [instance_ids[i] for i in options.indices]

		ec2_cli.start_instances(InstanceIds=instance_ids)
		print(f"Starting '{ctx}' instances", ", ".join([str(id) for id in instance_ids]))

def stop_instances(options):
	for ctx in options.ctx:
		current_instances = query_ctx_instance_info(options.region, ctx)
		ec2_cli = boto3.client('ec2', region_name=options.region)
		instance_ids = [inst.id for inst in current_instances]
		if options.indices != -1:
			instance_ids = [instance_ids[i] for i in options.indices]

		ec2_cli.stop_instances(InstanceIds=instance_ids)
		print(f"Stopping '{ctx}' instances", ", ".join([str(id) for id in instance_ids]))

def reboot_instances(options):
	for ctx in options.ctx:
		current_instances = query_ctx_instance_info(options.region, ctx)
		ec2_cli = boto3.client('ec2', region_name=options.region)
		instance_ids = [inst.id for inst in current_instances]
		if options.indices!= -1:
			instance_ids = [instance_ids[i] for i in options.indices]

		ec2_cli.reboot_instances(InstanceIds=instance_ids)
		print(f"Rebooting '{ctx}' instances", ", ".join([str(id) for id in instance_ids]))

def print_full_info(indices, ctx, instance_info):
	print(str(len(instance_info)) + " instances:")
	for i in indices:
		inst = instance_info[i]
		print("  {:2d}  {}  {}  {}  {:15}  {}".format(i, inst.id, inst.type,
			inst.placement, inst.pr_ip, inst.last_observed_state))

def get_instance_info(options):
	for i, ctx in enumerate(options.ctx):
		current_instances = query_ctx_instance_info(options.region, ctx)
		if len(current_instances) == 0:
			print(f"Context '{ctx}' has no live instances")
			return

		if not options.text:
			print("Context '" + ctx + "'")
		indices = range(len(current_instances)) if options.indices == -1 else options.indices
		for ind in indices:
			inst = current_instances[ind]

			msg = ''
			if options.pubip:
				msg = inst.pub_ip
			elif options.dns:
				msg = inst.dns
			elif options.prip:
				msg = inst.pr_ip
			elif options.type:
				msg = inst.type
			elif options.zone:
				msg = inst.placement
			elif options.state:
				msg = inst.last_observed_state
			else:
				print_full_info(indices, ctx, current_instances)
				break

			msg = msg if options.text else "  ".join(["", str(ind), msg])
			print(msg)

		if i < len(options.ctx) - 1:
			print()

def ssh_to_instance(options):
	current_instances = query_ctx_instance_info(options.region, options.ctx)

	if options.all:
		## Filter for instances that are currently running
		current_instances = [inst for inst in current_instances if inst.last_observed_state == 'running']
		if len(current_instances) == 0:
			print(f'No running instances in context {options.ctx}')
			exit(13)
	else:
		current_instances = [current_instances[i] for i in options.indices]
		for inst in current_instances:
			if inst.pub_ip == '0':
				print("At least one public IP is '0'. Make sure instance is running")
				exit(13)

	if options.user == '' and current_instances[0].user == '':
		print("No cached user for this instance. Please provide a user (--user)")
		exit(15)

	ssh_user = current_instances[0].user
	if options.user != '':
		ssh_user = options.user

	ssh_key = current_instances[0].key
	if options.key != '':
		ssh_key = options.key

	remote_access_opts = []
	if ssh_key != '':
		remote_access_opts = ['-i', ssh_key]
		remote_access_opts = remote_access_opts + ['-t'] if options.sudo else remote_access_opts

	processes = []
	for inst in current_instances:
		ssh_command = ['ssh'] + remote_access_opts \
			+ [ssh_user + '@' + inst.dns] \
			+ options.comm.split()

		if options.parallel:
			processes.append(subprocess.Popen(ssh_command))
		else:
			subprocess.run(ssh_command)

	if options.parallel:
		for proc in processes:
			proc.wait()

def rsync_instance(options):
	current_instances = query_ctx_instance_info(options.region, options.ctx)
	if options.indices == -1:
		current_instances = [inst for inst in current_instances \
							if inst.last_observed_state == 'running']
		if len(current_instances) == 0:
			print(f'No running instances in context {options.ctx}')
			exit(13)
	else:
		current_instances = [current_instances[i] for i in options.indices]

	for inst in current_instances:
		if inst.pub_ip == '0':
			print("At least one public IP is '0'. Make sure instance is running")
			exit(13)

	if options.user == '' and current_instances[0].user == '':
		print("No cached user for this instance. Please provide a user (--user)")
		exit(15)

	ssh_user = current_instances[0].user
	if options.user != '':
		ssh_user = options.user

	ssh_key = current_instances[0].key
	if options.key != '':
		ssh_key = options.key

	remote_access_opts = []
	if ssh_key != '':
		remote_access_opts = ['-i', ssh_key]

	confirmed = False
	processes = []
	for inst in current_instances:
		if options.force:
			delete_dir_command = 'rm -rf ' + options.location
			create_dir_command = 'mkdir -p ' + options.location
			ssh_command_base = ['ssh'] + remote_access_opts \
				+ [ssh_user + '@' + inst.dns]
			if not confirmed:
				confirm = input("Are you sure you want to run 'rm -rf' on '"
					+ options.location + "'? (yes/no)\n")
				confirmed = confirm == 'yes'
			if confirmed:
				subprocess.run(ssh_command_base + delete_dir_command.split())
				subprocess.run(ssh_command_base + create_dir_command.split())
			else:
				return

		exclusions = ['--exclude'] + ' --exclude '.join(options.exclude).split() \
			if len(options.exclude) != 0 else []
		rsync_command = ['rsync', '-auzh', '-zz'] \
			+ ['-e'] + [' '.join(["ssh"] + remote_access_opts)] \
			+ exclusions + [options.file] \
			+ [ssh_user + '@' + inst.dns+ ":" + options.location]

		if options.parallel:
			processes.append(subprocess.Popen(rsync_command))
		else:
			subprocess.run(rsync_command)

	if options.parallel:
		for proc in processes:
			proc.wait()

def scp_instance(options):
	current_instances = query_ctx_instance_info(options.region, options.ctx)
	if options.indices == -1:
		current_instances = [inst for inst in current_instances \
							if inst.last_observed_state == 'running']
		if len(current_instances) == 0:
			print(f'No running instances in context {options.ctx}')
			exit(13)
	else:
		current_instances = [current_instances[i] for i in options.indices]

	for inst in current_instances:
		if inst.pub_ip == '0':
			print("At least one public IP is '0'. Make sure instance is running")
			exit(13)

	if options.user == '' and current_instances[0].user == '':
		print("No cached user for this instance. Please provide a user (--user)")
		exit(15)

	ssh_user = current_instances[0].user
	if options.user != '':
		ssh_user = options.user

	ssh_key = current_instances[0].key
	if options.key != '':
		ssh_key = options.key

	remote_access_opts = []
	if ssh_key != '':
		remote_access_opts = ['-i', ssh_key]

	for i, inst in enumerate(current_instances):
		scp_cmd = ['scp'] + remote_access_opts
		if options.put:
			scp_cmd = scp_cmd + [options.file, ssh_user + '@' + inst.dns + ':' + options.location]
		elif options.get:
			scp_cmd = scp_cmd + [ssh_user + '@' + inst.dns + ':' + options.file, options.location]

		subprocess.run(scp_cmd)
import boto3
import json
import os
import time
import subprocess
import sys
import yaml


import manec2
from manec2.utils.instance_type import Instance
from manec2.utils.load_defaults import get_default_config
from manec2.utils.constants import RED_TEXT, RESET_TEXT

def create_boto3_client(profile, region, service='ec2'):
	session = boto3.Session(profile_name=profile)
	return session.client(service, region_name=region)

def query_ctx_instance_info(ctx, options):
	ec2_cli = create_boto3_client(options.profile, options.region)

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
				dns, state))

	instances.sort(key=lambda x : x.id)
	return instances

def get_contexts(options):
	ec2_cli = create_boto3_client(options.profile, options.region)
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

	# Can't use boto3.client here. Use boto3.resource
	session = boto3.Session(profile_name=options.profile)
	ec2 = boto3.resource('ec2', region_name=options.region)

	if options.file:
		launch_params = yaml.safe_load(open(options.file, 'r'))
		print(f'Launching with args {launch_params}')

		response = ec2.create_instances(**launch_params)
		instance_ids = [inst.id for inst in response]
		print("Created instances", instance_ids)

		return

	default_config = get_default_config(options)

	if options.ami == None:
		print("Please provide an AMI")
		exit(13)

	args = {
		'ImageId': options.ami,
		'InstanceType': options.type,
		'MinCount': options.cnt,
		'MaxCount': options.cnt,
		'KeyName': default_config['InstanceOptions']['KeyPair'] if options.key_pair == None else options.key_pair,
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

	args['SecurityGroupIds'] = default_config['InstanceOptions']['SecurityGroups'][options.region]
	
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
	ec2_cli = boto3.client('ec2', region_name=options.region)
	for ctx in options.ctx:
		current_instances = query_ctx_instance_info(ctx, options)

		msg = f"Are you sure you want to " + RED_TEXT + "terminate " + \
			f"{'**ALL** instances' if options.indices == -1 else f'instances {options.indices}'} " \
			+ RESET_TEXT + f"in context '{ctx}'?\nType '" + RED_TEXT + "terminate" + RESET_TEXT + "' to confirm\n"
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
	ec2_cli = boto3.client('ec2', region_name=options.region)
	for ctx in options.ctx:
		current_instances = query_ctx_instance_info(ctx, options)
		instance_ids = [inst.id for inst in current_instances]
		if options.indices != -1:
			instance_ids = [instance_ids[i] for i in options.indices]

		ec2_cli.start_instances(InstanceIds=instance_ids)
		print(f"Starting '{ctx}' instances", ", ".join([str(id) for id in instance_ids]))

def stop_instances(options):
	ec2_cli = boto3.client('ec2', region_name=options.region)
	for ctx in options.ctx:
		current_instances = query_ctx_instance_info(ctx, options)
		instance_ids = [inst.id for inst in current_instances]
		if options.indices != -1:
			instance_ids = [instance_ids[i] for i in options.indices]

		ec2_cli.stop_instances(InstanceIds=instance_ids)
		print(f"Stopping '{ctx}' instances", ", ".join([str(id) for id in instance_ids]))

def reboot_instances(options):
	ec2_cli = boto3.client('ec2', region_name=options.region)
	for ctx in options.ctx:
		current_instances = query_ctx_instance_info(ctx, options)
		instance_ids = [inst.id for inst in current_instances]
		if options.indices!= -1:
			instance_ids = [instance_ids[i] for i in options.indices]

		ec2_cli.reboot_instances(InstanceIds=instance_ids)
		print(f"Rebooting '{ctx}' instances", ", ".join([str(id) for id in instance_ids]))

def create_instance_image(options):
	current_instances = query_ctx_instance_info(options.ctx, options)
	instance_to_image = current_instances[options.index]
	ec2_cli = boto3.client('ec2', region_name=options.region)

	crt_img_response = ec2_cli.create_image(
		Description=options.description,
		InstanceId=instance_to_image.id,
		Name=options.image_name
	)

	image_id = crt_img_response['ImageId']

	if options.wait:
		while True:
			desc_image_response = ec2_cli.describe_images(ImageIds=[image_id])
			current_state = desc_image_response['Images'][0]['State']
			if current_state == 'available':
				break

			if current_state != 'pending':
				print(f'Image has status {current_state}. Ending...', file=sys.stderr)
				sys.exit(13)

			time.sleep(5)

		print(f'Image {image_id} available for use')

def print_full_info(indices, ctx, instance_info):
	print(str(len(instance_info)) + " instances:")
	for i in indices:
		inst = instance_info[i]
		print("  {:2d}  {}  {}  {}  {:15}  {}".format(i, inst.id, inst.type,
			inst.placement, inst.pr_ip, inst.last_observed_state))

def get_instance_info(options):
	for i, ctx in enumerate(options.ctx):
		current_instances = query_ctx_instance_info(ctx, options)
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

def _ssh_failure(inst, trials):
	time.sleep(3)

	if trials > 20:
		print(f'Tried to access instances {inst.id} SSH 20 times. Failing...')
		exit(15)

	if trials % 3 == 0:
		print(f'Connection timed out. Retrying...')

def _get_ssh_options(options):
	default_config = get_default_config(options)

	ssh_user = options.user if options.user is not None else default_config['SSHOptions'].get('User', None)
	if ssh_user is None:
		print("No default user found. Please provide a user (--user)")
		exit(13)

	ssh_key = options.key if options.key is not None else default_config['SSHOptions'].get('Key', None)
	if ssh_key is None:
		print("No default key found. Please provide an SSH key (--key)")
		exit(13)

	return ssh_user, ssh_key

def ssh_to_instance(options):
	current_instances = query_ctx_instance_info(options.ctx, options)

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

	ssh_user, ssh_key = _get_ssh_options(options)

	remote_access_opts = []
	if ssh_key != '':
		remote_access_opts = ['-i', ssh_key]
		remote_access_opts = remote_access_opts + ['-t'] if options.sudo else remote_access_opts

	processes = []
	for inst in current_instances:
		ssh_command_base = ['ssh'] + remote_access_opts \
			+ [ssh_user + '@' + inst.dns] \

		ssh_command_test = ssh_command_base \
			+ ['exit']

		ssh_command_final = ssh_command_base \
			+ options.comm.split()

		if options.wait:
			trials = 0
			while True:
				try:
					retcode = subprocess.run(ssh_command_test, timeout=5).returncode
					if retcode != 0:
						_ssh_failure(inst, trials)
					else:
						break
				except subprocess.TimeoutExpired:
					_ssh_failure(inst, trials)

				trials +=1

		if options.parallel:
			processes.append(subprocess.Popen(ssh_command_final))
		else:
			subprocess.run(ssh_command_final)

	if options.parallel:
		for proc in processes:
			proc.wait()

def rsync_instance(options):
	current_instances = query_ctx_instance_info(options.ctx, options)
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

	ssh_user, ssh_key = _get_ssh_options(options)

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
	current_instances = query_ctx_instance_info(options.ctx, options)
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

	ssh_user, ssh_key = _get_ssh_options(options)

	remote_access_opts = []
	if ssh_key != '':
		remote_access_opts = ['-i', ssh_key]

	recursive_opts = []
	if options.recursive:
		recursive_opts = ['-r']

	processes = []
	for i, inst in enumerate(current_instances):
		scp_cmd = ['scp'] + recursive_opts + remote_access_opts
		if options.put:
			scp_cmd = scp_cmd + [options.file, ssh_user + '@' + inst.dns + ':' + options.location]
		elif options.get:
			scp_cmd = scp_cmd + [ssh_user + '@' + inst.dns + ':' + options.file, options.location]

		if options.parallel:
			processes.append(subprocess.Popen(scp_cmd))
		else:
			subprocess.run(scp_cmd)

	for proc in processes:
		proc.wait()
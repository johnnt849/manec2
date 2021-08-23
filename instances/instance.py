import boto3
import json
import os
import time
import subprocess

import manec2
from manec2.instances import INSTANCE_CACHE_DIR, INSTANCE_CACHE_FILE
from manec2.instances.instance_type import Instance, deserialize


def read_instance_cache_file():
	instance_info = {}
	if os.path.isfile(INSTANCE_CACHE_FILE):
		instance_info = json.load(open(INSTANCE_CACHE_FILE, 'r'))

	for ctx in instance_info.keys():
		instance_info[ctx] = [deserialize(json_rep) for json_rep in instance_info[ctx]]
		instance_info[ctx].sort(key=lambda x : x.id)

	return instance_info

def write_instance_cache_file(instance_info):
	if not os.path.exists(INSTANCE_CACHE_DIR):
		os.mkdir(INSTANCE_CACHE_DIR)

	for ctx in instance_info.keys():
		instance_info[ctx].sort(key=lambda x : x.id)
		instance_info[ctx] = [inst.serialize() for inst in instance_info[ctx]]

	json.dump(instance_info, open(INSTANCE_CACHE_FILE, 'w'), indent=4)

def update_instance_info(instance_ids, ssh_user, ssh_key):
	ec2_cli = boto3.client('ec2')
	response = ec2_cli.describe_instances(InstanceIds=instance_ids)
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
			if state != 'terminated':
				prip = inst['PrivateIpAddress']
			if state ==  'running':
				pubip = inst['PublicIpAddress']
				dns = inst['PublicDnsName']
			instances.append(Instance(inst_id, inst_type, inst_place, prip, pubip,
				dns, state, ssh_user, ssh_key))

	instances.sort(key=lambda x : x.id)
	return instances

def create_instances(options):
	if options.ctx == 'all':
		print("Context name 'all' is reserved. Choose another name")
		exit(17)

	instance_info = read_instance_cache_file()
	ec2 = boto3.resource('ec2')
	instances = []

	if options.ami == None:
		print("Please provide an AMI")
		exit(13)

	args = {
		'ImageId': options.ami,
		'InstanceType': options.type,
		'MinCount': options.cnt,
		'MaxCount': options.cnt,
		'SecurityGroupIds': ['sg-098524cf5a5d0011f'],
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

	if options.az != None:
		args['Placement'] = { 'AvailabilityZone': options.az }
		if options.az[:-1] == 'us-east-2':
			args['SecurityGroupIds'] = ['sg-0a98f6952f8c78610']

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

	print(args)

	response = ec2.create_instances(**args)
	instance_ids = [inst.id for inst in response]
	print("CREATED INSTANCES", instance_ids)
	time.sleep(1)
	created_instances = update_instance_info(instance_ids, options.user, options.key)

	if options.ctx not in instance_info:
		instance_info[options.ctx] = []

	instance_info[options.ctx] += created_instances
	instance_info[options.ctx].sort(key=lambda x : x.id)

	write_instance_cache_file(instance_info)

def terminate_instances(options):
	instance_info = read_instance_cache_file()

	contexts = instance_info.keys()
	if options.ctx != 'all':
		contexts = [options.ctx]

	ec2_cli = boto3.client('ec2')
	for ctx in contexts:
		msg = f"Are you sure you want to terminate " + \
			f"{'**ALL** instances' if options.indices == -1 else f'instances {options.indices}'} " \
			+ f"in context '{ctx}'?\nType 'terminate' to confirm\n"
		confirm = input(msg)

		if confirm != 'terminate':
			continue

		instance_ids = [inst.id for inst in instance_info[ctx]]
		if options.indices != -1:
			instance_ids = [instance_ids[i] for i in options.indices]
			ec2_cli.terminate_instances(InstanceIds=instance_ids)
			print("Terminating instances", ", ".join([str(id) for id in instance_ids]))
			reverse_sorted_inds = sorted(options.indices, reverse=True)
			for ind in reverse_sorted_inds:
				del instance_info[ctx][ind]
		else:
			ec2_cli.terminate_instances(InstanceIds=instance_ids)
			print("Terminating instances", ", ".join([str(id) for id in instance_ids]))
			del instance_info[ctx]

	write_instance_cache_file(instance_info)

def start_instances(options):
	instance_info = read_instance_cache_file()

	contexts = instance_info.keys()
	if options.ctx != 'all':
		contexts = [options.ctx]

	ec2_cli = boto3.client('ec2')
	for ctx in contexts:
		instance_ids = [inst.id for inst in instance_info[ctx]]
		if options.indices != -1:
			instance_ids = [instance_ids[i] for i in options.indices]

		ec2_cli.start_instances(InstanceIds=instance_ids)
		print("Starting instances", ", ".join([str(id) for id in instance_ids]))

	write_instance_cache_file(instance_info)

def stop_instances(options):
	instance_info = read_instance_cache_file()

	contexts = instance_info.keys()
	if options.ctx != 'all':
		contexts = [options.ctx]

	ec2_cli = boto3.client('ec2')
	for ctx in contexts:
		instance_ids = [inst.id for inst in instance_info[ctx]]
		if options.indices != -1:
			instance_ids = [instance_ids[i] for i in options.indices]

		ec2_cli.stop_instances(InstanceIds=instance_ids)
		print("Stopping instances", ", ".join([str(id) for id in instance_ids]))
		for inst in instance_info[ctx]:
			inst.pub_ip = '0'
			inst.dns = '0'

	write_instance_cache_file(instance_info)

def reboot_instances(options):
	instance_info = read_instance_cache_file()

	contexts = instance_info.keys()
	if options.ctx != 'all':
		contexts = [options.ctx]

	ec2_cli = boto3.client('ec2')
	for ctx in contexts:
		instance_ids = [inst.id for inst in instance_info[ctx]]
		if options.indices!= -1:
			instance_ids = [instance_ids[i] for i in options.indices]

		ec2_cli.reboot_instances(InstanceIds=instance_ids)
		print("Rebooting instances", ", ".join([str(id) for id in instance_ids]))

	write_instance_cache_file(instance_info)

def call_update_instance_info(options):
	instance_info = read_instance_cache_file()

	contexts = instance_info.keys()
	if options.ctx != 'all':
		contexts = [options.ctx]

	for ctx in contexts:
		ctx_instance_ids = [inst.id for inst in instance_info[ctx]]
		ssh_user = options.user if len(options.user) != 0 else instance_info[ctx][0].user
		ssh_key = options.key if len(options.key) != 0 else instance_info[ctx][0].key
		instance_info[ctx] = update_instance_info(ctx_instance_ids, ssh_user, ssh_key)

	write_instance_cache_file(instance_info)

def print_full_info(ctx, instance_info):
	ctx_instance_ids = [inst.id for inst in instance_info[ctx]]
	ssh_user = instance_info[ctx][0].user
	ssh_key = instance_info[ctx][0].key
	instance_info[ctx] = update_instance_info(ctx_instance_ids, ssh_user, ssh_key)
	print(str(len(instance_info[ctx])) + " instances:")
	for i, inst in enumerate(instance_info[ctx]):
		print("  {:2d}  {}  {}  {}  {:15}  {}".format(i, inst.id, inst.type,
			inst.placement, inst.pr_ip, inst.last_observed_state))

def get_instance_info(options):
	instance_info = read_instance_cache_file()

	contexts = instance_info.keys()
	if options.ctx != 'all':
		contexts = [options.ctx]

	for ctx in contexts:
		if not options.text:
			print("Context '" + ctx + "'")
		instances = instance_info[ctx] if options.indices == -1 \
			else [instance_info[ctx][i] for i in options.indices]
		i = 0 if options.indices == -1 else options.indices[0]
		for inst in instances:
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
				print_full_info(ctx, instance_info)
				break

			msg = msg if options.text else "  ".join(["", str(i), msg])
			print(msg)

			i += 1

	write_instance_cache_file(instance_info)

def ssh_to_instance(options):
	instance_info = read_instance_cache_file()

	current_instances = instance_info[options.ctx] if options.all \
		else [instance_info[options.ctx][i] for i in options.indices]

	for inst in current_instances:
		if inst.pub_ip == '0':
			instance_info[options.ctx] = \
				update_instance_info([inst.id for inst in instance_info[options.ctx]],
				current_instances[0].user, current_instances[0].key)

	current_instances = instance_info[options.ctx] if options.all \
		else [instance_info[options.ctx][i] for i in options.indices]

	if options.all:
		## Filter for instances that are currently running
		current_instances = [inst for inst in current_instances if inst.last_observed_state == 'running']
		if len(current_instances) == 0:
			print(f'No running instances in context {options.ctx}')
			exit(13)
	else:
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
	instance_info = read_instance_cache_file()

	current_instances = instance_info[options.ctx]
	if options.indices != -1:
		current_instances = [current_instances[i] for i in options.indices]

	for inst in current_instances:
		if inst.pub_ip == '0':
			instance_info[options.ctx] = \
				update_instance_info([inst.id for inst in instance_info[options.ctx]],
				current_instances[0].user, current_instances[0].key)

	current_instances = instance_info[options.ctx]
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
	instance_info = read_instance_cache_file()

	current_instances = instance_info[options.ctx]
	if options.indices != -1:
		current_instances = [current_instances[i] for i in options.indices]

	for inst in current_instances:
		if inst.pub_ip == '0':
			instance_info[options.ctx] = \
				update_instance_info([inst.id for inst in instance_info[options.ctx]],
				current_instances[0].user, current_instances[0].key)

	current_instances = instance_info[options.ctx]
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

	scp_cmd = ['scp'] + remote_access_opts
	for inst in current_instances:
		if options.put:
			scp_cmd = scp_cmd + [options.file, ssh_user + '@' + inst.dns + ':' + options.location]
		elif options.get:
			scp_cmd = scp_cmd + [ssh_user + '@' + inst.dns + ':' + options.file, options.location]

		subprocess.run(scp_cmd)
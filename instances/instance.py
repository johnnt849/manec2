import boto3
import json
import os
import time
import subprocess

import manec2
from manec2.instances import INSTANCE_CACHE_FILE
from manec2.instances.instance_type import Instance, deserialize


def read_instance_cache_file():
	instance_info = {}
	if os.path.isfile(INSTANCE_CACHE_FILE):
		instance_info = json.load(open(INSTANCE_CACHE_FILE, 'r'))

	for ctx in instance_info.keys():
		instance_info[ctx] = [deserialize(json_rep) for json_rep in instance_info[ctx]]

	return instance_info

def write_instance_cache_file(instance_info):
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
			if state != 'terminated':
				prip = inst['PrivateIpAddress']
			if state ==  'running':
				pubip = inst['PublicIpAddress']
			instances.append(Instance(inst_id, inst_type, inst_place, prip, pubip, state,
				ssh_user, ssh_key))

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
		'SecurityGroupIds': ['sg-098524cf5a5d0011f']
	}

	if options.type != 't2.micro':
		args['EbsOptimized'] = True

	if options.az != None:
		args['Placement'] = { 'AvailabilityZone': options.az }
		if options.az[:-1] == 'us-east-2':
			args['SecurityGroupIds'] = ['sg-0a98f6952f8c78610']


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
		confirm = input("Are you sure you want to terminate ALL instances in context "
			+ ctx + "?\nType 'terminate' to confirm.\n")

		if confirm != 'terminate':
			continue

		instance_ids = [inst.id for inst in instance_info[ctx]]
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
		if options.one:
			instance_ids = [instance_ids[0]]

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
		if options.one:
			instance_ids = [instance_ids[0]]

		ec2_cli.stop_instances(InstanceIds=instance_ids)
		print("Stopping instances", ", ".join([str(id) for id in instance_ids]))
		for inst in instance_info[ctx]:
			inst.pub_ip = '0'

	write_instance_cache_file(instance_info)

def call_update_instance_info(options):
	instance_info = read_instance_cache_file()

	contexts = instance_info.keys()
	if options.ctx != 'all':
		contexts = [options.ctx]

	for ctx in contexts:
		ctx_instance_ids = [inst.id for inst in instance_info[ctx]]
		ssh_user = instance_info[ctx][0].user
		ssh_key = instance_info[ctx][0].key
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
		print("Context '" + ctx + "'")
		instances = instance_info[ctx] if options.index == -1 else [instance_info[ctx][options.index]]
		i = 0 if options.index == -1 else options.index
		for inst in instances:
			if options.pubip:
				print(i, " ", inst.pub_ip)
			elif options.prip:
				print(i, " ",  inst.pr_ip)
			elif options.type:
				print(i, " ",  inst.type)
			elif options.zone:
				print(i, " ", inst.placement)
			elif options.state:
				print(i, " ", inst.state)
			else:
				print_full_info(ctx, instance_info)
				break

			i += 1

	write_instance_cache_file(instance_info)


def ssh_to_instance(options):
	instance_info = read_instance_cache_file()

	current_instance = instance_info[options.ctx][options.index]

	if current_instance.pub_ip == '0':
		instance_info[options.ctx] =
			update_instance_info([id for id in instance_info[options.ctx]],
			current_instance.user, current_instance.ssh_key)
		current_instance = instance_info[options.ctx][options.index]
		if current_instance.pub_ip = '0':
			print("Public IP is '0'. Make sure instance is running")
			exit(13)

	if options.user == '' and current_instance.user == '':
		print("No cached user for this instance. Please provide a user (--user)")
		exit(15)

	ssh_user = current_instance.user
	if options.user != '':
		ssh_user = options.user

	ssh_key = current_instance.key
	if options.key != '':
		ssh_key = options.key

	remote_access_opts = []
	if ssh_key != '':
		remote_access_opts = ['-i', ssh_key]
	ssh_command = ['ssh'] + remote_access_opts \
		+ [ssh_user + '@' + current_instance.pub_ip] \
		+ options.comm.split()

	subprocess.run(ssh_command)

def rsync_instance(options):
	pass

def scp_instance(options):
	pass

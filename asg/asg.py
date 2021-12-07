import boto3
import json
import os
import time
import subprocess

import manec2
from manec2.utils.instance_type import Instance

def query_ctx_instance_info(region, instance_ids, ssh_user='ubuntu', ssh_key='~/.ssh/oregon.pem'):
	ec2_cli = boto3.client('ec2', region_name=region)
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
			try:
				prip = inst['PrivateIpAddress']
			except KeyError as e:
				## This is probably terminating. Just skip it
				continue
			if state ==  'running':
				pubip = inst['PublicIpAddress']
				dns = inst['PublicDnsName']
			instances.append(Instance(inst_id, inst_type, inst_place, prip, pubip,
				dns, state, ssh_user, ssh_key))

	instances.sort(key=lambda x : x.id)
	return instances

def list_groups(options):
	asg = boto3.client('autoscaling')
	response = asg.describe_auto_scaling_groups()

	for group in response['AutoScalingGroups']:
		print(group['AutoScalingGroupName'])

def ssh_command(options):
	asg = boto3.client('autoscaling')
	asg_response = asg.describe_auto_scaling_groups(
		AutoScalingGroupNames=[options.auto_scaling_group_name])['AutoScalingGroups'][0]['Instances']
	instance_ids = []
	if options.all:
		instance_ids = sorted([inst['InstanceId'] for inst in asg_response])
	else:
		instance_ids = sorted([inst['InstanceId'] for i, inst in enumerate(asg_response) if i in options.indices])

	instances = query_ctx_instance_info(options.region, instance_ids)
	instances = [inst for inst in instances if inst.last_observed_state == 'running']

	if len(instances) == 0:
		print(f'No running instances in context {options.ctx}')
		exit(13)

	ssh_user = instances[0].user
	if options.user != '':
		ssh_user = options.user

	ssh_key = instances[0].key
	if options.key != '':
		ssh_key = options.key

	remote_access_opts = []
	if ssh_key != '':
		remote_access_opts = ['-i', ssh_key]

	processes = []
	for inst in instances:
		ssh_command = ['ssh'] + remote_access_opts \
			+ [ssh_user + '@' + inst.dns] \
			+ options.comm.split()

		if options.parallel:
			processes.append(subprocess.Popen(ssh_command))
		else:
			subprocess.run(ssh_command)

	for proc in processes:
		proc.wait()

def scale_group(options):
	asg = boto3.client('autoscaling')
	asg.set_desired_capacity(
		AutoScalingGroupName=options.auto_scaling_group_name,
		DesiredCapacity=options.size
	)

	print(f'Setting desired capacity of {options.auto_scaling_group_name} to {options.size}')

def group_info(options):
	asg = boto3.client('autoscaling')
	response = asg.describe_auto_scaling_groups(AutoScalingGroupNames=options.auto_scaling_group_names)

	for as_group in response['AutoScalingGroups']:
		name = as_group['AutoScalingGroupName']
		instances = as_group['Instances']
		print(f'Auto Scaling Group {name}\n{len(instances)} instances')
		for i, inst in enumerate(instances):
			print("  {:2d}  {}  {}  {}  {}".format(i, inst['InstanceId'],
				inst['InstanceType'], inst['AvailabilityZone'],
				inst['LifecycleState']))

		print()
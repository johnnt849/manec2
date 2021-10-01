import boto3
import json
import os
import time
import subprocess

import manec2

def list_groups(options):
	asg = boto3.client('autoscaling')
	response = asg.describe_auto_scaling_groups()

	for group in response['AutoScalingGroups']:
		print(group['AutoScalingGroupName'])
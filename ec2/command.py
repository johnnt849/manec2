import argparse
from multiprocessing import parent_process


NAME = 'instance manager'
HELP = None

def add_arguments(parser):
	subparsers = parser.add_subparsers(metavar='command')

	general_parser = argparse.ArgumentParser(add_help=False)
	general_parser.add_argument('--profile', type=str, default=None)
	general_parser.add_argument('--region', '-r', type=str, default=None)

	from manec2.ec2.command import get_contexts_command
	get_contexts_parser = subparsers.add_parser('contexts', help=None, parents=[general_parser])
	get_contexts_parser.set_defaults(command=get_contexts_command)

	from manec2.ec2.command import create_instances_command
	create_instance_parser = subparsers.add_parser('create', help=None, parents=[general_parser])
	create_instance_parser.set_defaults(command=create_instances_command)
	create_instance_parser.add_argument('--ctx', type=str, default=None)

	## Overrides any other specifications
	create_instance_parser.add_argument('--file', type=str, default=None)

	create_instance_parser.add_argument('--ami', type=str, default=None)
	create_instance_parser.add_argument('--type', type=str, default='t2.micro')
	create_instance_parser.add_argument('--cnt', type=int, default=1)
	create_instance_parser.add_argument('--az', type=str, default=None)
	create_instance_parser.add_argument('--pg', type=str, default=None)
	create_instance_parser.add_argument('--spot', action='store_true')
	create_instance_parser.add_argument('--key-pair', '-k', type=str, default=None)

	create_instance_parser.add_argument('--incremental', '-inc', action='store_true',
										default=False)

	from manec2.ec2.command import terminate_instances_command
	terminate_instance_parser = subparsers.add_parser('terminate', help=None, parents=[general_parser])
	terminate_instance_parser.set_defaults(command=terminate_instances_command)
	terminate_instance_parser.add_argument('ctx', type=str, nargs='+', default=None)
	terminate_instance_parser.add_argument('--indices', '-ids', type=int, nargs='+',
										default=-1)

	from manec2.ec2.command import start_instances_command
	start_instance_parser = subparsers.add_parser('start', help=None, parents=[general_parser])
	start_instance_parser.set_defaults(command=start_instances_command)
	start_instance_parser.add_argument('ctx', type=str, nargs='+', default=None)
	start_instance_parser.add_argument('--indices', '-ids', type=int, nargs='+',
									   default=-1)

	from manec2.ec2.command import stop_instances_command
	stop_instance_parser = subparsers.add_parser('stop', help=None, parents=[general_parser])
	stop_instance_parser.set_defaults(command=stop_instances_command)
	stop_instance_parser.add_argument('ctx', type=str, nargs='+', default=None)
	stop_instance_parser.add_argument('--indices', '-ids', type=int, nargs='+',
									  default=-1)

	from manec2.ec2.command import reboot_instances_command
	reboot_instance_parser = subparsers.add_parser('reboot', help=None, parents=[general_parser])
	reboot_instance_parser.set_defaults(command=reboot_instances_command)
	reboot_instance_parser.add_argument('ctx', type=str, nargs='+', default=None)
	reboot_instance_parser.add_argument('--indices', '-ids', type=int, nargs='+',
										default=-1)

	from manec2.ec2.command import create_instance_image_command
	image_instance_parser = subparsers.add_parser('image', help=None, parents=[general_parser])
	image_instance_parser.set_defaults(command=create_instance_image_command)
	image_instance_parser.add_argument('ctx', type=str, default=None)
	image_instance_parser.add_argument('--index', '-ind', type=int, default=0)
	image_instance_parser.add_argument('--image-name', '-n', type=str, default=None)
	image_instance_parser.add_argument('--description', '-desc', type=str, default='')
	image_instance_parser.add_argument('--wait', action='store_true', default=False)

	from manec2.ec2.command import info_instances_command
	info_instance_parser = subparsers.add_parser('info', help=None, parents=[general_parser])
	info_instance_parser.set_defaults(command=info_instances_command)
	info_instance_parser.add_argument('ctx', type=str, nargs='+', default=None)
	info_instance_parser.add_argument('--indices', '-ids', type=int, nargs='+',
									  default=-1)
	info_instance_parser.add_argument('--pubip', action='store_true')
	info_instance_parser.add_argument('--prip', action='store_true')
	info_instance_parser.add_argument('--dns', action='store_true')
	info_instance_parser.add_argument('--type', action='store_true')
	info_instance_parser.add_argument('--zone', action='store_true')
	info_instance_parser.add_argument('--state', action='store_true')
	info_instance_parser.add_argument('--text', action='store_true')

	from manec2.ec2.command import ssh_instance_command
	ssh_instance_parser = subparsers.add_parser('ssh', help=None, parents=[general_parser])
	ssh_instance_parser.set_defaults(command=ssh_instance_command)
	ssh_instance_parser.add_argument('ctx', type=str, default=None)
	ssh_instance_parser.add_argument('--indices', '-ids', type=int, nargs='+',
									 default=[0])
	ssh_instance_parser.add_argument('--all', '-a', action='store_true')

	ssh_instance_parser.add_argument('--user', '-u', type=str, default=None)
	ssh_instance_parser.add_argument('--key', '-i', type=str, default=None)
	ssh_instance_parser.add_argument('--comm', '-c', type=str, default='')

	ssh_instance_parser.add_argument('--parallel', '-p', action='store_true')
	ssh_instance_parser.add_argument('--sudo', '-s', action='store_true')
	ssh_instance_parser.add_argument('--wait', '-w', action='store_true')

	from manec2.ec2.command import rsync_instance_command
	rsync_instance_parser = subparsers.add_parser('rsync', help=None, parents=[general_parser])
	rsync_instance_parser.set_defaults(command=rsync_instance_command)
	rsync_instance_parser.add_argument('ctx', type=str, default='')
	rsync_instance_parser.add_argument('--user', '-u', type=str, default=None)
	rsync_instance_parser.add_argument('--key', '-i', type=str, default=None)
	rsync_instance_parser.add_argument('--exclude', '-e', nargs='+', type=str,
									   default='')
	rsync_instance_parser.add_argument('--file', '-f', type=str, default=None)
	rsync_instance_parser.add_argument('--location', '-l', type=str, default='.')
	rsync_instance_parser.add_argument('--indices', '-ids', type=int, nargs='+',
									   default=-1)
	rsync_instance_parser.add_argument('--parallel', '-p', action='store_true')
	rsync_instance_parser.add_argument('--force', action='store_true')

	from manec2.ec2.command import scp_instance_command
	scp_instance_parser = subparsers.add_parser('scp', help=None, parents=[general_parser])
	scp_instance_parser.set_defaults(command=scp_instance_command)
	scp_instance_parser.add_argument('ctx', type=str, default='')
	scp_instance_parser.add_argument('file', type=str, default=None)
	scp_instance_parser.add_argument('--user', '-u', type=str, default=None)
	scp_instance_parser.add_argument('--key', '-i', type=str, default=None)
	scp_instance_parser.add_argument('--get', action='store_true', default=False)
	scp_instance_parser.add_argument('--put', action='store_true', default=False)
	scp_instance_parser.add_argument('--location', '-l', type=str, default='.')
	scp_instance_parser.add_argument('--indices', '-ids', type=int, nargs='+',
									 default=-1)
	scp_instance_parser.add_argument('--parallel', '-p', action='store_true')


## Commands that interact with AWS infrastructure
def get_contexts_command(options):
	from .instance import get_contexts
	get_contexts(options)

def create_instances_command(options):
	from .instance import create_instances
	create_instances(options)

def terminate_instances_command(options):
	from .instance import terminate_instances
	terminate_instances(options)

def start_instances_command(options):
	from .instance import start_instances
	start_instances(options)

def stop_instances_command(options):
	from .instance import stop_instances
	stop_instances(options)

def reboot_instances_command(options):
	from .instance import reboot_instances
	reboot_instances(options)

def create_instance_image_command(options):
	from .instance import create_instance_image
	create_instance_image(options)

def info_instances_command(options):
	from .instance import get_instance_info
	get_instance_info(options)


## Commands that interact with instances directly
def ssh_instance_command(options):
	from .instance import ssh_to_instance
	ssh_to_instance(options)

def rsync_instance_command(options):
	from .instance import rsync_instance
	rsync_instance(options)

def scp_instance_command(options):
	from .instance import scp_instance
	scp_instance(options)

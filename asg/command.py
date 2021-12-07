NAME = 'autoscaling manager'
HELP = None

def add_arguments(parser):
	subparsers = parser.add_subparsers(metavar='command')
	parser.add_argument('--region', '-r', type=str, default='us-west-2')

	from manec2.asg.command import list_command
	list_groups_parser = subparsers.add_parser('list', help=None)
	list_groups_parser.set_defaults(command=list_command)

	from manec2.asg.command import group_info_command
	info_parser = subparsers.add_parser('info', help=None)
	info_parser.set_defaults(command=group_info_command)
	info_parser.add_argument('auto_scaling_group_names', type=str, nargs='+')

	from manec2.asg.command import ssh_instance_command
	ssh_instance_parser = subparsers.add_parser('ssh', help=None)
	ssh_instance_parser.set_defaults(command=ssh_instance_command)
	ssh_instance_parser.add_argument('auto_scaling_group_name', type=str)
	ssh_instance_parser.add_argument('--indices', '-ids', type=int, nargs='+',
									 default=[0])
	ssh_instance_parser.add_argument('--all', action='store_true')
	ssh_instance_parser.add_argument('--user', '-u', type=str, default='')
	ssh_instance_parser.add_argument('--key', '-i', type=str, default='')
	ssh_instance_parser.add_argument('--comm', '-c', type=str, default='')
	ssh_instance_parser.add_argument('--parallel', '-p', action='store_true')

	from manec2.asg.command import scale_group_command
	scale_group_parser = subparsers.add_parser('scale', help=None)
	scale_group_parser.set_defaults(command=scale_group_command)
	scale_group_parser.add_argument('auto_scaling_group_name', type=str)
	scale_group_parser.add_argument('--size', '-s', type=int, default=None)

## Commands that interact with AWS infrastructure
def list_command(options):
	from .asg import list_groups
	list_groups(options)

def ssh_instance_command(options):
	from .asg import ssh_command
	ssh_command(options)

def scale_group_command(options):
	from .asg import scale_group
	scale_group(options)

def group_info_command(options):
	from .asg import group_info
	group_info(options)
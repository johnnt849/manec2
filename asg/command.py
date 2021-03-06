NAME = 'autoscaling manager'
HELP = None

def add_arguments(parser):
	subparsers = parser.add_subparsers(metavar='command')

	from manec2.asg.command import list_command
	list_groups_parser = subparsers.add_parser('list', help=None)
	list_groups_parser.set_defaults(command=list_command)
	list_groups_parser.add_argument('--region', '-r', type=str, default=None)

	from manec2.asg.command import group_info_command
	info_parser = subparsers.add_parser('info', help=None)
	info_parser.set_defaults(command=group_info_command)
	info_parser.add_argument('auto_scaling_group_names', type=str, nargs='+')
	info_parser.add_argument('--region', '-r', type=str, default=None)

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
	ssh_instance_parser.add_argument('--region', '-r', type=str, default=None)

	from manec2.asg.command import scp_instance_command
	scp_instance_parser = subparsers.add_parser('scp', help=None)
	scp_instance_parser.set_defaults(command=scp_instance_command)
	scp_instance_parser.add_argument('auto_scaling_group_name', type=str)
	scp_instance_parser.add_argument('file', type=str, default=None)
	scp_instance_parser.add_argument('--indices', '-ids', type=int, nargs='+',
									 default=[0])
	scp_instance_parser.add_argument('--all', action='store_true')
	scp_instance_parser.add_argument('--user', '-u', type=str, default='')
	scp_instance_parser.add_argument('--key', '-i', type=str, default='')
	scp_instance_parser.add_argument('--get', action='store_true', default=False)
	scp_instance_parser.add_argument('--put', action='store_true', default=False)
	scp_instance_parser.add_argument('--location', '-l', type=str, default='.')

	scp_instance_parser.add_argument('--parallel', '-p', action='store_true')
	scp_instance_parser.add_argument('--region', '-r', type=str, default=None)

	from manec2.asg.command import scale_group_command
	scale_group_parser = subparsers.add_parser('scale', help=None)
	scale_group_parser.set_defaults(command=scale_group_command)
	scale_group_parser.add_argument('auto_scaling_group_name', type=str)
	scale_group_parser.add_argument('--size', '-s', type=int, default=None)
	scale_group_parser.add_argument('--region', '-r', type=str, default=None)

	from manec2.asg.command import rsync_command
	rsync_parser = subparsers.add_parser('rsync', help=None)
	rsync_parser.set_defaults(command=rsync_command)
	rsync_parser.add_argument('auto_scaling_group_name', type=str)
	rsync_parser.add_argument('--user', '-u', type=str, default='')
	rsync_parser.add_argument('--key', '-i', type=str, default='')
	rsync_parser.add_argument('--exclude', '-e', nargs='+', type=str,
								default='')
	rsync_parser.add_argument('--file', '-f', type=str, default=None)
	rsync_parser.add_argument('--location', '-l', type=str, default=None)
	rsync_parser.add_argument('--indices', '-ids', nargs='+', type=int,
								default=-1)
	rsync_parser.add_argument('--parallel', '-p', action='store_true')
	rsync_parser.add_argument('--force', action='store_true')
	rsync_parser.add_argument('--region', '-r', type=str, default=None)

## Commands that interact with AWS infrastructure
def list_command(options):
	from .asg import list_groups
	list_groups(options)

def ssh_instance_command(options):
	from .asg import ssh_command
	ssh_command(options)

def scp_instance_command(options):
	from .asg import scp_command
	scp_command(options)

def scale_group_command(options):
	from .asg import scale_group
	scale_group(options)

def group_info_command(options):
	from .asg import group_info
	group_info(options)

def rsync_command(options):
	from .asg import rsync_group_command
	rsync_group_command(options)

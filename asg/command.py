NAME = 'autoscaling manager'
HELP = None

def add_arguments(parser):
	subparsers = parser.add_subparsers(metavar='command')
	parser.add_argument('--region', '-r', type=str, default='us-east-1')

	from manec2.asg.command import list_command
	get_contexts_parser = subparsers.add_parser('list', help=None)
	get_contexts_parser.set_defaults(command=list_command)


## Commands that interact with AWS infrastructure
def list_command(options):
	from .asg import list_groups
	list_groups(options)
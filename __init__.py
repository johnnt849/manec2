import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

region_aliases = {
	'us-west-2': 'us-west-2',
	'uw2': 'us-west-2',
	'us-east-1': 'us-east-1',
	'ue1': 'us-east-1',
	'us-east-2': 'us-east-2',
	'ue2': 'us-east-2'
}

def main(args):
	from manec2.core.base import parse
	options = parse(args)

	try:
		options.region = region_aliases[options.region]
	except KeyError as e:
		print(f'Specified region not found, check the region name or abbreviation')
		sys.exit(33)

	if 'command' in options:
		options.command(options)

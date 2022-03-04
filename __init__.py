import os
from pathlib import Path
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

def get_default_region():
	with open(Path.home() / '.aws/config', 'r') as config_file:
		for line in config_file:
			if 'region' in line:
				region = line.split('=')[1].strip()
				return region

def main(args):
	from manec2.core.base import parse
	options = parse(args)

	if options.region is None:
		options.region = get_default_region()

	try:
		options.region = region_aliases[options.region]
	except KeyError as e:
		print(f'Specified region not found, check the region name or abbreviation')
		sys.exit(33)

	if 'command' in options:
		options.command(options)

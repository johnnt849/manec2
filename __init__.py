import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main(args):
	from manec2.core.base import parse
	options = parse(args)

	if 'command' in options:
		options.command(options)

import argparse
import functools
import importlib
import logging
import pkgutil
import subprocess

import manec2

def parse(args):
	parser = argparse.ArgumentParser(prog='manec2',
					description='EC2 Instance Manager')

	# Only one module but extensible in the future
	for module_info in pkgutil.iter_modules(manec2.__path__):
		if not module_info.ispkg:
			continue
		full_module_name = 'manec2.{}.command'.format(module_info.name)
		try:
			module = importlib.import_module(full_module_name)
		except ModuleNotFoundError as e:
			continue

	module.add_arguments(parser)

	return parser.parse_args(args)

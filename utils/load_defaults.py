import os
import yaml

from pathlib import Path

config_file_path = Path.home() / '.manec2_config.yaml'
default_config = {}
if os.path.exists(config_file_path):
    default_config = yaml.safe_load(open(config_file_path, 'r'))

def get_default_config(options):
    if not default_config:
        return {}

    profile = options.profile if options.profile is not None else 'default'
    return default_config[profile]
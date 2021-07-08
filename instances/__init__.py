import manec2
import os

MODULE_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTANCE_CACHE_DIR = MODULE_BASE_DIR + "/instances/resources/"
INSTANCE_CACHE_FILE = INSTANCE_CACHE_DIR + "instance_info.json"
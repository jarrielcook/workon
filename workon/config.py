import os
import json

CONFIG_FILE='.workon.cfg'

#
# Workon configuration
#
def default_config():
    default_context_path = os.path.join(os.environ['HOME'], '.context')
    config = {
        'context_dir': default_context_path,
    }
    return config

def read_config():
    config_file = os.path.join(os.environ['HOME'], CONFIG_FILE)
    config = {}

    try:
        with open(config_file) as fp:
            config = json.load(fp)
    except Exception as e:
        print(e)
        config = default_config()
        write_config(config)

    return config

def write_config(config):
    config_file = os.path.join(os.environ['HOME'], CONFIG_FILE)

    try:
        with open(config_file, 'w') as fp:
            json.dump(config, fp)
            print('Wrote configuration file: {}'.format(config_file))
    except Exception as e:
        print(e)



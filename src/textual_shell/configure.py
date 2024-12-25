import os
from typing import Annotated

import yaml

HOME_DIR = os.environ.get('HOME')
PATH = os.path.join(HOME_DIR, '.config.yaml')

def create_config(
    path: Annotated[str, 'The path to create the config file.']=PATH
) -> None:
    if not os.path.exists(path):
        with open(path, 'w') as config_file:
            yaml.dump({}, config_file)

def get_config(
    path: Annotated[str, 'The path to create the config file.']=PATH
) -> dict:
    if not os.path.exists(path):
        create_config(path)
        
    with open(path, 'r') as config_file:
        return yaml.safe_load(config_file) or {}    

def get_setting(
    section: Annotated[str, 'The section of the config.'],
    setting: Annotated[str, 'The setting to get.'],
    path: Annotated[str, 'The path to create the config file.']=PATH
) -> Annotated[str | None, 'The value if it exists else None.']:
    config = get_config(path)
    return config.get(section, {}).get(setting, None)

def add_section(
    section: Annotated[str, 'Section Name'],
    path: Annotated[str, 'The path to create the config file.']=PATH
):
    config = get_config(path)
    if section not in config:
        config[section] = {}
    
    with open(path, 'w') as config_file:
        yaml.dump(config, config_file)

def update_setting(
    section: Annotated[str, 'The section of the config.'],
    setting: Annotated[str, 'The setting to update.'],
    value: Annotated[str, 'The new value']=None,
    path: Annotated[str, 'The path to create the config file.']=PATH
) -> None:
    config = get_config(path)
    if section not in config:
        config[section] = {}
        
    config[section][setting]['value'] = value
    
    with open(path, 'w') as config_file:
        yaml.dump(config, config_file)

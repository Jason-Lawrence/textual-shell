import os
from typing import Annotated

import yaml


def create_config(
    path: Annotated[str, 'The path to create the config file.']
) -> None:
    if not os.path.exists(path):
        with open(path, 'w') as config_file:
            yaml.dump({}, config_file)

def get_config(
    path: Annotated[str, 'The path to create the config file.']
) -> dict:
    if not os.path.exists(path):
        create_config(path)
        
    with open(path, 'r') as config_file:
        return yaml.safe_load(config_file) or {}
    
def get_setting_value(
    section: Annotated[str, 'The section of the config.'],
    setting: Annotated[str, 'The setting to get.'],
    path: Annotated[str, 'The path to create the config file.']
) -> str:
    setting = get_setting(section, setting, path)
    return setting.get('value')

def get_setting_description(
    section: Annotated[str, 'The section of the config.'],
    setting: Annotated[str, 'The setting to get.'],
    path: Annotated[str, 'The path to create the config file.']
) -> str:
    setting = get_setting(section, setting, path)
    return setting.get('description')
      

def get_setting(
    section: Annotated[str, 'The section of the config.'],
    setting: Annotated[str, 'The setting to get.'],
    path: Annotated[str, 'The path to create the config file.']
) -> Annotated[str | None, 'The value if it exists else None.']:
    config = get_config(path)
    return config.get(section, {}).get(setting, None)

def add_section(
    section: Annotated[str, 'Section Name'],
    path: Annotated[str, 'The path to create the config file.']
):
    config = get_config(path)
    if section not in config:
        config[section] = {}
    
    with open(path, 'w') as config_file:
        yaml.dump(config, config_file)

def update_setting(
    section: Annotated[str, 'The section of the config.'],
    setting: Annotated[str, 'The setting to update.'],
    path: Annotated[str, 'The path to create the config file.'],
    value: Annotated[str, 'The new value']=None,
) -> None:
    config = get_config(path)
    if section not in config:
        config[section] = {}
        
    config[section][setting]['value'] = value
    
    with open(path, 'w') as config_file:
        yaml.dump(config, config_file)

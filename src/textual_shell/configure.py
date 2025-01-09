import os
from typing import Annotated

import yaml


def create_config(
    path: Annotated[str, 'The path to create the config file.'],
    config: Annotated[dict[str, str], 'Settings']={}
) -> None:
    """
    Create a default config for the application.
    
    Args:
        path (str): The path to create the config file.
    """
    if not os.path.exists(path):
        with open(path, 'w') as config_file:
            yaml.dump(config, config_file)

def get_config(
    path: Annotated[str, 'The path to the config file.']
) -> Annotated[dict, 'The config loaded into a dictionary.']:
    """
    Load the config into a dictionary.
    
    Args:
        path (str): The path to the config.
    """
    if not os.path.exists(path):
        create_config(path)
        
    with open(path, 'r') as config_file:
        return yaml.safe_load(config_file) or {}
    
def get_setting_value(
    section: Annotated[str, 'The section of the config.'],
    setting: Annotated[str, 'The setting to get.'],
    path: Annotated[str, 'The path to the config file.']
) -> Annotated[str, 'The value of the setting.']:
    """
    Get the value of the setting.
    
    Args:
        section (str): The section of the config.
        setting (str): The setting to retrieve the value for.
        path (str): The path to the config.
    
    Returns:
        value (str): The value of the setting.
    """
    setting = get_setting(section, setting, path)
    return setting.get('value')

def get_setting_description(
    section: Annotated[str, 'The section of the config.'],
    setting: Annotated[str, 'The setting to get.'],
    path: Annotated[str, 'The path to the config file.']
) -> Annotated[str, 'The description of the setting.']:
    """
    Retrieve the description of a setting.
    
    Args:
        section (str): The section of the config.
        setting (str): The setting to retrieve the value for.
        path (str): The path to the config.

    Returns: 
        description (str): The description of the setting.
    """
    setting = get_setting(section, setting, path)
    return setting.get('description')

def get_setting_options(
    section: Annotated[str, 'The section of the config.'],
    setting: Annotated[str, 'The setting to get.'],
    path: Annotated[str, 'The path to the config file.']
) -> (list[str] | dict[str, str]):
    """
    Get the options for a specific setting if they exist.
    
    Args:
        section (str): The section of the config.
        setting (str): The setting to retrieve the value for.
        path (str): The path to the config.
    
    Returns:
        options (list[str] | dict[str, str]):
            The options can either be a list of possible values, 
            or a dictionary where the keys are the values that will
            be displayed and the value will be the actual value.
    """
    setting = get_setting(section, setting, path)
    return setting.get('options', None)

def get_setting(
    section: Annotated[str, 'The section of the config.'],
    setting: Annotated[str, 'The setting to get.'],
    path: Annotated[str, 'The path to create the config file.']
) -> Annotated[str | None, 'The setting sub dictionary.']:
    """
    Get the setting sub dictionary.
    
    Args:
        section (str): The section of the config.
        setting (str): The setting to retrieve the value for.
        path (str): The path to the config.
        
    Returns:
        setting (dict): The description and value of a setting.
    """
    config = get_config(path)
    return config.get(section, {}).get(setting, None)

def check_section(
    section: Annotated[str, 'The name of the section.'],
    path: Annotated[str, 'The path to create the config file.'],
) -> bool:
    """
    Check if a section exists in the config.
    
    Args:
        section (str): The section of the config.
        path (str): The path to the config.
        
    Returns:
        exists (bool): True if it exists else False.
    """
    config = get_config(path)
    return section in config

def add_section(
    section_name: Annotated[str, 'The section key'],
    section: Annotated[dict[str, str], 'Section config'],
    path: Annotated[str, 'The path to the config file.']
) -> None:
    """
    Add a section to the config.
    
    Args:
        section (dict[str, str]): The section name.
        path (str): The path to the config
    """
    config = get_config(path)
    if section_name not in config:
        config.update(section)
    
    with open(path, 'w') as config_file:
        yaml.dump(config, config_file)

def update_setting(
    section: Annotated[str, 'The section of the config.'],
    setting: Annotated[str, 'The setting to update.'],
    path: Annotated[str, 'The path to create the config file.'],
    value: Annotated[str, 'The new value']=None,
) -> None:
    """
    Update the value of a  setting.
    
    Args:
        section (str): The section of the config.
        setting (str): The setting to retrieve the value for.
        path (str): The path to the config.
        value (str): The new value.
    """
    config = get_config(path)
    if section not in config:
        config[section] = {}
        
    config[section][setting]['value'] = value
    
    with open(path, 'w') as config_file:
        yaml.dump(config, config_file)

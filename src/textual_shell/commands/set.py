import os
import logging
from typing import Annotated

from textual.message import Message


from .. import configure
from ..job import Job
from .command import Command, CommandArgument


class Set(Command):
    """
    Set Shell Variables and update config.ini via configparser.
    
    Args:
        config_path (str): The path to the config. Defaults to the user's 
            home directory or the current working directory.
    
    Examples:
        set <section> <setting> <value> # sets the variable in the section to the value.
    """
    
    def __init__(
        self,
        config_path: Annotated[str, "Path to the config. Defaults to user's home directory first else cwd"]=None
    ) -> None:
        super().__init__()
        if config_path:
            self.config_path = config_path
        
        else:
            config_dir = os.environ.get('HOME', os.getcwd())
            self.config_path = os.path.join(config_dir, '.config.yaml')
            
        self._load_sections_into_struct()
        
    def _load_sections_into_struct(self) -> None:
        """
        Load the settings from the config file into the command digraph.
        
        Args:
            root_index (int): The index of the root node.
        """
        arg = CommandArgument('set', 'Set new shell variables.')
        root_index = self.add_argument_to_cmd_struct(arg)
        
        data = configure.get_config(self.config_path)
        for section in data:
            parent = self._add_section_to_struct(section, data[section]['description'], parent=root_index)
            for setting in data[section]:
                if setting == 'description':
                    continue
                
                node = self._add_section_to_struct(
                    setting,
                    data[section][setting]['description'],
                    parent
                )
                
                self._add_options(node, section, setting)
    
    def _add_options(self, node, section, setting) -> None:
        """Add options for the setting node."""
        options = configure.get_setting_options(section, setting, self.config_path)
        
        if options is None:
            return
        
        elif isinstance(options, dict):
            options = list(options.keys())
            
        
        for option in options:
            self._add_section_to_struct(option, None, node)
            
    def _add_section_to_struct(
        self,
        section: Annotated[str, 'Section name'],
        description: Annotated[str, 'Description of the section']=None,
        parent: Annotated[int, 'Index of the parent']=0
    ) -> Annotated[int, 'The index of the added node.']:
        """
        Add a section or setting from the config to the command digraph.
        
        Args:
            section (str): Section name.
            description (str): Description of the setting or section.
            parent (int): The index of the parent node. 
            
        Returns:
            index (int): The index of the inserted node.
        """
        arg = CommandArgument(section, description)
        return self.add_argument_to_cmd_struct(arg, parent=parent)
        
    def create_job(self, *args) -> 'SetJob':
        """
        Create a job to handle the execution.
        
        Args:
            args (tuple[str]): Should contain the section, setting, and value.
            
        Returns:
            set_job (SetJob): The job to handle the execution.
        """
        return SetJob(
            *args,
            config=self.config_path,
            shell=self.widget,
            cmd=self.name
        )

        
class SetJob(Job):
    """
    Job for handling setting shell variables.
    
    Args:
        section_name (str): The name of the section.
        setting_name (str): The name of the setting.
        value (str): The value the setting was set to.
        config (str): The path to the config.
    """
    
    class SettingsChanged(Message):
        """
        Event for when a setting has been changed.
        
        Args:
            section_name (str): The name of the section.
            setting_name (str): The name of the setting.
            value (str): The value the setting was set to.
        """
        
        def __init__(
            self,
            section_name: Annotated[str, 'The name of the section.'],
            setting_name: Annotated[str, 'The name of the setting that was changed.'],
            value: Annotated[str, 'The value the setting was set to.']
        ) -> None:
            super().__init__()
            self.section_name = section_name
            self.setting_name = setting_name
            self.value = value
    
    
    def __init__(
        self,
        section: Annotated[str, 'Section name'],
        setting: Annotated[str, 'Setting name'],
        value: Annotated[str, 'value for the setting'],
        config: Annotated[str, 'Path to the config.'],
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.config = config
        self.section = section
        self.setting = setting
        self.value = value
    
    async def execute(self) -> None:
        """
        Update the setting in the config.
        """
        self.status = self.Status.RUNNING
        options = configure.get_setting_options(
            self.section, self.setting, self.config
        )
            
        if self.value is not None and self.value not in options:
            self.send_log(
                f'Invalid value: {self.value} for {self.section}.{self.setting}',
                logging.ERROR
            )
            return
        
        self.send_log(
            f'Updating setting: {self.section}.{self.setting}',
            logging.INFO
        )
        configure.update_setting(
            self.section,
            self.setting,
            self.config, 
            self.value
        )
        self.shell.post_message(
            self.SettingsChanged(
                self.section,
                self.setting,
                self.value
            )
        )

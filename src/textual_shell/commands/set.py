import logging
from typing import Annotated

from textual.message import Message

from .. import configure
from ..job import Job
from ..command import Command, CommandNode


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
        self.running()
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
        self.completed()


class Set(Command):
    """
    Set Shell Variables and update config.ini via configparser.
    
    Args:
        config_path (str): The path to the config. Defaults to the user's 
            home directory or the current working directory.
    
    Examples:
        set <section> <setting> <value> # sets the variable in the section to the value.
    """
    
    DEFINITION = {
        'set': CommandNode(
            name='set',
            description='Set shell variables and update the config file.'
        ) 
    }
    
    def __init__(
        self,
        config_path: Annotated[str, "Path to the config"]
    ) -> None:
        super().__init__()
        self.config_path = config_path
        self.load_sections()
        
    def load_sections(self) -> None:
        """Load the settings from the config file 
        into the command definition."""
        root = self.get_root()
        data = configure.get_config(self.config_path)
        
        for key in data:
            node = CommandNode(
                name=key,
                description=data[key]['description']
            )
            root.children[key] = node
            
            for setting in data[key]:
                if setting == 'description':
                    continue
                
                node.children[setting] = CommandNode(
                    name=setting,
                    description=data[key][setting]['description'],
                    value=data[key][setting]['value'],
                    options=data[key][setting].get('options', None)
                )
    
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
            shell=self.shell,
            cmd=self.name
        )

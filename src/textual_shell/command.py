from typing import Annotated
from abc import ABC, abstractmethod

from textual import log
from textual.message import Message

from .job import Job
from . import configure


class Command(ABC):
    """Base class for the Commands for the shell widget."""
    
    class Log(Message):
        """
        Default Logging event for commands.
        
        Args:
            sender (str): The name of the command sending the log.
            msg (str): The log message.
            severity (int): The level of the severity.
            
        """
        def __init__(
            self,
            sender: Annotated[str, 'The name of the command sending the log.'],
            msg: Annotated[str, 'The log message.'],
            severity: Annotated[int, 'The level of the severity']
        ) -> None:
            super().__init__()
            self.sender = sender
            self.msg = msg
            self.severity = severity
    

    @property
    @abstractmethod
    def DEFINITION(self):
        pass
            
    def __init__(self) -> None:
        self.name = self.__class__.__name__.lower()
        
    def get_suggestions(
        self,
        cmdline: Annotated[list[str], 'The current value of the command line.']
    ) -> Annotated[list[str], 'A list of possible next values.']:
        """
        Get a list of suggestions for autocomplete via the current args neighbors.
        
        Args:
            cmdline (list[str]): The current value of the command line.
            
        Returns:
            suggestions (list[str]): List of possible next values.
        """
        sub = self.DEFINITION
        for key in cmdline:
            if new_sub := sub.get(key, None):
                sub = new_sub
        
        if options := sub.get('options', None):
            if isinstance(options, list):
                return options
            
            elif isinstance(options, dict):
                return list(options.keys())
        
        else:
            return [key for key in sub.keys() if key != 'description']

    def recurse_definition(
        self,
        arg: Annotated[str, 'The level of the substructure'],
        sub: Annotated[dict[str, dict | list | str], 'A sub dict in the definition.']
    )-> Annotated[str, 'The help text for all of the sub structures.']:
        """
        Recurse through the command definition and generate the help text.
        
        Args:
            key (str): The key in the definition.
            sub (dict[str, dict | list | str] | Any): A sub structure in 
                the definition.
                
        Returns:
            help_text (str): The help text for all of the sub structures
                in the definition.
        """
        help_text = f'**{arg}:**  \n'
        for key, val in sub.items():
            if key == 'description':
                help_text += f'&nbsp;&nbsp;&nbsp;&nbsp;**description:** {val}  \n'
            
            elif key == 'options':
                help_text += '&nbsp;&nbsp;&nbsp;&nbsp;**options:**  \n'
                if isinstance(val, list):
                    options = [f'&nbsp;&nbsp;&nbsp;&nbsp;- {v}  \n' for v in val]
                    help_text += ''.join(options)
                
                elif isinstance(val, dict):
                    options = [f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**{k}:** {v}  \n' for k, v in val.items()]
                    help_text += ''.join(options)
                    
            elif key == 'value':
                continue
                
            else:
                help_text += '&nbsp;&nbsp; '+ self.recurse_definition(key, val)
        
        return help_text
        
        
    
    def help(self) -> Annotated[str, 'The help text for the command.']:
        """
        Generates the Help text for the command.
        
        Returns:
            help_text (str): The help text for the command with markdown syntax.
        """
        log(self.DEFINITION)
        description = self.DEFINITION[self.name]['description']
        
        help_text = f'### Command: {self.name}\n'
        help_text += f'**Description:** {description}\n'
        help_text += '---\n'
        
        sub = self.DEFINITION.get(self.name)
        for key, val in sub.items():
            if key == 'description':
                continue

            else:
                help_text += self.recurse_definition(key, val)
        
        return help_text
        
    @abstractmethod
    def create_job(self, *args) -> Job:
        """
        Create a job to execute the command.
        Subclasses must implement it.
        
        Returns:
            job (Job): The created job ready for execution.
        """
        pass

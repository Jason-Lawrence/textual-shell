from abc import ABC, abstractmethod
from typing import Annotated, List

import treelib
import treelib.exceptions

from . import configure
from .screen import HelpScreen


class CommandArgument:
    
    def __init__(
        self,
        name: Annotated[str, 'The name of the argument or sub-command'],
        description: Annotated[str, 'The description of the argument or sub-command']
    ) -> None:
        self.name = name
        self.description = description
        
    def __repr__(self) -> str:
        return f'Argument(name={self.name}, description={self.description})'
    
    def __str__(self) -> str:
        return f'{self.name}: {self.description}' 


class Command(ABC):
            
    def __init__(
        self,
        cmd_tree: Annotated[treelib.Tree, 'The command line structure']=None,
    ) -> None:
        self.name = self.__class__.__name__.lower()
        if cmd_tree and not isinstance(cmd_tree, treelib.Tree):
            raise ValueError('cmd_tree is not a Tree from treelib.')
        
        elif not cmd_tree:
            self.cmd_tree = treelib.Tree()
        
        else:
            self.cmd_tree = cmd_tree
            
    def add_argument_to_cmd_tree(
        self, 
        arg: CommandArgument,
        parent: str=None
    ) -> None:
        self.cmd_tree.create_node(
            tag=arg.name.capitalize(),
            identifier=arg.name,
            parent=parent,
            data=arg
        )
        
    def get_suggestions(
        self,
        current_arg: str
    ) -> Annotated[List[str], 'A list of possible next values']:
        try:
            children_nodes = self.cmd_tree.children(current_arg)
        
        except treelib.exceptions.NodeIDAbsentError as error:
            children_nodes = []
        
        return [child.data.name for child in children_nodes]
            
    def help(self):
        """This will generate help text in a pop up in the textual app."""
        help_text = '\n'.join([node.data for node in self.cmd_tree.all_nodes()])
        return help_text     
    
    @abstractmethod
    def execute(self):
        pass
    
    
class Help(Command):
    """
    Display the help for a given command
    
    Examples:
        help <command>
    """
    def __init__(self) -> None:
        super().__init__()
        arg = CommandArgument('help', 'Show help for commands')
        self.add_argument_to_cmd_tree(arg)
        
    def help(self):
        """"""
        root = self.cmd_tree.get_node(self.name)
        help_text = f"""
            ### Command: {self.name}
            **Description:** {root.data.description}
        """
        return help_text
    
    def execute(self, cmd: Command):
        help_text = cmd.help()
        return HelpScreen(help_text)
    

class Set(Command):
    """
    Set Shell Variables and update config.ini via configparser.
    
    Examples:
        set <section> <setting> <value> # sets the variable in the section to the value.
    """
    def __init__(self) -> None:
        super().__init__()
        arg = CommandArgument('set', 'Set new shell variables.')
        self.add_argument_to_cmd_tree(arg)
        self._load_sections_into_tree()
        
    def _load_sections_into_tree(self) -> None:
        data = configure.get_config()
        for section in data:
            self._add_section_to_tree(section, data[section]['description'])
            for setting in data[section]:
                if setting == 'description':
                    continue
                
                self._add_setting_to_tree(
                    section,
                    setting,
                    data[section][setting]['description']
                )
            
    def _add_setting_to_tree(
        self,
        section: Annotated[str, 'Section name'],
        setting: Annotated[str, 'Setting name'],
        description: Annotated[str, 'Description of the section']=None
    ) -> None:
        arg = CommandArgument(setting, description)
        self.add_argument_to_cmd_tree(arg, parent=section)
            
    def _add_section_to_tree(
        self,
        section: Annotated[str, 'Section name'],
        description: Annotated[str, 'Description of the section']=None
    ) -> None:
        arg = CommandArgument(section, description)
        self.add_argument_to_cmd_tree(arg, parent='set')
    
    def update_settings(
        self, 
        section: Annotated[str, 'Section name'],
        setting: Annotated[str, 'Setting name'],
        value: Annotated[str, 'Default value']=None
    ) -> int:
        configure.update_setting(section, setting, value)
        return 0
        
    def execute(self, *args) -> int:
        return self.update_settings(*args)


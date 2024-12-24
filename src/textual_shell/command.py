from abc import ABC, abstractmethod
from typing import Annotated, List

import treelib
import treelib.exceptions

from . import configure


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
            
    @abstractmethod
    def execute(self):
        pass
    
    def help(self):
        """This will show self.HelpMessage in a pop up in the textual app."""
        return self.help_info
    
    
class Help(Command):
    """
    Display the help for a given command
    
    Examples:
        help <command>
    """
    def execute(self, cmd: Command):
        cmd.help()
        
    def help(self):
        pass
    

class Set(Command):
    """
    Set Shell Variables and update config.ini via configparser.
    
    Examples:
        set new section <section> # creates new section in config.ini
        set new section <section> <setting>  Optional[str, 'value']# creates a new setting in the section
        set <section> <setting> <value> # sets the variable in the section to the value.
    """
    def __init__(self) -> None:
        super().__init__()
        arg = CommandArgument('set', 'Set new shell variables.')
        self.add_argument_to_cmd_tree(arg)
        
        new = CommandArgument('new', 'Add a new section or setting.')
        self.add_argument_to_cmd_tree(new, parent=arg.name)
        
    def get_suggestions(
        self,
        current_arg: str
    ) -> Annotated[List[str], 'A list of possible next values']:
        try:
            children_nodes = self.cmd_tree.children(current_arg)
        
        except treelib.exceptions.NodeIDAbsentError as error:
            children_nodes = None
        
        return [child.data.name for child in children_nodes]
    
    def update_settings(
        self, 
        section: Annotated[str, 'Section name'],
        setting: Annotated[str, 'Setting name'],
        default: Annotated[str, 'Default value']=None
    ) -> None:
        configure.update_setting(section, setting, default)
        
    def add_new_section(
        self,
        section: Annotated[str, 'Section name'],
        description: Annotated[str, 'Description of the section']=None
    ) -> None:
        configure.add_section(section)
        configure.update_setting(section, 'description', description)
        arg = CommandArgument(section, description)
        self.add_argument_to_cmd_tree(arg, parent='set')
        
    def execute(self):
        pass
    
    def help(self):
        pass

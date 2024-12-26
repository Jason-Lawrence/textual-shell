from abc import ABC, abstractmethod
from typing import Annotated, List

import rustworkx as rx

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
        cmd_struct: Annotated[rx.PyDiGraph, 'The command line structure']=None,
    ) -> None:
        self.name = self.__class__.__name__.lower()
        if cmd_struct and not isinstance(cmd_struct, rx.PyDiGraph):
            raise ValueError('cmd_struct is not a PyDiGraph from rustworkx.')
        
        elif not cmd_struct:
            self.cmd_struct = rx.PyDiGraph()
        
        else:
            self.cmd_struct = cmd_struct
            
    def add_argument_to_cmd_struct(
        self, 
        arg: CommandArgument,
        parent: int=None
    ) -> int:
        if parent is None:
            return self.cmd_struct.add_node(arg)
            
        else:
            return self.cmd_struct.add_child(parent, arg, None)
        
    def match_arg_name(
        self,
        node: CommandArgument
    ) -> Annotated[bool, "True if the node's name matches the current arg else False"]:
        return self.current_arg_name == node.name
        
    def get_suggestions(
        self,
        current_arg: str
    ) -> Annotated[List[str], 'A list of possible next values']:
        self.current_arg_name = current_arg
        indices = self.cmd_struct.filter_nodes(self.match_arg_name)
        if len(indices) == 0:
            return []
        
        children = self.cmd_struct.neighbors(indices[0])
        return [self.cmd_struct.get_node_data(child).name for child in children]
            
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
        self.add_argument_to_cmd_struct(arg)
        
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
        root_index = self.add_argument_to_cmd_struct(arg)
        self._load_sections_into_struct(root_index)
        
    def _load_sections_into_struct(self, root_index) -> None:
        data = configure.get_config()
        for section in data:
            parent = self._add_section_to_struct(section, data[section]['description'], parent=root_index)
            for setting in data[section]:
                if setting == 'description':
                    continue
                
                self._add_section_to_struct(
                    setting,
                    data[section][setting]['description'],
                    parent
                )
            
    def _add_section_to_struct(
        self,
        section: Annotated[str, 'Section name'],
        description: Annotated[str, 'Description of the section']=None,
        parent: Annotated[int, 'Index of the parent']=0
    ) -> None:
        arg = CommandArgument(section, description)
        return self.add_argument_to_cmd_struct(arg, parent=parent)
    
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


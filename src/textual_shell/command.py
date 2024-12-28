import os
from abc import ABC, abstractmethod
from typing import Annotated, List

import rustworkx as rx

from textual.screen import ModalScreen
from textual.message import Message
from textual.widget import Widget

from . import configure
from .screen import HelpScreen


class CommandArgument:
    """Used as nodes for the rustworkx.PyDiGraph"""
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
    """Base class for the Commands for the shell widget."""
    def __init__(
        self,
        cmd_struct: Annotated[rx.PyDiGraph, 'The command line structure']=None,
        widget: Widget=None
    ) -> None:
        self.name = self.__class__.__name__.lower()
        self.widget = widget
        
        if cmd_struct and not isinstance(cmd_struct, rx.PyDiGraph):
            raise ValueError('cmd_struct is not a PyDiGraph from rustworkx.')
        
        elif not cmd_struct:
            self.cmd_struct = rx.PyDiGraph(check_cycle=True)
        
        else:
            self.cmd_struct = cmd_struct
            
    def add_argument_to_cmd_struct(
        self, 
        arg: CommandArgument,
        parent: int=None
    ) -> int:
        """
        Add an argument node to the command digraph.
        
        Args:
            arg (CommandArgument): The argument to add.
            parent (int): The index of the parent in the digraph.
            
        Returns:
            new_index (int): The index of the inserted node.
        """
        if parent is None:
            return self.cmd_struct.add_node(arg)
            
        else:
            return self.cmd_struct.add_child(parent, arg, None)
        
    def match_arg_name(
        self,
        node: CommandArgument
    ) -> Annotated[bool, "True if the node's name matches the current arg else False"]:
        """
        Find the node in the command digraph.
        
        Args: 
            node (CommandArgument): The node's data
            
        Returns:
            result (bool): True If the nodes arg.name is equal
                to the current arg in the command line else False.
        """
        return self.current_arg_name == node.name
    
    def get_suggestions(
        self,
        current_arg: str
    ) -> Annotated[List[str], 'A list of possible next values']:
        """
        Get a list of suggestions for autocomplete via the current args neighbors.
        
        Args:
            current_arg (str): The current arg in the command line.
            
        Returns:
            suggestions (List[str]): List of current node's neighbors names.
        """
        self.current_arg_name = current_arg
        indices = self.cmd_struct.filter_nodes(self.match_arg_name)
        if len(indices) == 0:
            return []
        
        children = self.cmd_struct.neighbors(indices[0])
        return [self.cmd_struct.get_node_data(child).name for child in children]
    
    def gen_help_text(
        self,
        node: CommandArgument
    ) -> Annotated[str, 'A Markdown string renderable in a Markdown widget.']:
        """
        Generate help text for the specific node in the graph.
        
        Args:
            node (CommandArgument): The node in the digraph.
            
        Returns:
            help_text (str): A Markdown string for the commands help.
        """
        return f'**{node.name}:**\t\t {node.description}  \n'
    
    def recurse_graph(
        self,
        node: Annotated[int, 'The index of the node.']
    ) -> Annotated[str, 'The help text for all nodes in the digraph.']:
        """
        Traverse the graph and generate the help text for each node.
        
        Args:
            node (int): The index of the node in the digraph.
            
        Returns:
            help_text (str): The help text for the command.
        """
        neighbors = self.cmd_struct.neighbors(node)
        
        if len(neighbors) == 0:
            return '&nbsp;&nbsp;&nbsp;&nbsp;' + self.gen_help_text(
                self.cmd_struct.get_node_data(node)
            ) 
            
        else:
            help_text =  self.gen_help_text(
                self.cmd_struct.get_node_data(node)
            )
            for neighbor in neighbors:
                help_text += self.recurse_graph(neighbor)
                
            return help_text
            
    def help(self):
        """
        Generates the Help text for the command.
        
        Returns:
            help_text (str): The help text for the command with markdown syntax.
        """
        root = self.cmd_struct.get_node_data(0)
        
        help_text = f'### Command: {root.name}\n'
        help_text += f'**Description:** {root.description}\n'
        help_text += '---\n'
        
        for neighbor in self.cmd_struct.neighbors(0):
            help_text += self.recurse_graph(neighbor)
        
        return help_text
    
    def validate_cmd_line(self, *args):
        current_index = 0
        for arg in args:
            print(current_index)
            neighbors = self.cmd_struct.neighbors(current_index)
            
            next_index = next(
                (index for index in neighbors if self.cmd_struct[index].name == arg), None
            )
            print(f'Arg: {arg} at index: {args.index(arg)} length: {len(args)} Next: {next_index}')
            if next_index is None and args.index(arg) == (len(args) - 1):
                return True

            elif next_index is None and args.index(arg) == (len(args) - 2):
                return not self.cmd_struct.neighbors(current_index)
            
            else:  
                current_index = next_index
        
        return False
                
        
    @abstractmethod
    def execute(self):
        """
        Child classes must implement this function. 
        This is what the shell will call to start the command.
        """
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
        """Generate the help text for the help command."""
        root = self.cmd_struct.get_node_data(0)
        help_text = f'### Command: {root.name}\n'
        help_text += f'**Description:** {root.description}'
        return help_text
    
    def execute(
        self,
        cmd: Command
    ) -> Annotated[ModalScreen, 'A help screen to show as a modal.']:
        """
        execute the help for whatever command was requested.
        
        Args:
            cmd (Command): The requested command.
            
        Returns:
            help_screen (HelpScreen): A modal for the app to render.
        """
        help_text = cmd.help()
        return HelpScreen(help_text)
    

class Set(Command):
    """
    Set Shell Variables and update config.ini via configparser.
    
    Args:
        config_path (str): The path to the config. Defaults to the user's 
            home directory or the current working directory.
    
    Examples:
        set <section> <setting> <value> # sets the variable in the section to the value.
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
        config_path: Annotated[str, "Path to the config. Defaults to user's home directory first else cwd"]=None
    ) -> None:
        super().__init__()
        if config_path:
            self.config_path = config_path
        
        else:
            config_dir = os.environ.get('HOME', os.getcwd())
            self.config_path = os.path.join(config_dir, '.config.yaml')
            
        arg = CommandArgument('set', 'Set new shell variables.')
        root_index = self.add_argument_to_cmd_struct(arg)
        self._load_sections_into_struct(root_index)
        
    def _load_sections_into_struct(
        self,
        root_index: Annotated[int, 'The index of the root node.']
    ) -> None:
        """
        Load the settings from the config file into the command digraph.
        
        Args:
            root_index (int): The index of the root node.
        """
        data = configure.get_config(self.config_path)
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
    
    def update_settings(
        self, 
        section: Annotated[str, 'Section name'],
        setting: Annotated[str, 'Setting name'],
        value: Annotated[str, 'Default value']=None
    ) -> None:
        """
        Update the setting in the config.
        
        Args:
            section (str): The name of the section.
            setting (str): The name of the setting.
            value (str): The value the setting was set to.
        """
        configure.update_setting(section, setting, self.config_path, value)
    
    def settings_changed(
        self,
        section_name: Annotated[str, 'The name of the section.'],
        setting_name: Annotated[str, 'The name of the setting that was changed.'],
        value: Annotated[str, 'The value the setting was set too.']
    ) -> None:
        """
        Event emitter for the settings being changed.
        
        Args:
            section_name (str): The name of the section.
            setting_name (str): The name of the setting.
            value (str): The value the setting was set to.
        """
        self.widget.post_message(
            self.SettingsChanged(
                section_name,
                setting_name,
                value
            )
        )
    
    def execute(self, *args) -> int:
        self.update_settings(*args)
        self.settings_changed(*args)
        

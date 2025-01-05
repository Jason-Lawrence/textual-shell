from typing import Annotated, List
from abc import ABC, abstractmethod

import rustworkx as rx

from textual.app import ComposeResult
from textual.containers import Center
from textual.message import Message
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Label,
    LoadingIndicator,
    Static
)


class CommandArgument:
    """
    Used as nodes for the rustworkx.PyDiGraph
    
    Args:
        name (str): The name of the command or sub-command.
        description (str): The description of the command or sub-command.
    """
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
    
    
class CommandScreen(Screen):
    """Base Screen for commands to output too."""
    
    def __init__(
        self, 
        cmd_name: Annotated[str, 'The name of the command'],
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.cmd_name = cmd_name
    
    def compose(self) -> ComposeResult:
        yield Center(Label(self.cmd_name.upper()))
        yield Center(LoadingIndicator())
        yield Center(Static(f'{self.cmd_name} is currently running.'))
        
    
class Command(ABC):
    """Base class for the Commands for the shell widget."""
    
    class Start(Message):
        """Default message to notify the app that a command has started."""
        pass
    
    class Finish(Message):
        """Default message to notify the app that the command has finished."""
        pass
    
    class PushScreen(Message):
        """
        Default Message for pushing a new screen onto the app.
        
        Args:
            screen (Screen): The output screen for the command.
        """
        def __init__(self, screen) -> None:
            super().__init__()
            self.screen = screen
            
    
    class Log(Message):
        """
        Default Logging event for commands.
        
        Args:
            command (str): The name of the command sending the log.
            msg (str): The log message.
            severity (int): The level of the severity.
            
        """
        def __init__(
            self,
            command: Annotated[str, 'The name of the command sending the log.'],
            msg: Annotated[str, 'The log message.'],
            severity: Annotated[int, 'The level of the severity']
        ) -> None:
            super().__init__()
            self.command = command
            self.msg = msg
            self.severity = severity
        
    
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
    
    def send_log(
        self,
        msg: Annotated[str, 'log message'],
        severity: Annotated[str, 'The level of severity']
    ) -> None:
        """
        Send logs to the app.
        
        Args:
            msg (str): The log message.
            severity (str): The severity level of the log.
        """
        self.widget.post_message(self.Log(self.name, msg, severity))
                
    def send_screen(
        self,
        screen: Annotated[Screen, 'The output screen'],
    ) -> None:
        """Send an output screen"""
        self.widget.post_message(self.PushScreen(screen))

    @abstractmethod
    def execute(self):
        """
        Child classes must implement this function. 
        This is what the shell will call to start the command.
        """
        pass

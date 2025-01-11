from typing import Annotated, Optional
from abc import ABC, abstractmethod

from rich.console import (
    Console,
    ConsoleOptions,
    group,
    RenderResult
)
from rich.panel import Panel
from rich.rule import Rule

from textual.message import Message

from .job import Job


class CommandNode:
    """
    Nodes for the command Definition.
    
    Args:
        name (str): The name for the node.
        description (str): The description for the node.
        value (Optional[str]): Optional value for the node
        options (Optional[list[str] | dict[str, str]]): 
            Optional values for the node.
            
    """
    
    def __init__(
        self,
        name: Annotated[str, 'The name for the node.'],
        description: Annotated[str, 'A description for the node.'],
        value: Annotated[Optional[str], 'Optional value for the node']=None,
        options: Annotated[Optional[list[str] | dict[str, str]], 'Optional list of values.']=None,
        children: Annotated[Optional[dict[str, 'CommandNode']], 'Optional dictionary of child nodes.']=None
    ) -> None:
        self.name = name
        self.description = description
        self.value = value
        self.options = options
        self.children = children or {}
        
    def get_options(self) -> list[str]:
        """
        Retrieve the nodes options for it value.
        If options is a dictionary then the keys are returned.
        
        Returns:
            options (list[str]): The options.
        
        """
        if isinstance(self.options, list):
            return self.options
        
        elif isinstance(self.options, dict):
            return list(self.options.keys())
        
        return []
        
    def __rich_console__(
        self,
        console: Console,
        opt: ConsoleOptions
    ) -> RenderResult:
        yield f'[bold]{self.name}\n'
        yield f'  [bold]Description:[/bold] {self.description}\n'
        
        if isinstance(self.options, list):
            options = '  [bold]options:[/bold]\n'
            options += ''.join([f'    [red]-[/red] {val}\n' for val in self.options])
            yield options
            
        elif isinstance(self.options, dict):
            options = '  [bold]options:[/bold]\n'
            options += ''.join([f'    [red]{key}:[/red] {val}\n' for key, val in self.options.items()])
            yield options
            
        if len(self.children) > 0:
            for child in self.children.values():
                yield child
                     
    
    def __str__(self) -> str:
        pass
    
    def __repr__(self) -> str:
        return f"""
            CommandNode(
                name={self.name},
                description={self.description},
                value={self.value},
                options={self.options},
                children={self.children}
            )
        """


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
    def DEFINITION(
        self
    ) -> Annotated[dict[str, CommandNode], 'The definition for the command.']:
        """
        Abstract property for representing the command definition.
        Subclasses must provide their own definitions as a dictionary 
        mapping node names to CommandNode instances.
        """
        pass
            
    def __init__(self) -> None:
        self.name = self.__class__.__name__.lower()
        
    def send_log(
        self,
        msg: Annotated[str, 'The message for the log.'],
        severity: Annotated[int, 'Same severity levels as the logging module.']
    ) -> None:
        """
        Send logs from the command to the console log.
        
        Args:
            msg (str): The message for the log.
            severity (int): The severity level for the log. 
                Uses the same levels as the logging module.
        """
        self.shell.post_message(
            self.Log(
                self.name,
                msg,
                severity
            )
        )
        
    def get_root(self) -> CommandNode:
        """
        Get the root of the Command Definition.
        
        Returns:
            root (CommandNode): The root of the Command.
        """
        return self.DEFINITION.get(self.name)
        
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
        cmd_def = self.DEFINITION
        for node_name in cmdline:
            node = cmd_def.get(node_name, None)
            if node is None:
                return []
        
            cmd_def = node.children    
        
        if len(node.children) == 0:
           return node.get_options()
            
        return list(node.children.keys())
    
    @group()
    def get_help_render(self, root: CommandNode):
        """
        Generate the rich markup for the help box.
        
        Args:
            root (CommandNode): The root of the commands definition.
            
        Yields:
            group (rich.console.Group): The rich renderable components for the command definition.
        """
        yield f'[bold]Command: [magenta1]{root.name}\n'
        yield f'[bold underline][plum2]Description:[/bold underline] {root.description}'
        
        if len(root.children.keys()) > 0:
            yield Rule('[bold]Arguments', style='white')
            for child in root.children.values():
                yield child
                
    def help(self) -> RenderResult:
        """
        Generate the rich.panel to display in the Help modals RichLog widget.
        
        Returns:
            panel (rich.panel.Panel): The panel with the help for the command.
        """
        root_node = self.get_root()
        panel_text = self.get_help_render(root_node)
        return Panel(panel_text, title='[cyan1]Help')
         
    @abstractmethod
    def create_job(self, *args) -> Job:
        """
        Create a job to execute the command.
        Subclasses must implement it.
        
        Returns:
            job (Job): The created job ready for execution.
        """
        pass

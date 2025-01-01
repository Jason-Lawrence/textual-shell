from typing import Annotated, List

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, TextArea


class CommandList(Widget):
    """
    Custom widget for listing commands for the shell.
    
    Args:
        command_list (List[str]): List of commands for the custom shell.
    """
    DEFAULT_CSS = """
        CommandList {
            background: transparent;
            border: round white;
            height: auto;
            width: 20;
            layout: vertical;
            
            Label {
                text-align: center;
            }
            
            TextArea {
                background: transparent;
                border: none;
                border-top: solid white;
                text-align: center;
            }
        }
    """
    
    def __init__(
        self, 
        command_list: Annotated[List[str], 'List of commands for the custom shell.'],
    ) -> None:
        self.commands = command_list
        super().__init__()
    
    def on_mount(self):
        ta = self.query_one(TextArea)
        ta.can_focus = False
    
    def compose(self) -> ComposeResult:
        yield Label('Commands')
        yield TextArea(
            '\n'.join(self.commands),
            read_only=True
        )

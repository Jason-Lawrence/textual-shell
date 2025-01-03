from typing import Annotated

from textual.app import ComposeResult
from textual.containers import Grid, Container
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Markdown

from .command import Command, CommandArgument


class HelpScreen(ModalScreen):
    """
    Default Help screen Modal. Displays the text generated 
    by the help function on Commands.
    
    Args:
        help_text (str): The help text to display.
    """
    
    DEFAULT_CSS = """
        HelpScreen {
            align: center middle;
            
        }

        #help-dialog {
            height: 60%;
            width: 50%;
            grid-size: 3;
            grid-rows: 3 1fr 1fr;
            grid-columns: 1fr 1fr 3;
            background: $surface;
            border: solid white;
            padding: 0;
        }
            
        #help-label {
            column-span: 2;
            row-span: 1;
            text-align: center;
            width: 100%;
            offset: 0 1;
            
        }

        #help-close {
            padding: 0;
            margin: 0;
        }

        #help-display {
            column-span: 3;
            row-span: 2;
            margin: 0;
            padding: 1;
            border-top: solid white;
        }
    """
    
    def __init__(
        self,
        help_text: Annotated[str, 'The help text to display in the modal']
    ) -> None:
        super().__init__()
        self.help_text = help_text
    
    def compose(self) -> ComposeResult:
        yield Grid(
            Label('Help', id='help-label'),
            Button('X', variant='error', id='close-button'),
            Markdown(self.help_text, id='help-display'),
            id='help-dialog'
        )
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Close help modal."""
        if event.button.id == 'close-button':
            self.app.pop_screen()


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
        self.send_screen(HelpScreen(help_text))

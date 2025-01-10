from typing import Annotated

from textual.app import ComposeResult
from textual.containers import Grid 
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Markdown

from ..command import Command
from ..job import Job


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
            self.dismiss(True)
            

class HelpJob(Job):
    
    def __init__(
        self,
        cmd_to_show: Annotated[Command, 'The command to generate the help screen for.'],
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.cmd_to_show = cmd_to_show
    
    async def execute(self):
        """Display the Help screen."""
        self.running()
        help_text = self.cmd_to_show.help()
        help_screen = HelpScreen(help_text)
        await self.shell.app.push_screen_wait(help_screen)
        self.completed()


class Help(Command):
    """
    Display the help for a given command
    
    Examples:
        help <command>
    """
    DEFINITION = {
        'help': {
            'description': 'Show help for the command'
        }
    }
        
    def create_job(self, *args) -> HelpJob:
        """Create the job to display the help text."""
        return HelpJob(
            args[0],
            shell=self.widget,
            cmd=self.name
        )

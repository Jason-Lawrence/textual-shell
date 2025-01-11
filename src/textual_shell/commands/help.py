from typing import Annotated

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import RichLog

from ..command import Command, CommandNode
from ..job import Job


class HelpScreen(ModalScreen):
    """
    Default Help screen Modal. Displays the text generated 
    by the help function on Commands.
    
    Args:
        help_text (str): The help text to display.
    """
    BINDINGS = [
        Binding('q', 'dismiss_screen', 'Close the help box.'),
        Binding('escape', 'dismiss_screen', 'Close the help box.', show=False),
    ]
    
    DEFAULT_CSS = """
        HelpScreen {
            align: center middle;
            
        }

        #help-dialog {
            height: auto;
            width: auto;
            background: $surface;
            padding: 0;
            max-height: 75%;
            max-width: 65%;
        }
    """
    
    def __init__(
        self,
        help_text: Annotated[str, 'The help text to display in the modal']
    ) -> None:
        super().__init__()
        self.help_text = help_text
    
    def compose(self) -> ComposeResult:
        yield RichLog(id='help-dialog', markup=True)
        
    def on_mount(self) -> None:
        """Write the help text when the DOM is ready."""
        rich_log = self.query_one(RichLog)
        rich_log.write(self.help_text)
        
    def action_dismiss_screen(self) -> None:
        """Close the help screen."""
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
        'help': CommandNode(
            name='set',
            description='Show the help dialog for the requested command.'
        )
    }
        
    def create_job(self, *args) -> HelpJob:
        """Create the job to display the help text."""
        return HelpJob(
            args[0],
            shell=self.shell,
            cmd=self.name
        )

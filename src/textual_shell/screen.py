from typing import Annotated

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Markdown


class HelpScreen(ModalScreen):
    """
    Default Help screen Modal. Displays the text generated 
    by the help function on Commands.
    
    Args:
        help_text (str): The help text to display.
        help_label_id (str): The CSS id for the Label. 
            Defaults to help-label.
        help_button_id (str): The CSS id for the Button. 
            Defaults to help-close.
        help_display_id (str): The CSS id for the Markdown. 
            Defaults to help-display.
        help_dialog_id (str): The CSS id for the Grid Container. 
            Defaults to help-dialog.
    """
    
    DEFAULT_CSS = """
        HelpScreen {
            align: center middle;
            height: 50;
        }
        
        HelpScreen Grid {
            grid-size: 3;
            grid-rows: 2 40;
            grid-columns: 1fr 1fr 4;
            width: 80;
            height: auto;
            background: $surface;
            border: solid white;
        }
        
        HelpScreen Grid Label {
            column-span: 2;
            content-align: center middle;
            width: 1fr;
            offset: 1 0;
        }
        
        HelpScreen Grid Button {
            column-span: 1;
            text-align: center;
            padding: 0;
            margin: 0;
        }
        
        HelpScreen Grid Markdown {
            column-span: 3;
            row-span: 2;
            content-align: center middle;
            border-top: solid white;
        }
        
    """
    
    def __init__(
        self,
        help_text: Annotated[str, 'The help text to display in the modal'],
        help_label_id: Annotated[str, 'CSS id for the Label']='help-label',
        help_button_id: Annotated[str, 'CSS id for the Button']='help-close',
        help_display_id: Annotated[str, 'CSS id for the Markdown']='help-display',
        help_dialog_id: Annotated[str, 'CSS id for the Grid Container']='help-dialog'
    ) -> None:
        super().__init__()
        self.help_text = help_text
        self.help_label_id = help_label_id
        self.help_button_id = help_button_id
        self.help_display_id = help_display_id
        self.help_dialog_id = help_dialog_id
    
    def compose(self) -> ComposeResult:
        yield Grid(
            Label('Help', id=self.help_label_id),
            Button('X', variant='error', id=self.help_button_id),
            Markdown(self.help_text, id=self.help_display_id),
            id=self.help_dialog_id
        )
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Close help modal."""
        if event.button.id == self.help_button_id:
            self.app.pop_screen()

from typing import Annotated

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Markdown


class HelpScreen(ModalScreen):
    
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
        if event.button.id == self.help_button_id:
            self.app.pop_screen()

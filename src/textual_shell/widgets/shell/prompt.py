from typing import Annotated

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label


class PromptInput(Input):
    """
    Custom Input widget for entering commands.
    Pressing ctrl+space will activate the Suggestions widget.
    Pressing tab will switch focus to the Suggestions widget.
    Pressing escape will hide the Suggestions widget.
    """
    
    class AutoComplete(Message):
        """Switch to the suggestions widget for auto-completions."""
        pass
    
    class Show(Message):
        """
        Activate the suggestions widget.
        
        Args:
            cursor (int): The x location of the cursor.
                Used to position the suggestions widget.
        """
        def __init__(self, cursor: int) -> None:
            super().__init__()
            self.cursor_position = cursor
    
    class Hide(Message):
        """Hide the suggestions widget."""
        pass

    class FocusChange(Message):
        """
        A message for when the prompt input 
        has either gained or lost focus.
        """
        def __init__(self, is_focused: bool):
            super().__init__()
            self.is_focused = is_focused
            
    
    BINDINGS = [
        Binding('tab', 'switch_autocomplete', 'Switch to auto-complete if active', show=True, priority=True),
        Binding('escape', 'hide', 'Hide auto-complete', show=True),
        Binding('ctrl+@', 'activate_autocomplete', 'Activate auto-completions', show=True, key_display='ctrl+space')
    ]

    def on_focus(self, event: events.Focus) -> None:
        """PromptInput widget has gained focus."""
        self.post_message(self.FocusChange(True))
    
    def on_blur(self, event: events.Blur) -> None:
        """PromptInput widget has lost focus."""
        self.post_message(self.FocusChange(False))
            
    def action_switch_autocomplete(self) -> None:
        """Switch to the Suggestion focus."""
        self.post_message(self.AutoComplete())
        
    def action_activate_autocomplete(self) -> None:
        """Activate the Suggestions."""
        self.post_message(self.Show(self.cursor_position))
        
    def action_hide(self):
        """Hide the Suggestions."""
        self.post_message(self.Hide())
        
        
class Prompt(Widget):
    """
    Custom Widget for Containing the Prompt Input and Label.
    
    Args:
        prompt (str): The prompt for the shell.
    """
    
    class CommandInput(Message):
        """User Typed into the shell."""
        def __init__(self, cmd_input: str, position: int) -> None:
            super().__init__()
            self.cmd_input = cmd_input
            self.cursor_position = position
            
    
    class CommandEntered(Message):
        """User entered a command."""
        def __init__(self, cmd: str):
            super().__init__()
            self.cmd = cmd

    
    def __init__(
        self, 
        prompt: Annotated[str, 'prompt for the shell.']
    ) -> None:
        super().__init__()
        self.prompt = prompt
    
    def on_mount(self) -> None:
        prompt_input = self.query_one(PromptInput)
        prompt_input.focus()
        
    def compose(self) -> ComposeResult:
        yield Label(f'[b]{self.prompt}[/b]')
        yield PromptInput(select_on_focus=False)
        
    def on_input_changed(self, event: Input.Changed) -> None:
        """
        Catch when the input value has changed and 
        and notify the parent shell of the current input 
        and location of the cursor.
        """
        event.stop()
        prompt_input = self.query_one(PromptInput)
        self.post_message(
            self.CommandInput(
                event.value,
                prompt_input.cursor_position
            )
        )
        
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Catch when a command has been entered.
        """
        event.stop()
        prompt_input = self.query_one(PromptInput)
        prompt_input.value = ''
        prompt_input.action_home()
        self.post_message(self.CommandEntered(event.value))

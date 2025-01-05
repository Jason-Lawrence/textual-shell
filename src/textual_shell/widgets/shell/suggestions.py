from typing import Annotated

from textual import events
from textual.binding import Binding
from textual.message import Message
from textual.widgets import OptionList

class Suggestions(OptionList):
    """Widget for displaying the suggestion for auto-completions as a pop-up."""
    
    class FocusChange(Message):
        """
        A message for when the prompt input 
        has either gained or lost focus.
        """
        def __init__(self, is_focused: bool):
            super().__init__()
            self.is_focused = is_focused
            
            
    class Cycle(Message):
        """
        Cycle the highlighted suggestion.
        
        Args:
            next (str): The next suggestion.
        """
        def __init__(self, next: Annotated[str, 'The next suggestion.']):
            super().__init__()
            self.next = next


    class Continue(Message):
        """Select the current highlighted suggestion."""
        pass
    
    class Hide(Message):
        """Hide the suggestions."""
        pass
    
    class Cancel(Message):
        """Cancel the suggestion and undo the auto-completion."""
        pass
    
    class Execute(Message):
        """Append the suggestion and execute the command"""
        pass
    
    
    BINDINGS = [
        Binding('backspace', 'cancel_completion', 'Cancel Autocompletion'),
        Binding('tab', 'cycle', 'Cycle autocompletion', priority=True),
        Binding('space', 'continue', 'Select suggestion'),
        Binding('escape', 'hide', 'Hide autosuggestion'),
        Binding('enter', 'enter_command', 'Select the suggestion and execute the command.', show=False)
    ]

    def on_focus(self, event: events.Focus) -> None:
        """The Suggestion widget has gained focus."""
        self.post_message(self.FocusChange(True))
    
    def on_blur(self, event: events.Blur) -> None:
        """The Suggestion widget has lost focus."""
        self.post_message(self.FocusChange(False))
      
    def action_cancel_completion(self) -> None:
        """Cancel the auto-completion."""
        self.highlighted = None
        self.post_message(self.Cancel())
      
    def action_cycle(self) -> None:
        """Cycle to the next completion."""
        if self.option_count == 0:
            return 
        
        next = self.highlighted + 1
        if next >= self.option_count:
            next = 0
        
        self.highlighted = next
        suggestion = self.get_option_at_index(next).prompt
        self.post_message(self.Cycle(suggestion))
        
    def action_continue(self) -> None:
        """Select the autocompletion."""
        self.post_message(self.Continue())
        
    def action_hide(self) -> None:
        """Hide the Suggestions"""
        self.post_message(self.Hide())
    
    def action_enter_command(self) -> None:
        """Execute the command"""
        self.post_message(self.Execute())

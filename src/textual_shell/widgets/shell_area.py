from collections import deque
from typing import Annotated

from textual import events
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import TextArea
from textual.widgets.text_area import Location


class ShellArea(TextArea):
    """Base class for textareas to be used for shell like behavior."""

    class Execute(Message):
        """
        Execute the command that was typed.

        Args:
            command (str): The command to execute.
        """
        def __init__(
            self,
            command: Annotated[str, 'The command to execute.'],
        ) -> None:
            super().__init__()
            self.command = command


    BINDINGS = [
        Binding('enter', 'enter_pressed', 'execute command', priority=True),
        Binding('ctrl+c', 'clear', 'Interrupt the current command line.'),
    ]

    history_list: reactive[deque[str]] = reactive(deque)
    current_history_index = None
    prompt = reactive(str)
    multiline = False
    multiline_prompt = ''
    multiline_char = ''

    def on_mount(self):
        self.action_cursor_line_end()

    def watch_prompt(self, prompt) -> None:
        """Switch to the new prompt."""
        self.clear()
        self.insert(self.prompt)

    def action_enter_pressed(self):
        """
        Handler for the enter key.
        If the command has a '\\' at the end
        then it is a multiline command.
        """
        text = self.text
        if text.endswith(self.multiline_char):
            self.insert(self.multiline_prompt)
            self.multiline = True
            return
        
        else:
            text = text[len(self.prompt):]
            self.post_message(self.Execute(text))

        self.current_history_index = None
        self.action_clear()
        self.action_cursor_line_end()
        self.multiline = False

    def action_clear(self):
        """WHen ctrl+c is hit clear the text area."""
        self.text = self.prompt
        self.action_cursor_line_end()

    def action_cursor_up(self, select=False):
        """When the up arrow is hit cycle upwards through the history."""
        if len(self.history_list) == 0:
            return
        
        if self.current_history_index is None:
            self.current_history_index = 0
        
        elif self.current_history_index == len(self.history_list) - 1:
            return
        
        else:
            self.current_history_index += 1
        
        previous_cmd = self.history_list[self.current_history_index]
        
        if self.multiline:
            text = self.text
            self.clear()
            self.insert(text[:self.limit])
            self.insert(previous_cmd)
            
        else:
            self.text = self.prompt + previous_cmd
            self.action_cursor_line_end()

    def action_cursor_down(self, select=False):
        """When the down arrow key is pressed cycle downwards through the history."""
        if len(self.history_list) == 0:
            return
        
        if self.current_history_index == 0:
            self.current_history_index = None
            self.action_clear()
            return
        
        elif self.current_history_index is None:
            return
        
        self.current_history_index -= 1
        previous_cmd = self.history_list[self.current_history_index]
        self.text = self.prompt + previous_cmd
        self.action_cursor_line_end()

    def check_cursor_location(self, location: Location) -> bool:
        """Return true if the location violates the prompt."""
        if self.multiline:
            return location[1] <= 2

        else:
            return location[1] <= len(self.prompt)

    def action_cursor_left(self, select = False):
        if self.check_cursor_location(self.cursor_location):
            return None
        else:
            return super().action_cursor_left(select)
        
    def action_cursor_line_start(self, select = False):
        """"""
        location = self.cursor_location
        if self.multiline:
            self.cursor_location = (location[0], 2)
            
        else:
            self.cursor_location = (location[0], len(self.prompt))
                
    def action_cursor_word_left(self, select=False):
        """Override to prevent moving cursor to prompt."""
        if self.check_cursor_location(self.cursor_location):
            return 
        else:
            return super().action_cursor_word_left(select)
    
    def action_delete_left(self):
        if self.check_cursor_location(self.cursor_location):
            return
        else:
            return super().action_delete_left()
    
    def action_delete_word_left(self):
        """Override to prevent deleting part of the prompt."""
        if self.check_cursor_location(self.cursor_location):
            return
        
        else:
            return super().action_delete_word_left()
        
    def action_delete_to_start_of_line(self):
        """Delete up to the prompt"""
        if self.multiline:
            index = self.text.rfind('\\\n> ') + 4
            text = self.text[:index]
            self.clear()
            self.insert(text)
            
        else:
            self.text = self.prompt
            self.action_cursor_line_end()
            
    def action_cut(self):
        """Basically ctrl+u. Figure out how to do selections."""
        if self.multiline:
            index = self.text.rfind('\\\n> ') + 4
            text = self.text[:index]
            self.clear()
            self.insert(text)
            
        else:
            self.text = self.prompt
            self.action_cursor_line_end()

    def action_cursor_page_down(self):
        """Override to prevent this behavior."""
        return 
    
    def action_cursor_page_up(self):
        """Override to prevent this behavior."""
        return

    def action_select_line(self):
        """Override to prevent this behavior."""
        return
        
    def action_select_all(self):
        """Override to prevent this behavior."""
        return
    
    def _on_mouse_down(self, event: events.MouseDown):
        """Prevent all mouse events"""
        event.stop()
        event.prevent_default()
        
    def _on_mouse_move(self, event: events.MouseMove):
        """Prevent all mouse events"""
        event.stop()
        event.prevent_default()
        
    def _on_mouse_up(self, event: events.MouseUp):
        """Prevent all mouse events"""
        event.stop()
        event.prevent_default()

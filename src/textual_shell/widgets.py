from typing import Annotated, List, Any

from textual import events, work
from textual.app import ComposeResult
from textual.containers import Grid
from textual.geometry import Offset
from textual.reactive import reactive
from textual.message import Message
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Input, 
    Label,
    Markdown,
    OptionList, 
    Rule, 
    TextArea 
)
from textual.worker import Worker, get_current_worker
from textual_shell.command import Command

class HelpScreen(ModalScreen):
    
    def __init__(
        self,
        help_text: Annotated[str, 'THe help text to display in the modal']
    ) -> None:
        super().__init__()
        self.help_text = help_text
    
    def compose(self) -> ComposeResult:
        yield Grid(
            Label('Help', id='help-label'),
            Button('X', variant='error', id='help-close'),
            Markdown(self.help_text, id='help-display'),
            id='help-dialog'
        )
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'help-close':
            self.app.pop_screen()


class CommandList(Widget):
    
    def __init__(
        self, 
        command_list: Annotated[List[str], 'List of commands for the custom shell.']
    ) -> None:
        self.commands = command_list
        super().__init__()
    
    def on_mount(self):
        ta = self.query_one('#cmd-list', TextArea)
        ta.can_focus = False
    
    def compose(self) -> ComposeResult:
        yield Label('Commands', id='cmd-label')
        yield Rule()
        yield TextArea(
            '\n'.join(self.commands),
            read_only=True, 
            id='cmd-list'
        )
        
class PromptInput(Input):
    
    class AutoComplete(Message):
        pass
    
    class Show(Message):
        def __init__(self, cursor: Offset) -> None:
            super().__init__()
            self.cursor_offset = cursor
    
    class Hide(Message):
        pass

    class FocusChange(Message):
        """
        A message for when the prompt input 
        has either gained or lost focus.
        """
        def __init__(self, is_focused: bool):
            super().__init__()
            self.is_focused = is_focused


    def on_focus(self, event: events.Focus) -> None:
        self.post_message(self.FocusChange(True))
    
    def on_blur(self, event: events.Blur) -> None:
        self.post_message(self.FocusChange(False))
    
    def key_tab(self, event: events.Key) -> None:
        event.stop()
        self.post_message(self.AutoComplete())
        
    def key_escape(self, event: events.Key) -> None:
        event.stop()
        self.post_message(self.Hide())
        
    def on_key(self, event: events.Key) -> None:
        if event.key == 'ctrl+@':
            event.stop()
            self.post_message(self.Show(self.cursor_screen_offset))


class Prompt(Widget):
    
    class CommandInput(Message):
        """User Typed into the shell."""
        def __init__(self, cmd_input: str, offset: Offset) -> None:
            super().__init__()
            self.cmd_input = cmd_input
            self.cursor_offset = offset
            
    
    class CommandEntered(Message):
        """User entered a command."""
        def __init__(self, cmd: str):
            super().__init__()
            self.cmd = cmd
            
    cmd_input = reactive('')
    
    def on_mount(self) -> None:
        prompt_input = self.query_one('#prompt-input', PromptInput)
        prompt_input.focus()
        
    def compose(self) -> ComposeResult:
        yield Label('[b]xbsr $> [/b]', id='prompt-label')
        yield PromptInput(id='prompt-input', select_on_focus=False)
        
    def on_input_changed(self, event: Input.Changed) -> None:
        event.stop()
        prompt_input = self.query_one('#prompt-input', PromptInput)
        self.cmd_input = event.value
        self.post_message(
            self.CommandInput(
                self.cmd_input,
                prompt_input.cursor_screen_offset
            )
        )
        
    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        prompt_input = self.query_one('#prompt-input', Input)
        prompt_input.value = ''
        prompt_input.action_home()
        self.post_message(self.CommandEntered(event.value))
        

class Suggestions(OptionList):
    
    class FocusChange(Message):
        """
        A message for when the prompt input 
        has either gained or lost focus.
        """
        def __init__(self, is_focused: bool):
            super().__init__()
            self.is_focused = is_focused
            
            
    class Cycle(Message):
        def __init__(self, next: str):
            super().__init__()
            self.next = next
            
    
    class Continue(Message):
        pass
    
    class Hide(Message):
        """Hide the suggestions."""
        pass
            

    def on_focus(self, event: events.Focus) -> None:
        self.post_message(self.FocusChange(True))
    
    def on_blur(self, event: events.Blur) -> None:
        self.post_message(self.FocusChange(False))
        
    def key_tab(self, event: events.Key) -> None:
        event.stop()
        next = self.highlighted + 1
        if next >= self.option_count:
            next = 0
        
        self.highlighted = next
        suggestion = self.get_option_at_index(next).prompt
        self.post_message(self.Cycle(suggestion))
        
    def key_space(self, event: events.Key) -> None:
        event.stop()
        self.post_message(self.Continue())
        
    def key_escape(self, event: events.Key) -> None:
        event.stop()
        self.post_message(self.Hide())
        

class Shell(Widget):
    
    is_prompt_focused = reactive(True)
    are_suggestions_focused = reactive(False)
    show_suggestions = reactive(False)
    
    def __init__(
        self,
        commands: Annotated[List[Command], 'List of Shell Commands']
    ) -> None:
        super().__init__()
        self.commands = commands
        self.command_list = [cmd.name for cmd in self.commands]
    
    def on_mount(self):
        self.update_suggestions(self.command_list)
        
    def compose(self) -> ComposeResult:
        yield CommandList(self.command_list)
        yield Prompt()
        yield Suggestions(id='auto-complete')
        
    def get_cmd_obj(self, cmd) -> Command:
        for command in self.commands:
            if command.name == cmd:
                return command
            
        return None
        
    def update_suggestions(
        self,
        suggestions: Annotated[List[str], 'suggestions for the ListView.']
    ) -> None:
        ol = self.query_one('#auto-complete', Suggestions)
        ol.clear_options()
        if self.show_suggestions:
            ol.visible = False if len(suggestions) == 0 else True
        ol.add_options(suggestions)
  
    def update_suggestions_location(self, cursor: Offset) -> None:
        ol = self.query_one('#auto-complete', Suggestions)
        ol.styles.offset = (cursor.x, cursor.y)
        
    def update_prompt_input(self, suggestion: str) -> None:
        prompt_input = self.query_one('#prompt-input', PromptInput)
        with prompt_input.prevent(Input.Changed):
            cmd_split = prompt_input.value.split(' ')
            cmd_split[-1] = suggestion
            prompt_input.value = ' '.join(cmd_split)
        
    def on_prompt_input_auto_complete(self, event: PromptInput.AutoComplete) -> None:
        ol = self.query_one('#auto-complete', Suggestions)
        ol.focus()
        if not ol.highlighted:
            ol.highlighted = 0
            
        suggestion = ol.get_option_at_index(ol.highlighted).prompt
        self.update_prompt_input(suggestion)
        
    def on_suggestions_cycle(self, event: Suggestions.Cycle) -> None:
        self.update_prompt_input(event.next)
        
    def on_suggestions_continue(self, event: Suggestions.Continue) -> None:
        prompt_input = self.query_one('#prompt-input', PromptInput)
        prompt_input.value += ' '
        prompt_input.action_end()
        prompt_input.focus()
    
    def on_prompt_input_focus_change(self, event: PromptInput.FocusChange) -> None:
        self.is_prompt_focused = event.is_focused
        
    def on_prompt_input_show(self, event: PromptInput.Show) -> None:
        self.update_suggestions_location(event.cursor_offset)
        self.show_suggestions = True
        
    def on_prompt_input_hide(self, event: PromptInput.Hide) -> None:
        self.show_suggestions = False
    
    # The naming scheme is important.
    def on_prompt_command_input(self, event: Prompt.CommandInput) -> None:
        cmd_input = event.cmd_input.split(' ')
        if len(cmd_input) == 1:
            val = cmd_input[0]
            suggestions = ([cmd for cmd in self.command_list if cmd.startswith(val)] 
                                if val else self.command_list)

        else:
            if cmd_input[0] == 'help':
                if len(cmd_input) < 3:
                    suggestions = self.command_list
                
                else: 
                    suggestions = []
            
            else:
                cmd = self.get_cmd_obj(cmd_input[0])
                suggestions = cmd.get_suggestions(cmd_input[-2])
            
            suggestions = [sub_cmd for sub_cmd in suggestions if sub_cmd.startswith(cmd_input[-1])]
        
        self.update_suggestions(suggestions)
        self.update_suggestions_location(event.cursor_offset)
        
    def on_prompt_command_entered(self, event: Prompt.CommandEntered) -> None:
        cmd_line = event.cmd.split(' ')
        cmd = self.get_cmd_obj(cmd_line.pop(0))
        if cmd.name == 'help':
            if show_help := self.get_cmd_obj(cmd_line[0]):
                res = cmd.execute(show_help)
                self.app.push_screen(HelpScreen(res))
            
        else:
            self.execute_command(cmd, *cmd_line)
        
    def on_suggestions_focus_change(self, event: Suggestions.FocusChange) -> None:
        self.are_suggestions_focused = event.is_focused
        
    def on_suggestions_hide(self, event: Suggestions.Hide) -> None:
        self.show_suggestions = False
    
    def toggle_suggestions(self, toggle: bool):
        ol = self.query_one('#auto-complete', Suggestions)
        ol.visible = toggle
        
    def decide_to_show_suggestions(self) -> None:
        
        if self.show_suggestions:
            
            if self.is_prompt_focused or self.are_suggestions_focused:
                self.toggle_suggestions(True)
        
            else:
                self.toggle_suggestions(False)
        
        else:
            self.toggle_suggestions(False)
    
    def watch_is_prompt_focused(self, is_prompt_focused: bool):
        self.decide_to_show_suggestions()
        
    def watch_are_suggestions_focused(self, are_suggestions_focused: bool):
        self.decide_to_show_suggestions()
            
    def watch_show_suggestions(self, show: bool):
        self.decide_to_show_suggestions()
     
    @work(thread=True)   
    def execute_command(self, cmd: Command, *cmd_line):
        worker = get_current_worker()
        res = cmd.execute(*cmd_line)

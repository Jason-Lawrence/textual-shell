from typing import Annotated, List

from textual import events, work, log
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Container
from textual.geometry import Offset
from textual.reactive import reactive
from textual.message import Message
from textual.widget import Widget
from textual.widgets import (
    DataTable,
    Input, 
    Label,
    OptionList, 
    Rule,
    RichLog,
    TextArea 
)
from textual.worker import Worker, get_current_worker

from . import configure
from .command import Command

class CommandList(Widget):
    
    def __init__(
        self, 
        command_list: Annotated[List[str], 'List of commands for the custom shell.'],
        cmd_label_id: Annotated[str, 'CSS id for the Label']='cmd-label',
        cmd_list_id: Annotated[str, 'CSS id for the TextArea']='cmd-list'
    ) -> None:
        self.commands = command_list
        self.cmd_label_id = cmd_label_id
        self.cmd_list_id = cmd_list_id
        super().__init__()
    
    def on_mount(self):
        ta = self.query_one(f'#{self.cmd_list_id}', TextArea)
        ta.can_focus = False
    
    def compose(self) -> ComposeResult:
        yield Label('Commands', id=self.cmd_label_id)
        yield Rule()
        yield TextArea(
            '\n'.join(self.commands),
            read_only=True, 
            id=self.cmd_list_id
        )
        
class PromptInput(Input):
    
    class AutoComplete(Message):
        pass
    
    class Show(Message):
        def __init__(self, cursor: int) -> None:
            super().__init__()
            self.cursor_position = cursor
    
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
            self.post_message(self.Show(self.cursor_position))


class Prompt(Widget):
    
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
            
    cmd_input = reactive('')
    
    def __init__(
        self, 
        prompt: Annotated[str, 'prompt for the shell.'],
        prompt_input_id: Annotated[str, 'The css id for the prompt input'],
        prompt_label_id: Annotated[str, 'The css id for the prompt label']
    ) -> None:
        super().__init__()
        self.prompt = prompt
        self.prompt_input_id = prompt_input_id
        self.prompt_label_id = prompt_label_id
    
    def on_mount(self) -> None:
        prompt_input = self.query_one(f'#{self.prompt_input_id}', PromptInput)
        prompt_input.focus()
        
    def compose(self) -> ComposeResult:
        yield Label(f'[b]{self.prompt}[/b]', id=self.prompt_label_id)
        yield PromptInput(id=self.prompt_input_id, select_on_focus=False)
        
    def on_input_changed(self, event: Input.Changed) -> None:
        event.stop()
        prompt_input = self.query_one(f'#{self.prompt_input_id}', PromptInput)
        self.cmd_input = event.value
        self.post_message(
            self.CommandInput(
                self.cmd_input,
                prompt_input.cursor_position
            )
        )
        
    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        prompt_input = self.query_one(f'#{self.prompt_input_id}', PromptInput)
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
    
    class Cancel(Message):
        pass
    
    
    BINDINGS = [
        Binding('backspace', 'cancel_completion', 'Cancel Autocompletion'),
        Binding('tab', 'cycle', 'Cycle autocompletion', priority=True),
        Binding('space', 'continue', 'Select autocompletion'),
        Binding('escape', 'hide', 'Hide autosuggestion')
    ]    

    def on_focus(self, event: events.Focus) -> None:
        self.post_message(self.FocusChange(True))
    
    def on_blur(self, event: events.Blur) -> None:
        self.post_message(self.FocusChange(False))
      
    def action_cancel_completion(self) -> None:
        self.highlighted = None
        self.post_message(self.Cancel())
      
    def action_cycle(self) -> None:
        if self.option_count == 0:
            return 
        
        next = self.highlighted + 1
        if next >= self.option_count:
            next = 0
        
        self.highlighted = next
        suggestion = self.get_option_at_index(next).prompt
        self.post_message(self.Cycle(suggestion))
        
    def action_continue(self) -> None:
        self.post_message(self.Continue())
        
    def action_hide(self) -> None:
        self.post_message(self.Hide())
        
        
class SettingsDisplay(Widget):
    
    def __init__(
        self,
        config_path: Annotated[str, 'THe path to the config file.']=None,
        settings_label_id: Annotated[str, 'The css id for the settings label']='settings-label',
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.config_path = config_path
        self.settings_label_id = settings_label_id
        
    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.can_focus = False
        self.column_keys = table.add_columns('setting', 'value')
        config = configure.get_config(self.config_path)
        for section in config:
            for key, val in config[section].items():
                if key == 'description':
                    continue
                
                setting = f'{section}.{key}'
                value = val['value']
                row = (setting, value)
                table.add_row(*row, key=setting)
                
    def compose(self) -> ComposeResult:
        yield Grid(
            Label('Settings', id=self.settings_label_id),
            DataTable()            
        )


class Shell(Widget):
    
    is_prompt_focused = reactive(True)
    are_suggestions_focused = reactive(False)
    show_suggestions = reactive(False)
    history_list: reactive[list[str]] = reactive(list)
    
    BINDINGS = [
        Binding('up', 'up_history', 'Cycle up through the history'),
        Binding('down', 'down_history', 'Cycle down through the history'),
        Binding('ctrl+c', 'clear_prompt', 'Clear the input prompt', priority=True)
    ]
    
    def __init__(
        self,
        commands: Annotated[List[Command], 'List of Shell Commands'],
        prompt: Annotated[str, 'prompt for the shell.'],
        prompt_input_id: Annotated[str, 'The css id for the prompt input']='prompt-input',
        prompt_label_id: Annotated[str, 'The css id for the prompt label']='prompt-label',
        suggestion_id: Annotated[str, 'The css id for the suggestions']='auto-complete',
        suggestion_offset: Annotated[Offset, 'The Offset to draw the suggestions from the shell input']=Offset(0, 4),
        history_id: Annotated[str, 'The css id for the history log']='history-log',
        history_log: Annotated[str, 'The path to write the history log too.']=None,
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.commands = commands
        self.command_list = [cmd.name for cmd in self.commands]
        self.prompt = prompt
        self.prompt_input_id = prompt_input_id
        self.prompt_label_id = prompt_label_id
        self.suggestion_id = suggestion_id
        self.suggestion_offset = suggestion_offset
        self.history_id = history_id
        self.current_history_index = None
        
        for cmd in self.commands:
            cmd.widget = self
    
    def on_mount(self):
        prompt_input = self.query_one(f'#{self.prompt_input_id}', PromptInput)
        self.prompt_input_offset = prompt_input.offset
        self.update_suggestions(self.command_list)
        
    def compose(self) -> ComposeResult:
        yield Container(
            RichLog(id=self.history_id),
            Prompt(
                prompt=self.prompt,
                prompt_input_id=self.prompt_input_id,
                prompt_label_id=self.prompt_label_id
            )
        )
        yield Suggestions(id=self.suggestion_id)
        
    def get_cmd_obj(self, cmd) -> Command:
        for command in self.commands:
            if command.name == cmd:
                return command
            
        return None
        
    def update_suggestions(
        self,
        suggestions: Annotated[List[str], 'suggestions for the ListView.']
    ) -> None:
        ol = self.query_one(f'#{self.suggestion_id}', Suggestions)
        ol.clear_options()
        if self.show_suggestions:
            ol.visible = False if len(suggestions) == 0 else True
        ol.add_options(suggestions)
  
    def update_suggestions_location(self, cursor: int) -> None:
        ol = self.query_one(f'#{self.suggestion_id}', Suggestions)
        ol.styles.offset = (
            self.prompt_input_offset.x + cursor + self.suggestion_offset.x,
            self.prompt_input_offset.y + self.suggestion_offset.y + len(self.history_list) 
        )
        
    def update_prompt_input(self, suggestion: str) -> None:
        prompt_input = self.query_one(f'#{self.prompt_input_id}', PromptInput)
        with prompt_input.prevent(Input.Changed):
            cmd_split = prompt_input.value.split(' ')
            cmd_split[-1] = suggestion
            prompt_input.value = ' '.join(cmd_split)
        
    def on_prompt_input_auto_complete(self, event: PromptInput.AutoComplete) -> None:
        event.stop()
        ol = self.query_one(f'#{self.suggestion_id}', Suggestions)
        if ol.option_count == 0 or not ol.visible:
            return
        
        if not ol.highlighted:
            ol.highlighted = 0
        
        ol.focus()
        suggestion = ol.get_option_at_index(ol.highlighted).prompt
        self.update_prompt_input(suggestion)
        
    def on_suggestions_cycle(self, event: Suggestions.Cycle) -> None:
        event.stop()
        self.update_prompt_input(event.next)
        
    def on_suggestions_continue(self, event: Suggestions.Continue) -> None:
        event.stop()
        prompt_input = self.query_one(f'#{self.prompt_input_id}', PromptInput)
        prompt_input.value += ' '
        prompt_input.action_end()
        prompt_input.focus()
    
    def on_prompt_input_focus_change(self, event: PromptInput.FocusChange) -> None:
        event.stop()
        self.is_prompt_focused = event.is_focused
        
    def on_prompt_input_show(self, event: PromptInput.Show) -> None:
        event.stop()
        self.update_suggestions_location(event.cursor_position)
        self.show_suggestions = True
        
    def on_prompt_input_hide(self, event: PromptInput.Hide) -> None:
        event.stop()
        self.show_suggestions = False
    
    def get_suggestions(self, cmd_line) -> None:
        cmd_input = cmd_line.split(' ')
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
                if cmd := self.get_cmd_obj(cmd_input[0]):
                    suggestions = cmd.get_suggestions(cmd_input[-2])
                
                else:
                    suggestions = []
            
            suggestions = [sub_cmd for sub_cmd in suggestions if sub_cmd.startswith(cmd_input[-1])]
        
        self.update_suggestions(suggestions)
    
    def on_prompt_command_input(self, event: Prompt.CommandInput) -> None:
        event.stop()
        self.get_suggestions(event.cmd_input)
        self.update_suggestions_location(event.cursor_position)
        
    def on_prompt_command_entered(self, event: Prompt.CommandEntered) -> None:
        event.stop()
        if len(event.cmd.strip(' ')) == 0:
            return
        
        cmd_line = event.cmd.split(' ')
        cmd_name = cmd_line.pop(0)
            
        if cmd := self.get_cmd_obj(cmd_name):
            
            if cmd.name == 'help':
                if len(cmd_line) == 0:
                    return
                
                if show_help := self.get_cmd_obj(cmd_line[0]):
                    help_screen = cmd.execute(show_help)
                    self.app.push_screen(help_screen)
                    
                else:
                    self.notify(
                        f'[b]Command:[/b] {cmd_name} does not exist!',
                        severity='error',
                        title='Invalid Command',
                        timeout=5
                    )
                    
            else:
                self.execute_command(cmd, *cmd_line)
        
        else:
            self.notify(
                f'[b]Command:[/b] {cmd_name} does not exist!',
                severity='error',
                title='Invalid Command',
                timeout=5
            )
            return
        
        self.history_list.insert(0, event.cmd)
        self.mutate_reactive(Shell.history_list)
        self.current_history_index = None
        
    def on_suggestions_focus_change(self, event: Suggestions.FocusChange) -> None:
        event.stop()
        self.are_suggestions_focused = event.is_focused
        
    def on_suggestions_hide(self, event: Suggestions.Hide) -> None:
        event.stop()
        prompt_input = self.query_one(f'#{self.prompt_input_id}', PromptInput)
        prompt_input.action_end()
        prompt_input.focus()
        self.show_suggestions = False
        
    def on_suggestions_cancel(self, event: Suggestions.Cancel) -> None:
        event.stop()
        prompt_input = self.query_one(f'#{self.prompt_input_id}', PromptInput)
        
        cmd_line = prompt_input.value.split(' ')
        cmd_line.pop(-1)
        prompt_input.value = " ".join(cmd_line)
        
        if len(prompt_input.value) > 0:
            prompt_input.value += ' '
            
        prompt_input.action_end()
        prompt_input.focus()
        
    
    def toggle_suggestions(self, toggle: bool):
        ol = self.query_one(f'#{self.suggestion_id}', Suggestions)
        if not toggle:
            ol.visible = toggle
            
        if ol.option_count > 0:
            ol.visible = toggle
        
    def decide_to_show_suggestions(self) -> None:
        
        if self.show_suggestions:
            
            if self.is_prompt_focused or self.are_suggestions_focused:
                self.toggle_suggestions(True)
        
            else:
                self.toggle_suggestions(False)
        
        else:
            self.toggle_suggestions(False)
    
    def watch_is_prompt_focused(self, is_prompt_focused: bool) -> None:
        self.decide_to_show_suggestions()
        
    def watch_are_suggestions_focused(self, are_suggestions_focused: bool) -> None:
        self.decide_to_show_suggestions()
            
    def watch_show_suggestions(self, show: bool) -> None:
        self.decide_to_show_suggestions()
        
    def watch_history_list(self, history_list: List[str]) -> None:
        try:
            rich_log = self.query_one(f'#{self.history_id}', RichLog)
            rich_log.write(f'{self.prompt}{history_list[0]}')

        except:
            return
        
    def action_clear_prompt(self) -> None:
        prompt_input = self.query_one(f'#{self.prompt_input_id}', PromptInput)
        prompt_input.value = ''
        prompt_input.action_home()
        
        ol = self.query_one(f'#{self.suggestion_id}', Suggestions)
        ol.highlighted = None
        
        if ol.has_focus:
            prompt_input.focus()
        
        self.current_history_index = None
        
    def action_up_history(self):
        if len(self.history_list) == 0:
            return
        
        if self.current_history_index is None:
            self.current_history_index = 0
        
        elif self.current_history_index == len(self.history_list) - 1:
            return
        
        else:
            self.current_history_index += 1
        
        previous_cmd = self.history_list[self.current_history_index]
        prompt_input = self.query_one(f'#{self.prompt_input_id}', PromptInput)
        prompt_input.value = previous_cmd
        prompt_input.action_end()
    
    def action_down_history(self):
        if len(self.history_list) == 0:
            return
        
        if self.current_history_index == 0:
            self.current_history_index = None
            self.action_clear_prompt()
            return
        
        elif self.current_history_index is None:
            return
        
        prompt_input = self.query_one(f'#{self.prompt_input_id}', PromptInput)
        self.current_history_index -= 1
        previous_cmd = self.history_list[self.current_history_index]
        prompt_input.value = previous_cmd
        prompt_input.action_end()
        
    @work(thread=True)   
    def execute_command(self, cmd: Command, *cmd_line):
        worker = get_current_worker()
        res = cmd.execute(*cmd_line)

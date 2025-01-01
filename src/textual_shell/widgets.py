import logging
from typing import Annotated, List
from datetime import datetime

from rich.logging import RichHandler

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
    RichLog,
    TextArea 
)
from textual.worker import Worker, get_current_worker

from . import configure
from .command import Command

class CommandList(Widget):
    """
    Custom widget for listing commands for the shell.
    
    Args:
        command_list (List[str]): List of commands for the custom shell.
        cmd_label_id (str): CSS id for the Label.
            Defaults to cmd-label.
        cmd_list_id (str): CSS id for the TextArea.
            Defaults to cmd-list.
            
    """
    
    DEFAULT_CSS = """
        CommandList {
            background: transparent;
            border: round white;
            height: auto;
            width: 20;
            layout: vertical;
            
            Label {
                text-align: center;
            }
            
            TextArea {
                background: transparent;
                border: none;
                border-top: solid white;
                text-align: center;
            }
        }
    """
    
    def __init__(
        self, 
        command_list: Annotated[List[str], 'List of commands for the custom shell.'],
    ) -> None:
        self.commands = command_list
        super().__init__()
    
    def on_mount(self):
        ta = self.query_one(TextArea)
        ta.can_focus = False
    
    def compose(self) -> ComposeResult:
        yield Label('Commands')
        yield TextArea(
            '\n'.join(self.commands),
            read_only=True
        )
        
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
        prompt_input_id (str): The CSS id for the prompt input.
        prompt_label_id (str): The CSS id for the prompt label.
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
            
    DEFAULT_CSS = """
        
    """
            
    cmd_input = reactive('')
    
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
        self.cmd_input = event.value
        self.post_message(
            self.CommandInput(
                self.cmd_input,
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
    
    
    BINDINGS = [
        Binding('backspace', 'cancel_completion', 'Cancel Autocompletion'),
        Binding('tab', 'cycle', 'Cycle autocompletion', priority=True),
        Binding('space', 'continue', 'Select autocompletion'),
        Binding('escape', 'hide', 'Hide autosuggestion')
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
        
        
class SettingsDisplay(Widget):
    """Custom widget for displaying settings for the shell."""
    
    DEFAULT_CSS = """
    
        SettingsDisplay {
            grid-size: 2;
            grid-columns: 1fr;
            grid-rows: auto 1fr;
            border: solid white;
            height: 15;
                
            Label {
                text-align: center;
                column-span: 2;
            }
            
            DataTable {
                column-span: 2;
                border-top: solid white;
            }
        }
    """
    
    def __init__(
        self,
        config_path: Annotated[str, 'THe path to the config file.']=None,
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.config_path = config_path
        
    def on_mount(self) -> None:
        """Load the settings from the config on mount."""
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
        yield Label('Settings')
        yield DataTable()            
        


class Shell(Widget):
    """
    Main custom widget for the shell.
    Pressing the up arrow key will cycle up through the history.
    Pressing the down arrow key will cycle down through the history,
    Pressing ctrl+c will clear the prompt input.
    
    Args:
        commands (List[Command]): List of shell commands.
        prompt (str): prompt for the shell.
        prompt_input_id (str): The CSS id for the prompt input.
        prompt_label_id (str): The CSS id for the prompt label.
        suggestion_id (str): The CSS id for the suggestion widget.
        suggestion_offset (Offset): The offset to draw the suggestion.
        history_id (str): The CSS id for the rich log.
        history_log (str): The path for the history log file. 
    """
    
    is_prompt_focused = reactive(True)
    are_suggestions_focused = reactive(False)
    show_suggestions = reactive(False)
    history_list: reactive[list[str]] = reactive(list)
    
    BINDINGS = [
        Binding('up', 'up_history', 'Cycle up through the history'),
        Binding('down', 'down_history', 'Cycle down through the history'),
        Binding('ctrl+c', 'clear_prompt', 'Clear the input prompt', priority=True)
    ]
    
    DEFAULT_CSS = """
        Shell Container {
            border: round white;
            height: auto;
        }
        
        Shell RichLog {
            height: auto;
            max-height: 10;
            padding: 0 1;
            background: transparent;
            border: hidden;
        }
        
        Prompt {
            margin: 0;
            padding-top: 0;
            height: 1;
            layout: horizontal;
        
            Label {
                padding: 0;
                padding-left: 1;
            }
            
            PromptInput {
                border: hidden;
                background: transparent;
                margin-left: 0;
                padding-left: 0;
            }
            
            PromptInput:focus {
                border: none;
                padding: 0;
            }
        }
        
        Suggestions {
            layer: popup;
            height: auto;
            width: 20;
            border: round white;
            padding: 0;
        }
        
        Suggestions:focus {
            border: round white;
            padding: 0;
        }
    """
    
    def __init__(
        self,
        commands: Annotated[List[Command], 'List of Shell Commands'],
        prompt: Annotated[str, 'prompt for the shell.'],
        suggestion_offset: Annotated[Offset, 'The Offset to draw the suggestions from the shell input']=Offset(0, 4),
        history_log: Annotated[str, 'The path to write the history log too.']=None,
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.commands = commands
        self.command_list = [cmd.name for cmd in self.commands]
        self.prompt = prompt
        self.suggestion_offset = suggestion_offset
        self.current_history_index = None
        
        for cmd in self.commands:
            cmd.widget = self
            
    def _get_prompt(self) -> Prompt:
        """
        Query the DOM for the child Prompt widget.
        
        Returns:
            prompt (Prompt): The child widget.
        """
        return self.query_one(Prompt)
    
    def _get_prompt_input(self) -> PromptInput:
        """
        Retrieve the PromptInput widget from the DOM.
        
        Returns:
            prompt_input (PromptInput): The child widget.
        """
        prompt = self._get_prompt()
        return prompt.query_one(PromptInput)
        
    def on_mount(self):
        """Update the location and suggestions for auto-completions."""
        prompt_input = self._get_prompt_input()
        self.prompt_input_offset = prompt_input.offset
        self.update_suggestions(self.command_list)
        
    def compose(self) -> ComposeResult:
        yield Container(
            RichLog(markup=True),
            Prompt(
                prompt=self.prompt,
            )
        )
        yield Suggestions()
        
    def get_cmd_obj(
        self,
        cmd: Annotated[str, 'The name of the command.']
    ) -> Command:
        """
        Retrieve the cmd instance.
        
        Args:
            cmd (str): The name of the command.
            
        Returns:
            command (Command): The command instance for the command.
        """
        for command in self.commands:
            if command.name == cmd:
                return command
            
        return None
        
    def update_suggestions(
        self,
        suggestions: Annotated[List[str], 'suggestions for the OptionList.']
    ) -> None:
        """
        Update the list of Suggestions.
        
        Args:
            suggestions (List[str]): The new suggestions.
            
        """
        ol = self.query_one(Suggestions)
        ol.clear_options()
        if self.show_suggestions:
            ol.visible = False if len(suggestions) == 0 else True
        ol.add_options(suggestions)
  
    def update_suggestions_location(
        self, 
        cursor: Annotated[int, 'The x location of the cursor.']
    ) -> None:
        """
        Update the location of the Suggestions.
        
        Args:
            cursor (int): The x location of the cursor.
        """
        rich_log = self.query_one(RichLog)
        log(f'Max-height: {rich_log.styles.max_height}')
        ol = self.query_one(Suggestions)
        ol.styles.offset = (
            self.prompt_input_offset.x + cursor + self.suggestion_offset.x,
            self.prompt_input_offset.y + self.suggestion_offset.y + min(
                len(self.history_list), rich_log.styles.max_height.value
            )
        )

    def update_prompt_input(
        self,
        suggestion: Annotated[str, 'The selected suggestion.']
    ) -> None:
        """
        Add the suggestion to the prompt input.
        This will prevent Input.Changed events from generating.
        
        Args:
            suggestion (str): The selected suggestion.
        """
        prompt_input = self._get_prompt_input()
        with prompt_input.prevent(Input.Changed):
            cmd_split = prompt_input.value.split(' ')
            cmd_split[-1] = suggestion
            prompt_input.value = ' '.join(cmd_split)
        
    def on_prompt_input_auto_complete(
        self,
        event: PromptInput.AutoComplete
    ) -> None:
        event.stop()
        ol = self.query_one(Suggestions)
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
        prompt_input = self._get_prompt_input()
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
        prompt_input = self._get_prompt_input()
        prompt_input.action_end()
        prompt_input.focus()
        self.show_suggestions = False
        
    def on_suggestions_cancel(self, event: Suggestions.Cancel) -> None:
        event.stop()
        prompt_input = self._get_prompt_input()
        
        cmd_line = prompt_input.value.split(' ')
        cmd_line.pop(-1)
        prompt_input.value = " ".join(cmd_line)
        
        if len(prompt_input.value) > 0:
            prompt_input.value += ' '
            
        prompt_input.action_end()
        prompt_input.focus()
        
    
    def toggle_suggestions(self, toggle: bool):
        ol = self.query_one(Suggestions)
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
            rich_log = self.query_one(RichLog)
            rich_log.write(f'{self.prompt}{history_list[0]}')

        except:
            return
        
    def action_clear_prompt(self) -> None:
        prompt_input = self._get_prompt_input()
        prompt_input.value = ''
        prompt_input.action_home()
        
        ol = self.query_one(Suggestions)
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
        prompt_input = self._get_prompt_input()
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
        
        prompt_input = self._get_prompt_input()
        self.current_history_index -= 1
        previous_cmd = self.history_list[self.current_history_index]
        prompt_input.value = previous_cmd
        prompt_input.action_end()
        
    @work(thread=True)   
    def execute_command(self, cmd: Command, *cmd_line):
        worker = get_current_worker()
        res = cmd.execute(*cmd_line)


class CommandLog(Widget):
    
    DEFAULT_CSS = """
        CommandLog {
            height: 50;
            border: round white;
            
            Label {
                text-align: center;
                width: auto;
            }
            
            RichLog {
                height: auto;
                max-height: 50;
                border: none;
                border-top: solid white;
                background: transparent;
            }
        }
    """
    
    COLOR_MAPPING = {
        logging.INFO: 'steel_blue1',
        logging.DEBUG: 'green1',
        logging.WARNING: 'yellow1',
        logging.ERROR: 'bright_red',
        logging.CRITICAL: 'dark_red'
    }
    
    def compose(self) -> ComposeResult:
        yield Container(
            Label('Command Log'),
            RichLog(markup=True)
        )
        
    def gen_record(self, event: Command.Log) -> str:
        level_name = logging.getLevelName(event.severity)
        color = self.COLOR_MAPPING[event.severity]
        
        lvl = f'[{color}]{level_name}[/{color}]'
        cmd = f'[bold magenta1]{event.command.upper()}[/bold magenta1]'
        time = f"[steel_blue]{datetime.now().strftime('[%H:%M:%S]')}[/steel_blue]"
        
        msg = f'{time} {lvl}  {cmd} - {event.msg}'
        return msg

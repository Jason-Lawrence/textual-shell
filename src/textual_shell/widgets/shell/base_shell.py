from collections import deque
from typing import Annotated, List

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.geometry import Offset
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, RichLog

from ...commands import Command
from .prompt import Prompt, PromptInput
from .suggestions import Suggestions


class BaseShell(Widget):
    """
    Main custom widget for the shell.
    Pressing the up arrow key will cycle up through the history.
    Pressing the down arrow key will cycle down through the history,
    Pressing ctrl+c will clear the prompt input.
    
    Args:
        commands (List[Command]): List of shell commands.
        prompt (str): prompt for the shell.
        history_log (str): The path for the history log file. 
    """
    
    is_prompt_focused = reactive(True)
    are_suggestions_focused = reactive(False)
    show_suggestions = reactive(False)
    history_list: reactive[deque[str]] = reactive(deque)
    
    BINDINGS = [
        Binding('up', 'up_history', 'Cycle up through the history'),
        Binding('down', 'down_history', 'Cycle down through the history'),
        Binding('ctrl+c', 'clear_prompt', 'Clear the input prompt', priority=True)
    ]
    
    def __init__(
        self,
        commands: Annotated[List[Command], 'List of Shell Commands'],
        prompt: Annotated[str, 'prompt for the shell.'],
        history_log: Annotated[str, 'The path to write the history log too.']=None,
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.commands = commands
        self.command_list = [cmd.name for cmd in self.commands]
        self.prompt = prompt
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
        self.get_offset()
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
    
    def get_offset(self) -> None:
        """Calculate the offset for the cursor location."""
        prompt_input = self._get_prompt_input()
        self.prompt_input_offset = Offset(
            prompt_input.offset.x + len(self.prompt) + 1,
            prompt_input.offset.y + 2
        )
        
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
        ol = self.query_one(Suggestions)
        ol.styles.offset = (
            self.prompt_input_offset.x + cursor,
            self.prompt_input_offset.y + min(
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
        """
        Handle auto complete request. 
        
        Args:
            event (PromptInput.AutoComplete)
        """
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
        """
        Update the prompt input with the next suggestion.
        
        Args:
            event (Suggestions.Cycle)
        """
        event.stop()
        self.update_prompt_input(event.next)
        
    def on_suggestions_continue(self, event: Suggestions.Continue) -> None:
        """
        Add a space to the prompt_input and switch back focus.
        
        Args:
            event (Suggestions.Continue)
        """
        event.stop()
        prompt_input = self._get_prompt_input()
        prompt_input.value += ' '
        prompt_input.action_end()
        prompt_input.focus()
        
    def on_suggestions_execute(self, event: Suggestions.Execute) -> None:
        """
        Execute the command.
        
        Args:
            event (Suggestions.Execute)
        """
        event.stop()
        prompt_input = self._get_prompt_input()
        self.command_entered(prompt_input.value)
        prompt_input.value = ''
        prompt_input.action_home()
        prompt_input.focus()
    
    def on_prompt_input_focus_change(self, event: PromptInput.FocusChange) -> None:
        """
        Handler for when the prompt_input has gained or lost focus.
        
        Args:
            event (PromptInput.FocusChange)
        """
        event.stop()
        self.is_prompt_focused = event.is_focused
        
    def on_prompt_input_show(self, event: PromptInput.Show) -> None:
        """
        Handler for showing the Suggestions.
        
        Args:
            event (PromptInput.Show)
        """
        event.stop()
        self.update_suggestions_location(event.cursor_position)
        self.show_suggestions = True
        
    def on_prompt_input_hide(self, event: PromptInput.Hide) -> None:
        """
        Handler for hiding the Suggestions.
        
        Args:
            event (PromptInput.Hide)
        """
        event.stop()
        self.show_suggestions = False
    
    def get_suggestions(
        self,
        cmd_line: Annotated[str, 'The input from the prompt.']
    ) -> None:
        """
        Get the suggestions for the current state of the command line.
        
        Args:
            cmd_line (str): The input from the prompt.
        """
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
        """
        Handler for when the user has typed into the prompt.
        
        Args:
            event (Prompt.CommandInput)
        """
        event.stop()
        self.get_suggestions(event.cmd_input)
        self.update_suggestions_location(event.cursor_position)
        
    def command_entered(
        self,
        cmdline: Annotated[str, 'The command line entered.']
    ) -> None:
        """
        Handler for how the shell should go about executing the command.
        Please override this in your shell.
        
        Args:
            cmdline (str): The command line entered.
        
        Raises:
            NotImplementedError: If not overridden in a derived class.
        """
        raise NotImplementedError('Subclasses must override.')
        
    def on_prompt_command_entered(self, event: Prompt.CommandEntered) -> None:
        """
        Handler for when a command has been entered.
        Execute the command in a worker thread.
        
        Args:
            event (Prompt.CommandEntered)
        """
        event.stop()
        self.command_entered(event.cmd)
        
    def on_suggestions_focus_change(self, event: Suggestions.FocusChange) -> None:
        """
        Handler for when the focus on the Suggestions widget changes.
        
        Args:
            event (Suggestions.FocusChange) 
        """
        event.stop()
        self.are_suggestions_focused = event.is_focused
        
    def on_suggestions_hide(self, event: Suggestions.Hide) -> None:
        """
        Handler for hiding the Suggestions.
        
        Args:
            event (Suggestions.Hide)
        """
        event.stop()
        prompt_input = self._get_prompt_input()
        prompt_input.action_end()
        prompt_input.focus()
        self.show_suggestions = False
        
    def on_suggestions_cancel(self, event: Suggestions.Cancel) -> None:
        """
        Handler for canceling the suggestion
        
        Args:
            event (Suggestions.Cancel)
        """
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
        """
        Handler for hiding or showing the suggestions pop up.
        
        Args:
            toggle (bool): If True show the suggestions as long as there are
                suggestions else False will hide them.
        """
        ol = self.query_one(Suggestions)
        if not toggle:
            ol.visible = toggle
            
        if ol.option_count > 0:
            ol.visible = toggle
        
    def decide_to_show_suggestions(self) -> None:
        """
        Based on reactive attributes evaluate whether to show
        or hide the suggestions.
        """
        if self.show_suggestions:
            
            if self.is_prompt_focused or self.are_suggestions_focused:
                self.toggle_suggestions(True)
        
            else:
                self.toggle_suggestions(False)
        
        else:
            self.toggle_suggestions(False)
    
    def watch_is_prompt_focused(self, is_prompt_focused: bool) -> None:
        """
        Watcher for when the prompt gains or loses focus.
        
        Args:
            is_prompt_focused (bool): The reactive attribute.
        """
        self.decide_to_show_suggestions()
        
    def watch_are_suggestions_focused(self, are_suggestions_focused: bool) -> None:
        """
        Watcher for when the suggestions gains or lose focus.
        
        Ars:
            are_suggestions_focused (bool): The reactive attribute.
        """
        self.decide_to_show_suggestions()
            
    def watch_show_suggestions(self, show_suggestions: bool) -> None:
        """
        Watcher for when to show suggestions.
        
        Args:
            show_suggestions (bool): The reactive attribute.
        """
        self.decide_to_show_suggestions()
        
    def watch_history_list(self, history_list: deque[str]) -> None:
        """
        Watcher for when the history has been updated.
        
        Args:
            history_list (List[str]): The history of the command line.
        """
        try:
            rich_log = self.query_one(RichLog)
            rich_log.write(f'{self.prompt}{history_list[0]}')

        except:
            return
        
    def action_clear_prompt(self) -> None:
        """
        When ctrl+c is pressed clear the command line.
        """
        prompt_input = self._get_prompt_input()
        prompt_input.value = ''
        prompt_input.action_home()
        
        ol = self.query_one(Suggestions)
        ol.highlighted = None
        
        if ol.has_focus:
            prompt_input.focus()
        
        self.current_history_index = None
        
    def action_up_history(self):
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
        prompt_input = self._get_prompt_input()
        prompt_input.value = previous_cmd
        prompt_input.action_end()
    
    def action_down_history(self):
        """When the down arrow key is pressed cycle downwards through the history."""
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
        
    # @work(thread=True)   
    # def execute_command(self, cmd: Command, *cmd_line):
    #     """
    #     Execute the command in a worker Thread.
        
    #     Args:
    #         cmd (Command): The command to be executed.
    #         cmd_line (*args): a list of positional arguments for the command.
    #     """
    #     res = cmd.execute(*cmd_line)
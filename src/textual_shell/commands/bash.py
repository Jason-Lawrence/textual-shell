import asyncio
import os
from collections import deque
from typing import Annotated

from textual import log, events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import RichLog, TextArea
from textual.widgets.text_area import Location


from ..command import Command, CommandNode
from ..job import Job

class BashTextArea(TextArea):
    """Custom TextArea to somewhat replicate a Bash shell interface."""
    
    class Execute(Message):
        """
        Execute the command that was typed in the text area.
        
        Args:
            text (str): The command in the text area
        """
        def __init__(
            self,
            text: Annotated[str, 'The command in the text area.']
        ) -> None:
            super().__init__()
            self.text = text
            
            
    class ShowSuggestions(Message):
        """
        Send suggestions to be written to the rich log.
        
        Args:
            cmd (str): The current command line.
            suggestions (list[str]): Suggestions for auto complete.
        """
        def __init__(self, cmd: str, suggestions: list[str]):
            super().__init__()
            self.cmd = cmd
            self.suggestions = suggestions
        
    
    BINDINGS = [
        Binding('enter', 'enter_pressed', 'execute command', priority=True),
        Binding('ctrl+c', 'clear', 'Interrupt the current command line.'),
        Binding('up', 'up_history', 'Cycle up through the history.', show=False),
        Binding('down', 'down_history', 'Cycle down through the history', show=False),
        Binding('tab', 'autocomplete', 'Auto complete the path.', show=False)
    ]
    
    COMPLETION_COMMANDS: tuple[str] = (
        './',
        '../',
        'cd',
        'ls',
        'mkdir',
        'rm',
        'touch',
    )
    
    history_list: reactive[deque[str]] = reactive(deque)
    current_history_index = None
    prompt = reactive(str)
    shell_working_directory = os.getcwd()
    multiline = False

    def on_mount(self):
        self.action_cursor_line_end()

    def watch_prompt(self, prompt) -> None:
        """Switch to the new prompt."""
        self.clear()
        self.insert(self.prompt)
        self.shell_working_directory = self.prompt.split(':')[-1][:-2]
        
    def send_suggestions(self, suggestions: list[str]) -> None:
        """
        Send the message for showing suggestions.
        
        Args:
            suggestions (list[str]): The suggestions.
        """
        self.post_message(
            self.ShowSuggestions(
                cmd=self.text[len(self.prompt):],
                suggestions=suggestions
            )
        )
        
    def match_options(
        self,
        options: list[str],
        pattern: str
    ) -> list[str]:
        """
        Match options to the pattern.
        
        Args:
            options (list[str]): The suggestions.
            pattern (str): The pattern to match against.
        
        Returns:
            suggestions (list[str]): The suggestions that 
                started with the pattern.
        """
        return [option for option in options if option.startswith(pattern)]
                
    def action_autocomplete(self):
        """On TAB try an auto complete the path or show 
        suggestions for auto completions."""
        if self.text.count(' && ') > 0:
            cmd = self.text.split(' && ')[-1]
        
        else:
            cmd = self.text[len(self.prompt):]
         
        if cmd.startswith(self.COMPLETION_COMMANDS):
            try:
                path = cmd.split(' ')[-1]
                if path == '':
                    suggestions = os.listdir(self.shell_working_directory)
                    self.send_suggestions(suggestions)
                    
                elif path == '.':
                    suggestions = ['./', '../']
                    others = os.listdir(self.shell_working_directory)
                    suggestions.extend(self.match_options(others, path))
                    self.send_suggestions(suggestions)
                    
                elif path == '..':
                    self.insert('/')
                
                else:
                    index = path.rfind('/')
                    if index < 0:
                        options = os.listdir(self.shell_working_directory)
                        suggestions = self.match_options(options, path)
                        
                        if len(suggestions) == 0: 
                            return
                        
                        elif len(suggestions) == 1:
                            suggestion = suggestions.pop()
                            self.insert(suggestion[len(path):])
                            return
                        
                        else:
                            self.send_suggestions(suggestions)
                    
                    elif index == 0:
                        options = os.listdir('/')
                        if len(path) == 1:
                            self.send_suggestions(options)
                            return
                        
                        suggestions = self.match_options(options, path[1:])
                        if len(suggestions) == 0:
                            return
                        
                        elif len(suggestions) == 1:
                            suggestion = suggestions.pop()
                            self.insert(suggestion[len(path[1:]):])
                        
                        else:
                            self.send_suggestions(suggestions)
                        
                    else:
                        path_to_list = path[:index]
                        options = os.listdir(f'{self.shell_working_directory}/{path_to_list}')
                        path_to_match = path[index:]
                        log(f'MATCH: {path_to_match}')
                        
                        if path_to_match == '/':
                            suggestions = options
                            
                        else:
                            suggestions = self.match_options(options, path_to_match[1:])
                            
                        log(f'SUGGESTIONS: {suggestions}')
                        
                        if len(suggestions) == 0:
                            return
                        
                        elif len(suggestions) == 1:
                            suggestion = suggestions.pop()
                            self.insert(suggestion[len(path_to_match[1:]):])
                        
                        else:
                            self.send_suggestions(suggestions)
            except:
                pass
            
    def action_enter_pressed(self):
        """
        Handler for the enter key.
        If the command has a '\\' at the end
        then it is a multiline command.
        """
        text = self.text
        if text.endswith('\\'):
            self.insert('\n> ')
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
        
        if self.multiline:
            text = self.text
            self.clear()
            self.insert(text[:self.limit])
            self.insert(previous_cmd)
            
        else:
            self.text = self.prompt + previous_cmd
            self.action_cursor_line_end()
        
    def action_down_history(self):
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
            
    def action_cursor_up(self, select) -> None:
        """Override to prevent this behavior."""
        return
    
    def action_cursor_down(self, select = False):
        """OVerride to prevent this behavior."""
        return
        
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
    
    
class BashShell(Screen):
    """
    Screen to render the Bash shell
    
    Args:
        task (asycnio.Task): The asyncio task of the job the shell is running in.
    """
    INCOMPATIBLE_COMMANDS: tuple[str] = (
        'more',
        'vim',
        'vi'
    )
    
    BINDINGS = [
        Binding('ctrl+z', 'background_job', 'Background the job.', priority=True),
        Binding('ctrl+d', 'kill_shell', 'Close the shell', priority=True),
    ]
    
    DEFAULT_CSS = """
        RichLog {
            height: auto;
            padding-left: 1;
            max-height: 90%;
            border: hidden;
            background: transparent;
        }
        
        TextArea {
            height: auto;
            border: hidden;
            background: transparent;
        }
        
        TextArea:focus {
            border: none;
        }
    """
    
    user = reactive(str)
    current_dir = reactive(str)
    prompt = reactive(str)
    
    def __init__(
        self,
        task: Annotated[asyncio.Task, 'The asyncio task of the job the shell is running in.'],
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.shell_task = task
        self.run_worker(self.setup())
        
    def compose(self) -> ComposeResult:
        yield RichLog(markup=True, wrap=True)
        yield BashTextArea()
    
    def on_mount(self) -> None:
        self.user = os.environ.get('USER', 'user')
        self.current_dir = os.getcwd()
        self.create_prompt()
        
        text_area = self.query_one(BashTextArea)
        text_area.focus()
        
    def create_prompt(self) -> None:
        """Take the current user and current directory 
        and make a prompt for the shell"""
        self.prompt = f'{self.user}:{self.current_dir}$ '
        
    def action_background_job(self) -> None:
        """Background the bash shell and 
        return to the main screen."""
        self.app.pop_screen()
    
    def action_kill_shell(self) -> None:
        """Kill the bash shell job and 
        return to the main screen"""
        for task in self.tasks:
            task.cancel()
        
        self.shell_task.cancel()
        self.app.pop_screen()
        
    async def setup(self):
        """Spawn the child process to run the bash shell.
        Also create the tasks for reading stdout and stderr."""
        self.BASH_SHELL = await asyncio.create_subprocess_exec(
            'bash',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_task = asyncio.create_task(
            self.read_stdout(),
            name='stdout_task'
        )
        
        stderr_task = asyncio.create_task(
            self.read_stderr(),
            name='stderr_task'
        )
        
        self.tasks = [stdout_task, stderr_task]
        
    def handle_cd(self, cmd: str) -> None:
        """
        update the current directory for the prompt.
        Check to see if it was a compound command. If so
        then split it and check to see if each command was cd.
        recursively call this command to handle each cd command. 
        
        Args:
            cmd (str): The command that was entered.
        """
        if cmd.count(' && ') > 0:
            cmds = cmd.split(' && ')
            for cmd in cmds:
                if cmd.startswith('cd'):
                    self.handle_cd(cmd)
        
        else:
            cmd = cmd.strip()
            if len(cmd) == 2 and cmd == 'cd':
                self.current_dir = os.environ.get('HOME')
            
            elif cmd.startswith('cd '):
                path = cmd[3:].strip()
                
                if path.startswith('$'):
                    path = os.environ.get(path[1:], None)
                    if path is None:
                        return
                    
                new_dir = os.path.abspath(os.path.join(self.current_dir, path))
                
                if os.path.isdir(new_dir):
                    self.current_dir = new_dir
                    
            else:
                return
            
    def handle_su(self) -> None:
        """Handle switching users. 
        Check to see if the user ENV variable has changed."""
        new_user = os.environ.get('USER')
        if new_user != self.user:
            self.user = new_user
        
    async def on_bash_text_area_execute(
        self,
        event: BashTextArea.Execute
    ) -> None:
        """
        Execute the command by piping it into stdin of the bash shell.
        The clear command is not piped into the bash shell as it screws with
        output. Only the RichLog needs to be cleared anyway.
        
        Args:
            event (BashTextArea.Execute): The message with the command.
        """
        rich_log = self.query_one(RichLog)
        text_area = self.query_one(BashTextArea)
        
        text = event.text.replace('\\\n> ', '').strip()
            
        if text != '':
            text_area.history_list.appendleft(text)
            
        if text == 'clear':
            rich_log.clear()
            return
        
        elif text == 'exit':
            self.action_kill_shell()
        
        elif text.count(' && ') > 0:
            cmds = text.split(' && ')
            for cmd in cmds:
                if cmd.startswith(self.INCOMPATIBLE_COMMANDS):
                    rich_log.write(self.prompt + event.text)
                    await self.update_from_stderr(f'COMMAND: {cmd} is not compatible')
                    return
                
        elif text.startswith(self.INCOMPATIBLE_COMMANDS):
            rich_log.write(self.prompt + event.text)
            await self.update_from_stderr(f'COMMAND: {text} is not compatible')
            return
            
        self.BASH_SHELL.stdin.write(text.encode() + b'\n')
        await self.BASH_SHELL.stdin.drain()
          
        rich_log.write(self.prompt + event.text)
        
        if text.count('cd') > 0:
            self.handle_cd(text)
            
        if text.count('su') > 0:
            self.handle_su()
            
    def on_bash_text_area_show_suggestions(
        self,
        event: BashTextArea.ShowSuggestions) -> None:
        """
        Show available suggestions for tab completions
        
        Args:
            event (BashTextArea.ShowSuggestions):
                The event for showing suggestions.
        """
        rich_log = self.query_one(RichLog)
        rich_log.write(self.prompt + event.cmd)
        rich_log.write('\t'.join(event.suggestions))

    async def update_from_stdout(self, output) -> None:
        """Take stdout and write it to the RichLog."""
        rich_log = self.query_one(RichLog)
        rich_log.write(output)
        
    async def update_from_stderr(self, error) -> None:
        """Take from stderr and write it to the RichLog."""
        rich_log = self.query_one(RichLog)
        rich_log.write(error)
        
    async def read_stdout(self):
        """Coroutine for reading stdout and updating the RichLog."""
        try:
            async for line in self.BASH_SHELL.stdout:
                decoded = line.decode().strip()
                await self.update_from_stdout(decoded)
        
        except asyncio.CancelledError:
            return
            
    async def read_stderr(self):
        """Coroutine for reading stderr and updating the RichLog."""
        try:
            async for line in self.BASH_SHELL.stderr:
                decoded = line.decode().strip()
                await self.update_from_stderr(decoded)

        except asyncio.CancelledError:
            return
        
    def watch_user(self) -> None:
        """When the user changes update the prompt."""
        self.create_prompt()
        
    def watch_current_dir(self) -> None:
        """When the working directory changes update the prompt."""
        self.create_prompt()
        
    def watch_prompt(self) -> None:
        """Whenever the prompt changes update the text area."""
        textarea = self.query_one(BashTextArea)
        textarea.prompt = self.prompt
        

class RunBashShell(Job):
    """Job for managing and executing a bash shell."""
    
    async def execute(self):
        """Create and install the screen for the bash shell.
        Wait for the user to kill the shell."""
        self.running()
        
        self.screen = BashShell(self.task)
        self.shell.app.install_screen(self.screen, name=self.id)
        self.shell.app.push_screen(self.screen)
        
        await self.wait_for_cancel()
        
        self.shell.app.uninstall_screen(self.screen)
        self.completed()


class Bash(Command):
    """Command for executing a bash shell."""
    
    DEFINITION = {
        'bash': CommandNode(
            name='bash',
            description='Spawn a Bash Shell'
        )
    }
    
    def create_job(self, *args) -> RunBashShell:
        """Create a Job for to execute the bash shell"""
        return RunBashShell(
            shell=self.shell,
            cmd=self.name
        )

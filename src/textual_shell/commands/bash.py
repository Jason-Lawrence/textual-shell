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

from ..command import Command, CommandNode
from ..job import Job

class BashTextArea(TextArea):
    """"""
    
    class Execute(Message):
        """"""
        def __init__(self, text) -> None:
            super().__init__()
            self.text = text
        
    
    BINDINGS = [
        Binding('enter', 'enter_pressed', 'execute command', priority=True),
        Binding('ctrl+c', 'clear', 'Interrupt the current command line.'),
        Binding('up', 'up_history', 'Cycle up through the history.', show=False),
        Binding('down', 'down_history', 'Cycle down through the history', show=False),
    ]
    
    language='bash'
    history_list: reactive[deque[str]] = reactive(deque)
    current_history_index = None
    prompt = reactive(str)
    multiline = False

    def on_mount(self):
        self.action_cursor_line_end()

    def watch_prompt(self, prompt) -> None:
        """"""
        self.clear()
        self.insert(self.prompt)
    
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
        
    def _on_key(self, event: events.Key) -> None:
        if event.character == '\x7f' or event.key == 'left':
            if (self.cursor_location[1] == 2 or 
                self.cursor_location[1] == len(self.prompt)):
                    event.prevent_default()
                    event.stop()


class BashShell(Screen):
    """"""
    
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
    
    def __init__(self, task: asyncio.Task, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.shell_task = task
        self.run_worker(self.setup())
        
    def compose(self) -> ComposeResult:
        yield RichLog(markup=True)
        yield BashTextArea()
    
    def on_mount(self) -> None:
        self.user = os.environ.get('USER', 'user')
        self.current_dir = os.getcwd()
        self.create_prompt()
        
        text_area = self.query_one(BashTextArea)
        text_area.focus()
        
    def create_prompt(self) -> None:
        # user_sec = f'[bright_green]{self.user}[/bright_green]'
        # c_dir_sec = f'[dodger_blue2]{self.current_dir}[/dodger_blue2]'
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
        """"""
        log('Setting up shell')
        
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
        
        log('Finished setting up the shell.')
        
    async def on_bash_text_area_execute(
        self,
        event: BashTextArea.Execute
    ) -> None:
        """"""
        rich_log = self.query_one(RichLog)
        text_area = self.query_one(BashTextArea)
        
        text = event.text.replace('\\\n> ', '').strip()
            
        if text != '':
            text_area.history_list.appendleft(text)
            
        if text == 'clear':
            rich_log.clear()
            return
        
        self.BASH_SHELL.stdin.write(text.encode() + b'\n')
        await self.BASH_SHELL.stdin.drain()
          
        rich_log.write(self.prompt + event.text)

    async def update_from_stdout(self, output) -> None:
        """Take stdout and write it to the RichLog."""
        rich_log = self.query_one(RichLog)
        rich_log.write(output)
        
    async def update_from_stderr(self, error) -> None:
        """Take from stderr and write it to the RichLog."""
        rich_log = self.query_one(RichLog)
        rich_log.write(error)
        
    async def read_stdout(self):
        try:
            async for line in self.BASH_SHELL.stdout:
                decoded = line.decode().strip()
                await self.update_from_stdout(decoded)
        
        except asyncio.CancelledError:
            return
            
    async def read_stderr(self):
        try:
            async for line in self.BASH_SHELL.stderr:
                decoded = line.decode().strip()
                await self.update_from_stderr(decoded)

        except asyncio.CancelledError:
            return
        
    def watch_user(self) -> None:
        self.create_prompt()
        
    def watch_current_dir(self) -> None:
        self.create_prompt()
        
    def watch_prompt(self) -> None:
        """Whenever the prompt changes update the text area."""
        textarea = self.query_one(BashTextArea)
        textarea.prompt = self.prompt
        

class RunBashShell(Job):
    
    async def execute(self):
        self.running()
        log(f'Executing: {self.id}')
        self.screen = BashShell(self.task)
        self.shell.app.install_screen(self.screen, name=self.id)
        self.shell.app.push_screen(self.screen)
        
        await self.wait_for_cancel()
        
        self.shell.app.uninstall_screen(self.screen)
        self.completed()


class Bash(Command):
    
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

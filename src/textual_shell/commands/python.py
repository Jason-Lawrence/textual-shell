import asyncio
import os
from typing import Annotated

from textual import log
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import RichLog


from ..command import Command, CommandNode
from ..job import Job
from ..widgets import ShellArea


class PythonArea(ShellArea):
    pass


class PythonInterpreter(Screen):
    """
    Screen to render an interactive python interpreter.

    Args:
        task (asyncio.Task): The asyncio task of the job.
    """

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

    def __init__(
        self,
        task: Annotated[asyncio.Task, 'The asyncio task of the job the shell is running in.'],
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.interpreter_task = task
        self.run_worker(self.setup())

    def compose(self) -> ComposeResult:
        yield RichLog(markup=True, wrap=True)
        yield PythonArea()

    def on_mount(self) -> None:
        text_area = self.query_one(PythonArea)
        text_area.focus()

    def action_background_job(self) -> None:
        """Background the bash shell and 
        return to the main screen."""
        self.app.pop_screen()
    
    def action_kill_shell(self) -> None:
        """Kill the bash shell job and 
        return to the main screen"""
        for task in self.tasks:
            task.cancel()
        
        self.interpreter_task.cancel()
        self.app.pop_screen()

    async def setup(self):
        """Spawn the child process to run the bash shell.
        Also create the tasks for reading stdout and stderr."""
        self.PYTHON_INTERPRETER = await asyncio.create_subprocess_exec(
            'python',
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

    async def on_shell_area_execute(
        self,
        event: ShellArea.Execute
    ) -> None:
        pass

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
        

class RunPythonInterpreter(Job):
    """"""

    async def execute(self):
        self.running()

        self.screen = PythonInterpreter(self.task)
        self.shell.app.install_screen(self.screen, name=self.id)
        self.shell.app.push_screen(self.screen)
        
        await self.wait_for_cancel()
        
        self.shell.app.uninstall_screen(self.screen)
        self.completed()


class Python(Command):
    """"""
    DEFINITION = {
        'python': CommandNode(
            name='python',
            description='Spawn a Python Interpreter'
        )
    }

    def create_job(self, *args):
        """"""
        return RunPythonInterpreter(
            shell=self.shell,
            cmd=self.name
        )
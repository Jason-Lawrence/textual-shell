import asyncio
import random
import string
from abc import ABC, abstractmethod
from enum import Enum
from typing import Annotated

from textual.message import Message
from textual.screen import Screen


class Job(ABC):
    
    class Status(Enum):
        """Enumeration of the Statuses."""
        PENDING = 0
        RUNNING = 1
        CANCELLED = 2
        COMPLETED = 3
        ERROR = 4
        
    class Start(Message):
        """Default message to notify the app that a command has started."""
        def __init__(
            self,
            job: Annotated['Job', 'The job created by the command.']
        ) -> None:
            super().__init__()
            self.job = job
    
    class Finish(Message):
        """Default message to notify the app that the command has finished."""
        def __init__(
            self,
            job_id: Annotated[str, 'The id of the job.']
        ) -> None:
            super().__init__()
            self.job_id = job_id
    
    class PushScreen(Message):
        """
        Default Message for pushing a new screen onto the app.
        
        Args:
            screen (Screen): The output screen for the command.
        """
        def __init__(self, screen) -> None:
            super().__init__()
            self.screen = screen
            
    
    class Log(Message):
        """
        Default Logging event for commands.
        
        Args:
            command (str): The name of the command sending the log.
            msg (str): The log message.
            severity (int): The level of the severity.
            
        """
        def __init__(
            self,
            command: Annotated[str, 'The name of the command sending the log.'],
            msg: Annotated[str, 'The log message.'],
            severity: Annotated[int, 'The level of the severity']
        ) -> None:
            super().__init__()
            self.command = command
            self.msg = msg
            self.severity = severity


    def __init__(
        self,
        cmd: Annotated[str, 'The name of the command'],
        shell
    ) -> None:
        self.id = f'{cmd}_{self._generate_id()}'
        self.status = self.Status.PENDING
        self.shell = shell
        self.cmd = cmd
        
    def _generate_id(self):
        """Generate a random 6 digit string."""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_log(
        self,
        msg: Annotated[str, 'log message'],
        severity: Annotated[str, 'The level of severity']
    ) -> None:
        """
        Send logs to the app.
        
        Args:
            msg (str): The log message.
            severity (str): The severity level of the log.
        """
        self.shell.post_message(self.Log(self.cmd, msg, severity))
                
    def send_screen(
        self,
        screen: Annotated[Screen, 'The output screen'],
    ) -> None:
        """Send an output screen"""
        self.shell.post_message(self.PushScreen(screen))
    
    async def start(self):
        """"""
        self.shell.post_message(self.Start(self))
        self.task = asyncio.create_task(
            self.execute(),
            name=self.id
        )
        self.task.add_done_callback(self.finish)
        
    def finish(self, task: asyncio.Task):
        self.shell.post_message(self.Finish(self.id))
        
    @abstractmethod
    async def execute(self):
        pass
        

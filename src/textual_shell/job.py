import asyncio
import random
import string
from abc import ABC, abstractmethod
from enum import Enum
from typing import Annotated

from textual.message import Message
from textual.screen import Screen


class Job(ABC):
    """
    Base Job class. Each command should have a corresponding Job it creates.
    
    Args:
        cmd (str): The name of the command that created the job.
        shell (textual_shell.widgets.baseshell): The shell widget for posting messages.
    """
    
    class Status(Enum):
        """Enumeration of the Statuses."""
        PENDING = 0
        RUNNING = 1
        CANCELLED = 2
        COMPLETED = 3
        ERROR = 4


    class StatusChange(Message):
        """
        Message to notify a change in status for a job.
        
        Args:
            job_id (str): The job's identifier.
            status (Job.Status): The new status.
        """
        def __init__(
            self,
            job_id: Annotated[str, 'The jobs identifier.'],
            status: Annotated['Job.Status', 'The new status.']
        ) -> None:
            super().__init__()
            self.job_id = job_id
            self.status = status

        
    class Start(Message):
        """
        Message to notify the app that a command has started.
        
        Args:
            job (Job): The job that has been created and started.
        """
        def __init__(
            self,
            job: Annotated['Job', 'The job created by the command.']
        ) -> None:
            super().__init__()
            self.job = job
    

    class Finish(Message):
        """
        Message to notify the app that the command has finished.
        
        Args:
            job_id (str): The id of the job.
        """
        def __init__(
            self,
            job_id: Annotated[str, 'The id of the job.']
        ) -> None:
            super().__init__()
            self.job_id = job_id


    class PushScreen(Message):
        """
        Message for pushing a new screen onto the app.
        
        Args:
            screen (Screen): The output screen for the command.
        """
        def __init__(self, screen) -> None:
            super().__init__()
            self.screen = screen
            
    
    class Log(Message):
        """
        Logging event for jobs.
        
        Args:
            sender (str): The id of the Job.
            msg (str): The log message.
            severity (int): The level of the severity.
            
        """
        def __init__(
            self,
            sender: Annotated[str, 'The id of the Job.'],
            msg: Annotated[str, 'The log message.'],
            severity: Annotated[int, 'The level of the severity']
        ) -> None:
            super().__init__()
            self.sender = sender
            self.msg = msg
            self.severity = severity


    def __init__(
        self,
        cmd: Annotated[str, 'The name of the command'],
        shell,
        screen: Screen=None
    ) -> None:
        self.id = f'{cmd}_{self._generate_id()}'
        self.status = self.Status.PENDING
        self.shell = shell
        self.cmd = cmd
        self.screen = screen
        
    def _generate_id(self):
        """
        Generate a random 6 digit string.
        
        Returns:
            id (str): The id for the job.
        """
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
        """Create a asyncio task for the job and 
        schedule it for execution."""
        self.shell.post_message(self.Start(self))
        self.task = asyncio.create_task(
            self.execute(),
            name=self.id
        )
        self.task.add_done_callback(self.finish)
        
    def finish(self, task: asyncio.Task):
        """Send a finish message to clean up the job."""
        self.shell.post_message(self.Finish(self.id))
        
    @abstractmethod
    async def execute(self):
        """Execute the async task for the job.
        Subclasses must implement this."""
        pass

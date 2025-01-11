import logging
from typing import Annotated

from textual.message import Message

from ..command import Command, CommandNode
from ..job import Job


class Attach(Job):
    """Job to attach to the screen of the selected job."""
    
    class To_Job(Message):
        """Message to attach to the job."""
        def __init__(self, job_id):
            super().__init__()
            self.job_id = job_id
    
    def __init__(
        self,
        selected_job: Annotated[str, 'The id of the selected job.'],
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.selected_job = selected_job
        
    async def execute(self):
        """Send request to attach to the selected job."""
        self.running()
        self.shell.post_message(
            self.To_Job(
                self.selected_job
            )
        )
        self.completed()
        
        
class Kill(Job):
    """Job to kill another job."""
    
    class Selected(Message):
        """Message to kill the selected job."""
        def __init__(self, job_id):
            super().__init__()
            self.job_id = job_id
    
    def __init__(
        self,
        selected_job: Annotated[str, 'The id of the selected job.'],
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.selected_job = selected_job
        
    async def execute(self):
        """Send the request to kill the selected job."""
        self.running()
        self.shell.post_message(
            self.Selected(
                self.selected_job
            )
        )
        self.completed()


class Jobs(Command):
    """Command for interacting with the jobs running in the shell."""
    
    DEFINITION = {
        'jobs': CommandNode(
            name='jobs',
            description='Manage jobs.',
            children={
                'attach': CommandNode(
                    name='attach',
                    description="Attach to the job's screen."
                ),
                'kill': CommandNode(
                    name='kill',
                    description='Kill the job.'
                )
            }
        )
    }
    
    JOBS = []
        
    def get_suggestions(
        self,
        cmdline: Annotated[list[str], 'The current value of the command line.']
    ) -> Annotated[list[str], 'A list of possible next values']:
        """
        Get a list of suggestions for autocomplete via the current args neighbors.
        
        Args:
            cmdline (list[str]): The current value of the  command line.
            
        Returns:
            suggestions (List[str]): List of current node's neighbors names.
        """
        if len(cmdline) == 2:
            if cmdline[1] == 'kill' or cmdline[1] == 'attach':
                return self.JOBS
        
        else:
            return super().get_suggestions(cmdline)

    def add_job_id(self, job_id: str) -> None:
        """
        Add the job id to use for suggestions.
        
        Args:
            job_id (str): Tht job to remove.
        """
        self.JOBS.append(job_id)
    
    def remove_job_id(self, job_id: str) -> None:
        """
        Remove the job id from the suggestions.
        
        Args:
            job_id (str): Tht job to remove.
        """
        self.JOBS.remove(job_id)
        
    def create_job(self, *args) -> Attach | Kill:
        """Create the job to manage other jobs."""
        if len(args) != 2:
            self.send_log('Invalid args', logging.ERROR)
            return
        
        if args[0] == 'attach':
            return Attach(
                selected_job=args[1],
                shell=self.shell,
                cmd=self.name
            )
            
        elif args[0] == 'kill':
            return Kill(
                selected_job=args[1],
                shell=self.shell,
                cmd=self.name
            )
        
        else:
            self.shell.notify(
                message='Invalid subcommand.',
                title='Command: jobs',
                severity='error'
            )
    
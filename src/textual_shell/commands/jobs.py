import logging
from typing import Annotated

from textual.message import Message

from ..command import Command, CommandArgument
from ..job import Job


class JobsJob(Job):
    
    class Attach(Message):
        """Message to attach to a jobs screen"""
        def __init__(self, job_id):
            super().__init__()
            self.job_id = job_id
            
    class Kill(Message):
        """Message to kill a job."""
        def __init__(self, job_id):
            super().__init__()
            self.job_id = job_id
    
    def __init__(
        self,
        selected_job: Annotated[str, 'The id of the selected job.'],
        sub_command: Annotated[str, 'Whether to attach or kill the selected job.'],
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.selected_job = selected_job
        self.sub_command = sub_command
        
    async def execute(self):
        """"""
        self.shell.post_message(
            self.StatusChange(
                self.id,
                self.Status.RUNNING
            )
        )
        if self.sub_command == 'attach':
            self.shell.post_message(
                self.Attach(self.selected_job)
            )
        
        else:
            self.shell.post_message(
                self.Kill(self.selected_job)
            )
        self.shell.post_message(
            self.StatusChange(
                self.id,
                self.Status.COMPLETED
            )
        )


class Jobs(Command):
    """"""
    
    def __init__(self) -> None:
        super().__init__()
        root = CommandArgument('jobs', 'Manage jobs.')
        root_index = self.add_argument_to_cmd_struct(root)
        
        attach = CommandArgument('attach', "Attach to the job's screen.")
        at_index = self.add_argument_to_cmd_struct(attach, parent=root_index)

        kill = CommandArgument('kill', 'Kill the job.')
        k_index = self.add_argument_to_cmd_struct(kill, parent=root_index)
        
        self.jobs = []
        
    def get_suggestions(
        self,
        current_arg: str
    ) -> Annotated[list[str], 'A list of possible next values']:
        """
        Get a list of suggestions for autocomplete via the current args neighbors.
        
        Args:
            current_arg (str): The current arg in the command line.
            
        Returns:
            suggestions (List[str]): List of current node's neighbors names.
        """
        if current_arg == 'kill' or current_arg == 'attach':
            return self.jobs
        
        else:
            return super().get_suggestions(current_arg)

    def add_job_id(self, job_id: str) -> None:
        """
        Add the job id to use for suggestions.
        
        Args:
            job_id (str): Tht job to remove.
        """
        self.jobs.append(job_id)
    
    def remove_job_id(self, job_id: str) -> None:
        """
        Remove the job id from the suggestions.
        
        Args:
            job_id (str): Tht job to remove.
        """
        self.jobs.remove(job_id)
        
    def create_job(self, *args) -> JobsJob:
        """Create the job to manage other jobs."""
        if len(args) != 2:
            self.send_log('Invalid args', logging.ERROR)
        
        if args[0] == 'attach':
            return JobsJob(
                selected_job=args[1],
                sub_command='attach',
                shell=self.widget,
                cmd=self.name
            )
            
        elif args[0] == 'kill':
            return JobsJob(
                selected_job=args[1],
                sub_command='kill',
                shell=self.widget,
                cmd=self.name
            )
        
        else:
            self.widget.notify(
                message='Invalid subcommand.',
                title='Command: jobs',
                severity='error'
            )
    
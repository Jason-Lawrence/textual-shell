from typing import Annotated

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    DataTable,
    Label
)

from ..job import Job


class JobManager(Widget):
    """Manage currently running jobs."""
    
    DEFAULT_CSS = """
    
    """
    
    job_list: dict[str, Job] = {}
    
    def compose(self) -> ComposeResult:
        yield Label('Jobs')
        yield DataTable()
        
    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        self.column_keys = table.add_columns('Jobs', 'Status')
        
    def add_job(
        self,
        job: Annotated[Job, 'The job to add.']
    ) -> None:
        """
        Add a new job to the table and dictionary.
        
        Args:
            job (Job): The job to add.
        """
        self.job_list[job.id] = job
        table = self.query_one(DataTable)
        row = (job.id, job.status)
        table.add_row(*row, key=job.id)
        
    def remove_job(
        self,
        job_id: Annotated[str, 'The id of the job.']
    ) -> None:
        """
        Remove a job from the table and dictionary.
        
        Args:
            job_id (str): The id of the job.
        """
        job = self.job_list.pop(job_id)
        table = self.query_one(DataTable)
        table.remove_row(job_id)
        
    def update_job_status(
        self,
        job_id: Annotated[str, 'The id of the job'],
        status: Job.Status
    ) -> None:
        """
        Update the status of the job in the table.
        
        Args:
            job_id (str): The id of the job.
            status (Job.Status): The jobs current status.
        """
        table = self.query_one(DataTable)
        table.update_cell(
            row_key=job_id,
            column_key=self.column_keys[1],
            value=status
        )
        
    def switch_job_screen(
        self,
        job_id: Annotated[str, 'The id of the job']
    ) -> None:
        """
        Switch to the specified jobs screen if it exists.
        
        Args:
            job_id (str): The id of the job.
        """
        try:
            job = self.job_list[job_id]
            if job.screen:
                self.app.push_screen(job.screen)
        
        except KeyError as e:
            pass
        
    def kill_job(
        self,
        job_id: Annotated[str, 'The id of the job'],
    ) -> None:
        """
        Cancel the job.
        
        Args:
            job_id (str): The id of the job.
        """
        try:
            job = self.job_list[job_id]
            job.task.cancel()
        
        except KeyError as e:
            pass

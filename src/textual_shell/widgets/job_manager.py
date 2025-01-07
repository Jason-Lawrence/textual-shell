from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import (
    DataTable,
    Label
)

from ..job import Job


class JobManager(Widget):
    """"""
    
    DEFAULT_CSS = """
    
    """
    
    job_list: dict[str, Job] = {}
    
    def compose(self) -> ComposeResult:
        yield Label('Jobs')
        yield DataTable()
        
    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        self.column_keys = table.add_columns('Jobs', 'Status')
        
    def add_job(self, job: Job) -> None:
        """"""
        self.job_list[job.id] = job
        table = self.query_one(DataTable)
        row = (job.id, job.status)
        table.add_row(*row, key=job.id)
        
    def remove_job(self, job_id: str) -> None:
        job = self.job_list.pop(job_id)
        table = self.query_one(DataTable)
        table.remove_row(job_id)
        
        
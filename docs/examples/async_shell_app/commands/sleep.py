import asyncio

from textual_shell.commands import Command, CommandArgument
from textual_shell.job import Job

class SleepJob(Job):
    
    def __init__(self, seconds: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.seconds = int(seconds)
    
    async def execute(self):
        self.shell.post_message(
            self.StatusChange(
                self.id,
                self.Status.RUNNING
            )
        )
        await asyncio.sleep(self.seconds)
        self.shell.post_message(
            self.StatusChange(
                self.id,
                self.Status.COMPLETED
            )
        )

class Sleep(Command):
    
    def __init__(self) -> None:
        super().__init__()
        arg = CommandArgument('sleep', 'Sleep for x seconds')
        self.add_argument_to_cmd_struct(arg)
        
    def create_job(self, *args) -> SleepJob:
        return SleepJob(
            shell=self.widget,
            cmd=self.name,
            seconds=args[0]
        )

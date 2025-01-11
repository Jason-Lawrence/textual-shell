import asyncio

from textual_shell.command import Command, CommandNode
from textual_shell.job import Job

class SleepJob(Job):
    
    def __init__(self, seconds: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.seconds = int(seconds)
    
    async def execute(self):
        self.running()
        await asyncio.sleep(self.seconds)
        self.completed()

class Sleep(Command):
    
    DEFINITION = {
        'sleep': CommandNode(
            name='sleep',
            description='Sleep for x seconds.'
        ) 
    }
        
    def create_job(self, *args) -> SleepJob:
        return SleepJob(
            shell=self.shell,
            cmd=self.name,
            seconds=args[0]
        )

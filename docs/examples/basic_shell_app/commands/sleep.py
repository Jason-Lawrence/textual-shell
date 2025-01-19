import asyncio
import logging

from textual_shell.command import Command, CommandNode
from textual_shell.job import Job

class SleepJob(Job):
    """
    A job that will sleep for x seconds.
    
    Args:
        seconds (str): The amount of seconds to sleep for.
    """
    def __init__(self, seconds: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.seconds = int(seconds)
    
    async def execute(self):
        self.running()
        self.send_log(
            msg=f'{self.id} - Sleeping for {self.seconds} seconds.',
            severity=logging.INFO
        )
        await asyncio.sleep(self.seconds)
        self.send_log(
            msg=f'{self.id} - Slept for {self.seconds} seconds.',
            severity=logging.INFO
        )
        self.completed()

class Sleep(Command):
    """
    Command to sleep for x seconds.
    
    Examples:
        sleep 10
    """
    DEFINITION = {
        'sleep': CommandNode(
            name='sleep',
            description='Sleep for x seconds.'
        ) 
    }
        
    def create_job(self, *args) -> SleepJob:
        """
        Create a SleepJob to execute the asyncio.sleep()
        
        Returns:
            job (SleepSeconds): A job that will sleep for x seconds.
        """
        if len(args) != 1:
            self.shell.notify(
                message='Invalid Arguments',
                title='Command: sleep',
                severity='error'
            )
            return

        elif not args[0].isdigit():
            self.shell.notify(
                message='Argument should be a number',
                title='Command: sleep',
                severity='error'
            )
            return
        
        return SleepJob(
            shell=self.shell,
            cmd=self.name,
            seconds=args[0]
        )

import logging
from typing import Annotated

from textual.message import Message

from ..command import Command, CommandNode
from ..job import Job


class History(Job):
    """Job to clear the history."""
    
    class Clear(Message):
        """Signal the app to clear the history."""
        pass
    
    async def execute(self):
        self.running()
        self.shell.post_message(
            self.Clear()
        )
        self.completed()


class Console(Job):
    """Job to clear the console."""
    
    class Clear(Message):
        """Signal the app to clear the console."""
        pass
    
    async def execute(self):
        self.running()
        self.shell.post_message(
            self.Clear()
        )
        self.completed()
        

class Clear(Command):
    """
    Command for clearing either the history log or 
    console log.
    """
    
    DEFINITION = {
        'clear': CommandNode(
            name='clear',
            description='Clear either the ConsoleLog or the HistoryLog.',
            children={
                'console': CommandNode(
                    name='console',
                    description='Clear the ConsoleLog',
                ),
                'history': CommandNode(
                    name='history',
                    description='Clear the HistoryLog.'
                )
            }
        )
    }
    
    def create_job(self, *args) -> Console | History:
        """Create the job to clear either the console or history."""
        if len(args) != 1:
            self.send_log('Invalid args!', logging.ERROR)
            return
            
        elif args[0] == 'console':
            return Console(
                shell=self.shell,
                cmd=self.name
            )
        
        elif args[0] == 'history':
            return History(
                shell=self.shell,
                cmd=self.name
            )
        
        else:
            self.shell.notify(
                message='Invalid subcommand.',
                title='Command: clear',
                severity='error'
            )

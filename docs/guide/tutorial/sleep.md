# Sleep Tutorial
The sleep command will have one argument which will be how long to sleep for.

``` py title='sleep.py'
import asyncio
import logging

from textual_shell.command import Command, CommandNode
from textual_shell.job import Job


class Sleep(Command):
    """Command to sleep for x seconds."""

    DEFINITION = {
        'sleep': CommandNode(
            name='sleep',
            description='Sleep for x seconds'
        )
    }
```

First things first, import the [Command](../../reference/command.md#src.textual_shell.command.Command), [CommandNode](../../reference/command.md#src.textual_shell.command.CommandNode), and [Job](../../reference/job.md#src.textual_shell.job.Job) from their respective modules. Then define a new Sleep class that extends the Command base class. Afterwards, write the DEFINITION for the command. The DEFINITION is a dictionary where the keys are the name of the nodes and the values are CommandNodes. 

``` py title='sleep.py'
import asyncio
import logging

from textual_shell.command import Command, CommandNode
from textual_shell.job import Job


class SleepSeconds(Job):
    pass


class Sleep(Command):
    """
    Command to sleep for x seconds.
    
    Examples:
        sleep 10
    """

    DEFINITION = {
        'sleep': CommandNode(
            name='sleep',
            description='Sleep for x seconds'
        )
    }

    def create_job(self, *args) -> SleepSeconds:
        """
        Create a SleepJob to execute the asyncio.sleep()
        
        Returns:
            job (SleepSeconds): A job that will sleep for x seconds.
        """
        # Simple cmdline validation.
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

        return SleepSeconds(
            shell=self.shell,
            cmd=self.name,
            seconds=args[0]
        )
```

Next lets define the SleepSeconds class that extends the Job base class. This will be the object that is created by the Sleep command and will contain the asyncio.Task object. Lets also implement some commandline validation. The command only takes a single argument and that argument should be a number. If those conditions are not met then send an error notification and return. Note the passing of the self.shell and self.name as parameters to the SleepSeconds Job. The self.shell is required so the job can send messages to the app. 

``` py title='sleep.py'
import asyncio
import logging

from textual_shell.command import Command, CommandNode
from textual_shell.job import Job


class SleepSeconds(Job):
    """
    A job that will sleep for x seconds.
    
    Args:
        seconds (str): The amount of seconds to sleep for.
    """
    def __init__(self, seconds: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs) # IMPORTANT: Make sure to call the super.
        self.seconds = int(seconds)
    
    async def execute(self):
        """Use asyncio.sleep to sleep in the background."""
        self.running() # set the status to running
        self.send_log(
            msg=f'{self.id} - Sleeping for {self.seconds} seconds.',
            severity=logging.INFO
        )
        await asyncio.sleep(self.seconds)
        self.send_log(
            msg=f'{self.id} - Slept for {self.seconds} seconds.',
            severity=logging.INFO
        )
        self.completed() # set the status to completed.


class Sleep(Command):
    """
    Command to sleep for x seconds.
    
    Examples:
        sleep 10
    """

    DEFINITION = {
        'sleep': CommandNode(
            name='sleep',
            description='Sleep for x seconds'
        )
    }

    def create_job(self, *args) -> SleepSeconds:
        """
        Create a SleepJob to execute the asyncio.sleep()
        
        Returns:
            job (SleepSeconds): A job that will sleep for x seconds.
        """
        # Simple cmdline validation.
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

        return SleepSeconds(
            shell=self.shell,
            cmd=self.name,
            seconds=args[0]
        )
```
Finally, Add the execution logic to the SleepSeconds Job. The execute method on the Job should be an async function. In this case, all thats done, is first set the job's status to be running. Then, use the send_log method to send a record to the app so, it can be written to the [ConsoleLog](../../widgets/console_log.md). We then await asyncio.sleep(). Its important to use asyncio instead of the time module since time.sleep will block all execution... Finally, send another log to show how long the job slept and set the status to completed.

## Wrap Up
That concludes the implementation of a basic sleep command. The create_job method should return a job or None if the job creation failed. The [timer](timer.md) tutorial is a little more advanced as we will look at screen management within a job.  
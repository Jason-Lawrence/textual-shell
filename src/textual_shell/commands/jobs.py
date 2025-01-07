import logging
from textual.message import Message

from .command import Command, CommandArgument


class Jobs(Command):
    """"""
    
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
    
    def __init__(self) -> None:
        super().__init__()
        root = CommandArgument('jobs', 'Manage jobs.')
        root_index = self.add_argument_to_cmd_struct(root)
        
        attach = CommandArgument('attach', "Attach to the job's screen.")
        at_index = self.add_argument_to_cmd_struct(attach, parent=root_index)

        kill = CommandArgument('kill', 'Kill the job.')
        k_index = self.add_argument_to_cmd_struct(kill, parent=root_index)
        
    
    def execute(self, *args):
        """"""
        if len(args) != 2:
            self.send_log('Invalid args', logging.ERROR)
        
        if args[0] == 'attach':
            job_id = args[1]
            self.widget.post_message(self.Attach(job_id))
            
        elif args[0] == 'kill':
            job_id = args[1]
            self.widget.post_message(self.Kill(job_id))
        
        else:
            self.widget.notify(
                message='Invalid subcommand.',
                title='Command: jobs',
                severity='error'
            )
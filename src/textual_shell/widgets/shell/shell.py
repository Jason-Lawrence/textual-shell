from textual import work

from .base_shell import BaseShell
from ...job import Job


class Shell(BaseShell):
    """
    Main shell widget. When a command is executed it will use 
    the command instance to create a job specific to the command
    and schedule it for execution.
    
    Pressing the up arrow key will cycle up through the history.
    Pressing the down arrow key will cycle down through the history,
    Pressing ctrl+c will clear the prompt input.
    
    Args:
        commands (List[Command]): List of shell commands.
        prompt (str): prompt for the shell.
        history_log (str): The path for the history log file. 
    
    """
    
    DEFAULT_CSS = """
        Shell Container {
            border: round white;
            height: auto;
        }
        
        Shell RichLog {
            height: auto;
            max-height: 10;
            padding: 0 1;
            background: transparent;
            border: hidden;
        }
        
        Prompt {
            margin: 0;
            padding-top: 0;
            height: 1;
            layout: horizontal;
        
            Label {
                padding: 0;
                padding-left: 1;
            }
            
            PromptInput {
                border: hidden;
                background: transparent;
                margin-left: 0;
                padding-left: 0;
            }
            
            PromptInput:focus {
                border: none;
                padding: 0;
            }
        }
        
        Suggestions {
            layer: popup;
            height: auto;
            width: 20;
            border: round white;
            padding: 0;
        }
        
        Suggestions:focus {
            border: round white;
            padding: 0;
        }
    """
    
    def command_entered(self, cmdline):
        """"""
        cmdline = cmdline.strip(' ')
        if len(cmdline) == 0:
            return
        
        cmd_args = cmdline.split(' ')
        cmd_name = cmd_args.pop(0)
            
        if cmd := self.get_cmd_obj(cmd_name):
            
            if cmd.name == 'help':
                if len(cmd_args) == 0:
                    return
                
                if show_help := self.get_cmd_obj(cmd_args[0]):
                    job = cmd.create_job(show_help)
                    self.start_job(job)
                    
                else:
                    self.notify(
                        f'[b]Command:[/b] {cmd_name} does not exist!',
                        severity='error',
                        title='Invalid Command',
                        timeout=5
                    )
                    
            else:
                job = cmd.create_job(*cmd_args)
                if job is None:
                    self.notify(
                        f'[b]Command:[/b] {cmd_name} failed to create job',
                        severity='error',
                        title='Job Failed'
                    )
                    return
                
                self.start_job(job)
        
        else:
            self.notify(
                f'[b]Command:[/b] {cmd_name} does not exist!',
                severity='error',
                title='Invalid Command',
                timeout=5
            )
            return
        
        self.history_list.appendleft(cmdline)
        self.history_count += 1
        self.mutate_reactive(Shell.history_list)
        self.current_history_index = None

    @work()
    async def start_job(self, job: Job):
        await job.start()

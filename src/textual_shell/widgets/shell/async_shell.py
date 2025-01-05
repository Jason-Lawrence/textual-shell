from textual import work

from .base_shell import BaseShell
from ...commands import Command


class AsyncShell(BaseShell):
    """
    Asynchronous shell widget where commands are executed in child threads.    
    """
    
    DEFAULT_CSS = """
        AsyncShell Container {
            border: round white;
            height: auto;
        }
        
        AsyncShell RichLog {
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
                    cmd.execute(show_help)
                    
                else:
                    self.notify(
                        f'[b]Command:[/b] {cmd_name} does not exist!',
                        severity='error',
                        title='Invalid Command',
                        timeout=5
                    )
                    
            else:
                self.execute_command(cmd, *cmd_args)
        
        else:
            self.notify(
                f'[b]Command:[/b] {cmd_name} does not exist!',
                severity='error',
                title='Invalid Command',
                timeout=5
            )
            return
        
        self.history_list.appendleft(cmdline)
        self.mutate_reactive(AsyncShell.history_list)
        self.current_history_index = None
    
    @work(thread=True)   
    def execute_command(self, cmd: Command, *cmd_line):
        """
        Execute the command in a worker Thread.
        
        Args:
            cmd (Command): The command to be executed.
            cmd_line (*args): a list of positional arguments for the command.
        """
        cmd.execute(*cmd_line)
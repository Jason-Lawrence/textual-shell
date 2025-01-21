import os

from textual.app import ComposeResult
from textual.containers import Grid, Container
from textual.widgets import Header, Footer

from textual_shell.app import BaseShellApp
from textual_shell.commands import Bash, Clear, Help, Jobs, Python, Set
from textual_shell.widgets import (
    Shell,
    CommandList,
    ConsoleLog,
    JobManager,
    SettingsDisplay,
)

from commands import Sleep, Timer


class BasicShell(BaseShellApp):
    
    CSS = """
        #app-grid {
            grid-size: 3;
            grid-rows: 1fr;
            grid-columns: 20 2fr 1fr;
            width: 1fr;
        }
    """
    
    theme = 'tokyo-night'

    CONFIG_PATH = os.path.join(os.getcwd(), '.config.yaml')
    
    cmd_list = [
        Bash(), Clear(), Help(), Set(CONFIG_PATH), 
        Jobs(), Python(), Timer(), Sleep()
    ]
    
    command_names = [cmd.name for cmd in cmd_list]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Grid(
            CommandList(self.command_names),
            Shell(
                self.cmd_list,
                prompt='prompt <$ '
            ),
            SettingsDisplay(self.CONFIG_PATH),
            Container(),
            ConsoleLog(self.CONFIG_PATH),
            JobManager(),
            id='app-grid'
        )
        
        
if __name__ == '__main__':
    BasicShell().run()

import os

from textual.app import ComposeResult
from textual.containers import Grid
from textual.geometry import Offset
from textual.widgets import Header, Footer

from textual_shell.app import ShellApp
from textual_shell.command import Help, Set
from textual_shell.widgets import CommandList, Shell, SettingsDisplay

class BasicShell(ShellApp):
    
    CSS_PATH = 'style.css'
    theme = 'tokyo-night'
        
    cmd_list = [Help(), Set()]
    command_names = [cmd.name for cmd in cmd_list]
    CONFIG_PATH = os.path.join(os.environ.get('HOME', os.getcwd()), '.config.yaml')
    HISTORY_LOG = os.path.join(os.environ.get('HOME', os.getcwd()), '.shell_history.log')
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Grid(
            CommandList(self.command_names),
            Shell(
                self.cmd_list,
                prompt='xbsr <$ ',
                suggestion_offset=Offset(10, 5)
            ),
            SettingsDisplay(self.CONFIG_PATH),
            id='app-grid'
        )
        
        
if __name__ == '__main__':
    BasicShell().run()

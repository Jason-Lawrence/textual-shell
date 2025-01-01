# Textual-Shell

Welcome to the Textual-Shell documentation! This is an addon for the Textual framework.

### What is Textual-Shell?

It is a collection of widgets that can be used to build a custom shell application. It draws inspiration from the cmd2 and prompt-toolkit libraries. 

## Quick Start

Install it with:
``` 
pip install textual-shell
```

```py title='Basic Shell'
import os

from textual.app import ComposeResult
from textual.containers import Grid
from textual.widgets import Header, Footer

from textual_shell.app import ShellApp
from textual_shell.command import Help, Set
from textual_shell.widgets import (
    CommandList,
    CommandLog,
    SettingsDisplay
    Shell

class BasicShell(ShellApp):
    
    CSS = """
        Grid {
            grid-size: 3;
            grid-rows: 1fr;
            grid-columns: 20 2fr 1fr;
            width: 1fr;
        }
    """
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
                prompt='prompt <$ '
            ),
            SettingsDisplay(self.CONFIG_PATH),
            Container(),
            Container(),
            CommandLog()
        )
        
        
if __name__ == '__main__':
    BasicShell().run()

```

## TODO:

* Command line validation
* write documentation on Commands
* write documentation on shell key binds

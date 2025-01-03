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
    CONFIG_PATH = os.path.join(os.environ.get('HOME', os.getcwd()), '.config.yml')
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

Below is an example config file. The descriptions are used by the help command. 
The Set command can be used to change these values. The SettingsDisplay widget will load the settings and the corresponding values
into a DataTable widget.

```yml title=".config.yml"
Server:
    description: An example server config.
    host:
        description: IP of the server.
        value: 127.0.0.1
    port:
        description: The open port.
        value: 8000
Logging:
    description: Config for logging.
    logdir:
        description: The directory to write log files too.
        value: /var/log/app
    log_format:
        description: The Format for the log records.
        value: '\%(levelname)s\t\%(message)'

```

## TODO:

* Command line validation
* write documentation on Commands
* write documentation on shell key binds

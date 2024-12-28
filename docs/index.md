# Textual-Shell

Welcome to the Textual-Shell documentation! This is an addon for the Textual framework.

### What is Textual-Shell?

It is a collection of widgets that can be used to build a custom shell application. It draws inspiration from the cmd2 and prompt-toolkit libraries. 

## Quick Start

Install it with:
``` 
pip install textual-shell
```

```py
# app.py
from textual.app import App, ComposeResult
from textual.geometry import Offset

from textual-shell.widgets import Shell, CommandList
from textual-shell.command import Help, Set

class ShellApp(App):

    cmd_list = [Help(), Set()] # add your commands here.
    command_names = [cmd.name for cmd in cmd_list]

    def compose(self) -> ComposeResult:
        yield CommandList(self.command_names) 
        yield Shell(
            self.cmd_list,
            prompt='shell <$ ', 
            suggestion_offset=Offset(10, 3) 
        )

if __name__ == '__main__':
    ShellApp().run()
```

## TODO:

* Command line validation
* Command Result
* flesh out command messages
* build settings widget
* write documentation on Commands
* write documentation on shell key binds
* Add command history
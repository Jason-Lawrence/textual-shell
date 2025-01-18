# Bash

![BASHSHELL](../assets/bash_shell.png)

This command will spawn a bash shell in a child task. Any text or command entered into the shell is fed into that child task, and the result is read from either stdout or stderr. It is then written to the RichLog along with the prompt and the command that was entered. This should meet any basic needs but your mileage may vary. Any interactive command will not work such as Vim, vi, nano, etc.

::: src.textual_shell.commands.bash
# Python

![PYTHON_INTERPRETER](../assets/python_interpreter.png)

This command will spawn a interactive python interpreter in a child process. Any text/command that is entered is sent to the stdin of the child, and the result is read from stdout and stderr. It is then written to a RichLog. This should meet any basic needs but your mileage may vary. 

::: src.textual_shell.commands.python
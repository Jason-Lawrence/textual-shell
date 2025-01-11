# Textual Shell

Welcome to the Textual-Shell documentation! This is an addon for the Textual framework.

### What is Textual-Shell?

It is a collection of widgets that can be used to build a custom shell application. It draws inspiration from the cmd2 and prompt-toolkit libraries. 

## Quick Start

Install it with:
``` 
pip install textual-shell
```

```py title='Basic Shell'
--8<-- "docs/examples/basic_shell_app/basic_app.py"
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
        value: '\%(levelname)s\t\%(message)s'
```

### TODO

* [ ] write documentation on Commands
* [ ] write documentation on shell key binds

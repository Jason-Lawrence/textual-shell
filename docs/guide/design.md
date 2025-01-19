# Design

The shell app is a simple event loop that fits in to the overarching event loop for textual apps.

![Shell App](../assets/shell_app_design.png)

The prompt is just a simple input widget where when the enter key is pressed it will send a Message to the shell widget that will parse the command line, retrieve whichever Command instance it needs and use it to create a job. Then execute that job.
This was all built with the asyncio library so none of the commands should block the event loop allowing for multiple jobs to be executed.

## Commands
[Commands](../reference/command.md) have two main parts: The DEFINITION and the [Job](../reference/job.md) factory.

### DEFINITION
The DEFINITION is used for two things. First, it is used to automatically generate the help text for the command. Second, generating a list of suggestions for auto-completion in the prompt.

### Job Factory
A job is really an asyncio Task that executes within the existing event loop that is running the textual app.
The command is responsible for parsing the rest of the arguments to generate the Job.

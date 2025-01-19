# Timer Tutorial
This will walk through taking the timer app [tutorial](https://textual.textualize.io/tutorial/) from Textual's Documentation and turn it into a command.

Below is the code from the tutorial but with some slight changes.
``` py title='timer.py'
import asyncio
from time import monotonic

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Digits, Footer, Header

from textual_shell.command import Command, CommandNode
from textual_shell.job import Job


class TimeDisplay(Digits):
    """A widget to display elapsed time."""

    start_time = reactive(monotonic)
    time = reactive(0.0)
    total = reactive(0.0)

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        """Method to update time to current."""
        self.time = self.total + (monotonic() - self.start_time)

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")

    def start(self) -> None:
        """Method to start (or resume) time updating."""
        self.start_time = monotonic()
        self.update_timer.resume()

    def stop(self):
        """Method to stop the time display updating."""
        self.update_timer.pause()
        self.total += monotonic() - self.start_time
        self.time = self.total

    def reset(self):
        """Method to reset the time display to zero."""
        self.total = 0
        self.time = 0


class Stopwatch(HorizontalGroup):
    """A stopwatch widget."""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        time_display = self.query_one(TimeDisplay)
        if button_id == "start":
            time_display.start()
            self.add_class("started")
        elif button_id == "stop":
            time_display.stop()
            self.remove_class("started")
        elif button_id == "reset":
            time_display.reset()

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")
        yield TimeDisplay()


class TimerScreen(Screen):
    """"""
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "add_stopwatch", "Add"),
        ("r", "remove_stopwatch", "Remove"),
        ("ctrl+z", "background", "Background the timer"),
        ("ctrl+d", "kill_timer", "Kill the timer")
    ]
    
    DEFAULT_CSS = """
        Stopwatch {
            background: $boost;
            height: 5;
            margin: 1;
            min-width: 50;
            padding: 1;
            
            Button {
                width: 16;
            }
        }

        TimeDisplay {   
            text-align: center;
            color: $foreground-muted;
            height: 3;
        }

        #start {
            dock: left;
        }

        #stop {
            dock: left;
            display: none;
        }

        #reset {
            dock: right;
        }

        .started {
            background: $success-muted;
            color: $text;
        }

        .started TimeDisplay {
            color: $foreground;
        }

        .started #start {
            display: none
        }

        .started #stop {
            display: block
        }

        .started #reset {
            visibility: hidden
        }
    """
    def __init__(
        self,
        task: asyncio.Task,
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.timer_task = task
    
    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header()
        yield Footer()
        yield VerticalScroll(Stopwatch(), Stopwatch(), Stopwatch(), id="timers")

    def action_add_stopwatch(self) -> None:
        """An action to add a timer."""
        new_stopwatch = Stopwatch()
        self.query_one("#timers").mount(new_stopwatch)
        new_stopwatch.scroll_visible()

    def action_remove_stopwatch(self) -> None:
        """Called to remove a timer."""
        timers = self.query("Stopwatch")
        if timers:
            timers.last().remove()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
        
    def action_background(self) -> None:
        """An action to background the timer screen
        and return to the shell app."""
        self.app.pop_screen()

    def action_kill_timer(self) -> None:
        """An action to kill the timer and
        return to the shell app."""
        self.timer_task.cancel()
        self.app.pop_screen()

```
The first change we added is the asyncio and textual_shell import statements. Next, the StopwatchApp class was renamed to TimerScreen, and instead of extending the App class extend the Screen class from textual.screen. Also lets add two more key binds, ctrl+z for backgrounding the timer screen and ctrl+d for killing the timer. 

Then, lets override the __init__ method to also take in an asyncio.Task. That way the screen will know which Job it is related too. This will be used to implement the kill_timer action. Finally, add the action methods to handle the new key binds. They are pretty much the same except the kill action will cancel the asyncio task before it pops the timer screen.

Next lets implement the Timer Command and the TimerApp Job.
``` py title='timer.py'

class TimerApp(Job):
    """A job to run an instance of the timer app."""
    
    async def execute(self):
        self.running()
        self.screen = TimerScreen(self.task)
        self.shell.app.install_screen(self.screen, name=self.id)
        self.shell.app.push_screen(self.screen)
        
        await self.wait_for_cancel()
        
        self.shell.app.uninstall_screen(self.screen)
        self.completed()


class Timer(Command):
    """A command to create a timer."""
    
    DEFINITION = {
        'timer': CommandNode(
            name='timer',
            description='Execute the timer app.'
        )
    }
        
    def create_job(self, *args) -> TimerApp:
        """
        Create a timer instance
        
        Returns:
            job (TimerApp): A job to run an instance of the timer app.
        """
        if len(args) != 0:
            self.shell.notify(
                message='Invalid Arguments',
                title='Command: timer',
                severity='error'
            )
            return

        return TimerApp(
            shell=self.shell,
            cmd=self.name
        )
```
Lets start with the Timer command class. Its real simple since the command takes no arguments and only has a single option for which job it will create. 

The TimerApp Job just needs to implement the async execute method. In it, we create an instance of the TimerScreen and set it to self.screen. Next, install the TimerScreen on the App's screen stack. This way if the user backgrounds the timer app it won't destroy the screen. Afterwards, push the screen to the top of the stack. This will make the timer screen immediately open up upon the execution of the command. Then, await the self.wait_for_cancel method. This basically just sleeps the job until the user cancels the task via the kill action or by the jobs kill command. Once the user does cancel, it will break out of the sleep loop and uninstall the screen, destroying the instance of the timer app.
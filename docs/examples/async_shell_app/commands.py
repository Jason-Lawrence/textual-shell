from time import monotonic, sleep

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Digits, Footer, Header

from textual_shell.commands import Command, CommandArgument


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
        ("c", "close", "Close")
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
        
    def action_close(self) -> None:
        """"""
        self.app.pop_screen()


class Timer(Command):
    
    def __init__(self) -> None:
        super().__init__()
        arg = CommandArgument('timer', 'Execute the timer app.')
        self.add_argument_to_cmd_struct(arg)
        
    def execute(self):
        self.send_screen(TimerScreen())


class Sleep(Command):
    
    def __init__(self) -> None:
        super().__init__()
        arg = CommandArgument('sleep', 'Sleep for x seconds')
        self.add_argument_to_cmd_struct(arg)
        
    def execute(self, seconds):
        self.widget.post_message(self.Start())
        sleep(int(seconds))
        self.widget.post_message(self.Finish())
import logging
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import Label, RichLog

from ..command import Command

class CommandLog(Widget):
    """
    Custom widget to write logs from the commands.
    The severity levels are the same as the logging module.
    The different levels map to different colors for markup.
    Command names are magenta1 and all uppercase.
    
    COLOR_MAPPING = {
        logging.INFO: 'steel_blue1',
        logging.DEBUG: 'green1',
        logging.WARNING: 'yellow1',
        logging.ERROR: 'bright_red',
        logging.CRITICAL: 'dark_red'
    }
    """
    
    DEFAULT_CSS = """
        CommandLog {
            height: 50;
            border: round white;
            
            Label {
                text-align: center;
                width: auto;
            }
            
            RichLog {
                height: auto;
                max-height: 50;
                border: none;
                border-top: solid white;
                background: transparent;
            }
        }
    """
    
    COLOR_MAPPING = {
        logging.INFO: 'steel_blue1',
        logging.DEBUG: 'green1',
        logging.WARNING: 'yellow1',
        logging.ERROR: 'bright_red',
        logging.CRITICAL: 'dark_red'
    }
    
    def compose(self) -> ComposeResult:
        yield Container(
            Label('Command Log'),
            RichLog(markup=True)
        )
        
    def gen_record(self, event: Command.Log) -> str:
        """
        Handle the log from the command.
        
        Args:
            event (Command.Log)
            
        Returns:
            msg (str): The formatted log message.
        """
        level_name = logging.getLevelName(event.severity)
        color = self.COLOR_MAPPING[event.severity]
        
        lvl = f'[{color}]{level_name}[/{color}]'
        cmd = f'[bold magenta1]{event.command.upper()}[/bold magenta1]'
        time = f"[steel_blue]{datetime.now().strftime('[%H:%M:%S]')}[/steel_blue]"
        
        msg = f'{time} {lvl}  {cmd} - {event.msg}'
        return msg

import logging
from typing import Annotated
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, RichLog

from .. import configure
from ..commands import Command

class ConsoleLog(Widget):
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
    
    class Reload(Message):
        """Message to Reload both the Set command and settings display"""
        pass
    
    COLOR_MAPPING = {
        logging.INFO: 'steel_blue1',
        logging.DEBUG: 'green1',
        logging.WARNING: 'yellow1',
        logging.ERROR: 'bright_red',
        logging.CRITICAL: 'dark_red'
    }
    
    DEFAULT_CSS = """
        ConsoleLog {
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
    
    DEFAULT_CONFIG = {
        'Logging': {
            'description': 'The config for logging.',
            'console-lvl': {
                'description': 'The minimum severity level for the console log.',
                'value': 'INFO',
                'options': {
                    'DEBUG': 10,
                    'INFO': 20,
                    'WARNING': 30,
                    'ERROR': 40,
                    'CRITICAL': 50
                }
            }   
        }
    }
    
    def __init__(
        self,
        config_path: Annotated[str, 'The path to the config.'],
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.config_path = config_path
    
    def compose(self) -> ComposeResult:
        yield Container(
            Label('Command Log'),
            RichLog(markup=True)
        )
        
    def on_mount(self) -> None:
        if not configure.check_section('Logging', self.config_path):
            configure.add_section(
                'Logging',
                self.DEFAULT_CONFIG,
                self.config_path
            )
            self.post_message(self.Reload())
            
        
    def check_log_level(self, severity: int):
        current_level_name = configure.get_setting_value(
            'Logging',
            'console-lvl',
            self.config_path
        )
        
        current_level = logging.getLevelNamesMapping()[current_level_name]
        
        if severity >= current_level:
            return True

        return False
        
    def gen_record(self, event: Command.Log) -> str:
        """
        Handle the log from the command.
        
        Args:
            event (Command.Log)
            
        Returns:
            msg (str): The formatted log message.
        """
        if not self.check_log_level(event.severity):
            return None
        
        level_name = logging.getLevelName(event.severity)
        color = self.COLOR_MAPPING[event.severity]
        
        lvl = f'[{color}]{level_name}[/{color}]'
        cmd = f'[bold magenta1]{event.command.upper()}[/bold magenta1]'
        time = f"[steel_blue]{datetime.now().strftime('[%H:%M:%S]')}[/steel_blue]"
        
        msg = f'{time} {lvl}  {cmd} - {event.msg}'
        return msg

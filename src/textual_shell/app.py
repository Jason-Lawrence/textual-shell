from textual import log
from textual.app import App
from textual.css.query import NoMatches
from textual.widgets import DataTable, RichLog

from textual_shell.command import Set, Command
from textual_shell.widgets import SettingsDisplay, CommandLog


class ShellApp(App):
    """Base app for the shell. Needed to catch messages sent by commands."""
        
    DEFAULT_CSS = """
            Screen {
                layers: shell popup;
            }
        """    
    
    def on_set_settings_changed(self, event: Set.SettingsChanged) -> None:
        """
        Catch messages for when a setting has been changed.
        Update the settings display to reflect the new value.
        """
        event.stop()
        try:
            settings_display = self.query_one(SettingsDisplay)
            table = settings_display.query_one(DataTable)
            row_key = f'{event.section_name}.{event.setting_name}'
            column_key = settings_display.column_keys[1]
            table.update_cell(row_key, column_key, event.value, update_width=True)
            
        except NoMatches as e:
            log(f'SettingsDisplay widget is not in the DOM.')

    def on_command_log(self, event: Command.Log) -> None:
        """
        Catch any logs sent by any command and write 
        them to the CommandLog widget.
        """
        event.stop()
        command_log = self.query_one(CommandLog)
        rich_log = command_log.query_one(RichLog)
        log_entry = command_log.gen_record(event)
        rich_log.write(log_entry)
from textual import log
from textual.app import App
from textual.css.query import NoMatches
from textual.widgets import DataTable, RichLog

from textual_shell.command import Set, Command
from textual_shell.widgets import SettingsDisplay, CommandLog


class ShellApp(App):
        
    def on_set_settings_changed(self, event: Set.SettingsChanged) -> None:
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
        event.stop()
        command_log = self.query_one(CommandLog)
        rich_log = command_log.query_one(RichLog)
        log_entry = f'[{event.severity}] {event.command}:\t{event.msg}'
        rich_log.write(log_entry)
from textual import log
from textual.app import App
from textual.css.query import NoMatches
from textual.widgets import DataTable, RichLog

from textual_shell.commands import Set, Command
from textual_shell.widgets import (
    ConsoleLog, SettingsDisplay, Shell
)


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
            
    def on_console_log_reload(self, event: ConsoleLog.Reload) -> None:
        """Handle Reloading the settings."""
        event.stop()
        shell = self.query_one(Shell)
        if set := shell.get_cmd_obj('set'):
            set.cmd_struct.clear()
            set._load_sections_into_struct()
        
        try:
            settings_display = self.query_one(SettingsDisplay)
            settings_display.reload()
            
        except NoMatches as e:
            log(f'SettingsDisplay widget is not in the DOM.')

    def on_command_log(self, event: Command.Log) -> None:
        """
        Catch any logs sent by any command and write 
        them to the CommandLog widget.
        """
        event.stop()
        try:
            command_log = self.query_one(ConsoleLog)
            rich_log = command_log.query_one(RichLog)
            log_entry = command_log.gen_record(event)
            if log_entry:
                rich_log.write(log_entry)
        
        except NoMatches as e:
            log(f'Console Log not found')
        
    def on_command_push_screen(self, event: Command.PushScreen) -> None:
        """
        Push the screen for the output of the command.
        """
        event.stop()
        self.push_screen(event.screen)
        
    def on_command_start(self, event: Command.Start) -> None:
        """Catch when a command has started."""
        shell = self.query_one(Shell)
        prompt_input = shell._get_prompt_input()
        prompt_input.disabled = True
        
    def on_command_finish(self, event: Command.Finish) -> None:
        """Catch when a command has finished."""
        shell = self.query_one(Shell)
        prompt_input = shell._get_prompt_input()
        prompt_input.disabled = False
        prompt_input.focus()

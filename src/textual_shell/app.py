from textual import log
from textual.app import App
from textual.css.query import NoMatches
from textual.widgets import (
    DataTable,
    RichLog
)

from .command import Command
from .commands import (
    Attach,
    Console,
    History,
    Kill,
    SetJob
)
from .job import Job
from .widgets import (
    BaseShell,
    ConsoleLog,
    JobManager,
    SettingsDisplay
)


class BaseShellApp(App):
    """Base app for the shell. Needed to catch messages sent by commands."""
        
    DEFAULT_CSS = """
            Screen {
                layers: shell popup;
            }
        """
        
    def _get_job_manager(self) -> JobManager:
        """Search through all of the screens to find the one with the Job Manager widget."""
        for screen in self.app.screen_stack:
            try: 
                return screen.query_one(JobManager)

            except NoMatches as e:
                pass
    
    def _get_shell(self) -> BaseShell:
        """Search through all of the screens to find the one with the Shell widget."""
        for screen in self.app.screen_stack:
            try:
                return screen.query_one(BaseShell)
            
            except NoMatches as e:
                pass
            
    def on_set_job_settings_changed(self, event: SetJob.SettingsChanged) -> None:
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
        shell = self._get_shell()
        if set := shell.get_cmd_obj('set'):
            set.load_sections()
        
        try:
            settings_display = self.query_one(SettingsDisplay)
            settings_display.reload()
            
        except NoMatches as e:
            log(f'SettingsDisplay widget is not in the DOM.')

    def on_job_log(self, event: Job.Log) -> None:
        """
        Catch any logs sent by any Job and write 
        them to the ConsoleLog widget.
        """
        event.stop()
        try:
            console_log = self.query_one(ConsoleLog)
            rich_log = console_log.query_one(RichLog)
            log_entry = console_log.gen_record(event)
            if log_entry:
                rich_log.write(log_entry)
        
        except NoMatches as e:
            log(f'Console Log not found')
            
    def on_command_log(self, event: Command.Log) -> None:
        """
        Catch any logs sent by any Command and write
        them to the ConsoleLog widget
        """
        event.stop()
        try:
            console_log = self.query_one(ConsoleLog)
            rich_log = console_log.query_one(RichLog)
            log_entry = console_log.gen_record(event)
            if log_entry:
                rich_log.write(log_entry)
                
        except NoMatches as e:
            log(f'Console Log not found.')
            
    def on_console_clear(self, event: Console.Clear):
        """Handler for clearing the console."""
        event.stop()
        try:
            console_log = self.query_one(ConsoleLog)
            rich_log = console_log.query_one(RichLog)
            rich_log.clear()
            
        except NoMatches as e:
            pass      
    
    def on_history_clear(self, event: History.Clear):
        """Handler for clearing the history log."""
        event.stop()
        try:
            shell = self._get_shell()
            history = shell.query_one(RichLog)
            history.clear()
            shell.history_count = 0
            shell.update_suggestions_location(0)
            
        except NoMatches as e:
            pass
    
    def on_job_start(self, event: Job.Start) -> None:
        """Add new jobs."""
        event.stop()
        job_manager = self._get_job_manager()
        job_manager.add_job(event.job)
        
        shell = self._get_shell()
        jobs = shell.get_cmd_obj('jobs')
        jobs.add_job_id(event.job.id)

    def on_job_finish(self, event: Job.Finish) -> None:
        """Clean up finished jobs."""
        event.stop()
        job_manager = self._get_job_manager()
        job_manager.remove_job(event.job_id)
        
        shell = self._get_shell()
        jobs = shell.get_cmd_obj('jobs')
        jobs.remove_job_id(event.job_id)
        
    def on_job_status_change(self, event: Job.StatusChange) -> None:
        """Update the status of a job."""
        event.stop()
        job_manager = self._get_job_manager()
        job_manager.update_job_status(event.job_id, event.status)

    def on_attach_to_job(self, event: Attach.To_Job) -> None:
        """Attach to the jobs screen."""
        event.stop()
        job_manager = self._get_job_manager()
        job_manager.switch_job_screen(event.job_id)

    def on_kill_selected(self, event: Kill.Selected) -> None:
        """Kill the job."""
        event.stop()
        job_manager =self._get_job_manager()
        job_manager.kill_job(event.job_id)

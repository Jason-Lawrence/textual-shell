from typing import Annotated

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Label

from textual_shell import configure

class SettingsDisplay(Widget):
    """
    Custom widget for displaying settings for the shell.
    
    Args:
        config_path (str): The path to the config file.
    """
    
    DEFAULT_CSS = """
    
        SettingsDisplay {
            grid-size: 2;
            grid-columns: 1fr;
            grid-rows: auto 1fr;
            border: solid white;
            height: 15;
                
            Label {
                text-align: center;
                column-span: 2;
            }
            
            DataTable {
                column-span: 2;
                border-top: solid white;
            }
        }
    """
    
    def __init__(
        self,
        config_path: Annotated[str, 'THe path to the config file.']=None,
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.config_path = config_path
                
    def compose(self) -> ComposeResult:
        yield Label('Settings')
        yield DataTable()
        
    def load_settings(self) -> None:
        """Load the settings from the config on mount."""
        table = self.query_one(DataTable)
        config = configure.get_config(self.config_path)
        for section in config:
            for key, val in config[section].items():
                if key == 'description':
                    continue
                
                setting = f'{section}.{key}'
                value = val['value']
                row = (setting, value)
                table.add_row(*row, key=setting)
                
    def reload(self) -> None:
        """Reload the DataTable if config has changed."""
        table = self.query_one(DataTable)
        table.clear()
        self.load_settings()
        
    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.can_focus = False
        self.column_keys = table.add_columns('setting', 'value')
        self.load_settings()
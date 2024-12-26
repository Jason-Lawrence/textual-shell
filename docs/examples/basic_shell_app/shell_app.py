
from textual.app import App, ComposeResult
from textual.geometry import Offset
from textual.widgets import Header, Footer
from textual_shell.widgets import Shell, CommandList
from textual_shell.command import Help, Set


class ShellApp(App):
    
    CSS_PATH = 'style.css'
    cmd_list = [Help(), Set()]
    command_names = [cmd.name for cmd in cmd_list]
    
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield CommandList(self.command_names)
        yield Shell(
            self.cmd_list,
            prompt='xbsr <$ ',
            suggestion_offset=Offset(10, 3)
        )
        
if __name__ == '__main__':
    ShellApp().run()
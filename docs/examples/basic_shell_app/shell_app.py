
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual_shell.widgets import Shell
from textual_shell.command import Help, Set


class ShellApp(App):
    
    CSS_PATH = 'style.css'
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Shell([Help(), Set()])
        
if __name__ == '__main__':
    ShellApp().run()
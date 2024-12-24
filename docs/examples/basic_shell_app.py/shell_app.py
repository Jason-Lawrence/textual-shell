
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual_shell.widgets import Shell


class ShellApp(App):
    
    CSS_PATH = 'style/style.tcss'
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Shell()
        
if __name__ == '__main__':
    ShellApp().run()
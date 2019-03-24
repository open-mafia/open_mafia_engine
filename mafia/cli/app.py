"""Command-line mafia application (for moderators).

This provides an example of interface to the API.
"""

from prompt_toolkit import Application
# from prompt_toolkit.application.current import get_app
# from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.layout.containers import HSplit, VSplit  # , Window
# from prompt_toolkit.layout.controls import 
#   BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import (
    HorizontalLine, VerticalLine, 
    TextArea, SearchToolbar, 
)
from prompt_toolkit.styles import Style

#


class GameMenu(object):
    """Main menu app thing. Under construction.

    Approximate layout:

        =========================================
        | Player Status | Game Status | Options |
        |               |             |         |
        |               |             |         |
        -----------------------------------------
        | >>>                                   |
        =========================================
    """

    def __init__(self):
        # Output fields
        self.out_player_status = TextArea(
            style='class:output-field', 
            text="Player Status:",
        )
        self.out_game_status = TextArea(
            style='class:output-field', 
            text="Game Status:",
        ) 
        self.out_debug = TextArea(
            style='class:output-field', 
            text="<Debug output>",
        )
        
        # Input fields
        self.search_field = SearchToolbar()
        self.input_field = TextArea(
            height=1, prompt='>>> ',
            style='class:input-field', 
            multiline=False, wrap_lines=False, 
            search_field=self.search_field, 
            # accept_handler=self.cb_enter_pressed, 
            accept_handler=self.cb_enter_pressed, 
        )

        # Layout
        self.root_container = HSplit([
            VSplit([
                self.out_player_status,
                VerticalLine(),
                self.out_game_status,
                VerticalLine(),
                self.out_debug,
            ]),
            HorizontalLine(),
            self.input_field, 
            self.search_field,
        ])

        # Keybinds
        self.kb = KeyBindings()
        self.kb.add('c-q')(self.do_exit)

        self.style = Style([
            ('output-field', 'bg:#000044 #ffffff'),
            ('input-field', 'bg:#000000 #ffffff'),
            ('line', '#004400'),
        ])

        self.app = Application(
            layout=Layout(
                self.root_container, 
                focused_element=self.input_field
            ),
            style=self.style, key_bindings=self.kb, 
            full_screen=True, mouse_support=True,
        )

    def do_exit(self, event):
        # get_app().exit()
        event.app.exit()

    def update_player_status_text(self):
        pass

    def update_game_status_text(self):
        pass

    def update_debug_text(self):
        input_text = self.input_field.text
        new_debug_text = self.out_debug.text + "\n" + input_text
        self.out_debug.buffer.document = Document(
            text=new_debug_text,
            cursor_position=len(new_debug_text),
        )

    def cb_enter_pressed(self, buff):
        """Callback for input validation."""

        # Do action
        # TODO: Implement

        # Update text everything
        self.update_debug_text()
        self.update_player_status_text()
        self.update_game_status_text()


#


if __name__ == "__main__":
    z = GameMenu()
    z.app.run()

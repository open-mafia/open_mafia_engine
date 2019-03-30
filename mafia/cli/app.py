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
from prompt_toolkit.widgets import HorizontalLine, VerticalLine, TextArea, SearchToolbar
from prompt_toolkit.styles import Style

#
from mafia.api.vanilla import VanillaExecutor


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
        # TEMP:
        # Initialize engine copy
        self.lobby = []
        self.executor = None

        # Styling
        self.style = Style(
            [
                ("output-field", "bg:#000044 #ffffff"),
                ("input-field", "bg:#000000 #ffffff"),
                ("line", "#004400"),
            ]
        )

        # Output fields
        self.out_player_status = TextArea(
            style="class:output-field", text="Player Status:"
        )
        self.out_game_status = TextArea(style="class:output-field", text="Game Status:")
        self.out_options = TextArea(style="class:output-field", text="Options:")

        # Input fields
        self.search_field = SearchToolbar()
        self.input_field = TextArea(
            height=1,
            prompt=">>> ",
            style="class:input-field",
            multiline=False,
            wrap_lines=False,
            search_field=self.search_field,
            # accept_handler=self.cb_enter_pressed,
            accept_handler=self.cb_enter_pressed,
        )

        # Layout
        self.root_container = HSplit(
            [
                VSplit(
                    [
                        self.out_player_status,
                        VerticalLine(),
                        self.out_game_status,
                        VerticalLine(),
                        self.out_options,
                    ]
                ),
                HorizontalLine(),
                self.input_field,
                self.search_field,
            ]
        )

        # Keybinds
        self.kb = KeyBindings()
        self.kb.add("c-q")(self.do_exit)

        self.app = Application(
            layout=Layout(self.root_container, focused_element=self.input_field),
            style=self.style,
            key_bindings=self.kb,
            full_screen=True,
            mouse_support=True,
        )

        # Just update the text
        self.do_update_text()

    def do_exit(self, event):
        # get_app().exit()
        event.app.exit()

    #
    VanillaExecutor.generate(5)

    def do_update_text(self):
        """Updates text everywhere."""

        # update options text
        options = []
        self.out_options.buffer.document = Document(
            "\n  ".join(["Options:"] + options + ["(Ctrl-Q to quit)"])
        )

        # update player_status text
        if self.executor is None:
            if len(self.lobby) == 0:
                player_status = ["(No players)"]
            else:
                player_status = self.lobby
        else:
            player_status = ["No game started."]

        self.out_player_status.buffer.document = Document(
            "\n  ".join(["Player Status"] + player_status)
        )

        # update game_status text
        self.out_game_status.buffer.document = Document(
            "\n  ".join(["Game Status"] + ["Awaiting players."])
        )

    def cb_enter_pressed(self, buff):
        """Callback for input validation."""

        input_text = self.input_field.text
        input_text

        # Do action
        # TODO: Implement

        # Update text everything
        self.do_update_text()


#


if __name__ == "__main__":
    z = GameMenu()
    z.app.run()

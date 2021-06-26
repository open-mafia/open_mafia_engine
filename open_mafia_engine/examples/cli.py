"""Example command-line application built using prompt_toolkit and open_mafia_engine."""

import shlex
import traceback
from textwrap import dedent, indent

from prompt_toolkit.application import Application
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window, VSplit
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import SearchToolbar, TextArea

import open_mafia_engine.api as mafia

if mafia.PYGMENTS_AVAILABLE:
    from prompt_toolkit.lexers import PygmentsLexer

    lexer = PygmentsLexer(mafia.MafiaCliLexer)
else:
    lexer = None


# The key bindings.
kb = KeyBindings()


@kb.add("c-c", "c-c")
@kb.add("c-q", "c-q")
def _(event):
    "Pressing Ctrl-Q or Ctrl-C twice will exit the user interface."
    event.app.exit()


status_field = TextArea(
    style="class:status-field",
    text="Current status will appear here.",
)

history_field = TextArea(
    style="class:history-field",
    text="",
    lexer=lexer,
)

search_field = SearchToolbar()
input_field = TextArea(
    height=1,
    prompt=">>> ",
    style="class:input-field",
    multiline=False,
    wrap_lines=False,
    search_field=search_field,
    lexer=lexer,
)


runner = mafia.CommandRunner[str](
    parser=mafia.ShellCommandParser(),
    lobby=mafia.AutoAddStrLobby(admin_names=["admin"]),
)


def set_status_text(msg: str):
    """Sets the status field text."""
    new_text = "Current Status:\n" + msg
    status_field.buffer.document = Document(
        text=new_text, cursor_position=len(new_text)
    )


def update_status_text():
    admstr = ", ".join(runner.lobby.admin_names)
    if runner.in_game:
        game: mafia.Game = runner.game
        txt = f"[In Game]\n\nAdmins: {admstr}\nPhase: {game.current_phase.name}\n"
        for act in game.actors:
            txt += (
                "\n-----------------\n"
                + f"{act.name} - {', '.join(f.name for f in act.factions)}"
                + indent(
                    "\n".join([abil.full_description() for abil in act.abilities]),
                    "  ",
                )
            )
            if len(act.status) > 0:
                txt += "\nStatus:" + "\n".join(
                    [f"  {k}: {v}" for k, v in act.status.items()]
                )
    else:
        txt = f"[In Lobby]\n\nAdmins: {admstr}\nPlayers:\n"
        if len(runner.lobby.players) == 0:
            txt += "  <no players>"
        else:
            txt += "\n".join(f"  {x}" for x in runner.lobby.player_names)
    set_status_text(txt)


def submit_command(buff):
    """This runs when we press 'enter' on the input field."""
    text = input_field.text

    # Add text to output buffer.
    new_history = history_field.text + "\n> " + text + "\n"

    # Handle with the runner
    _parts = shlex.split(text, posix=True)
    if len(_parts) == 0:
        return
    src = _parts[0]
    other = ", ".join([f'"{x}"' for x in _parts[1:]])
    try:
        runner.parse_and_run(src, other)
        # TODO: How do we return stuff?
        update_status_text()
    except Exception as e:
        err_str = traceback.format_exc()
        new_history += err_str + "\n"

    # Print text to history buffer
    history_field.buffer.document = Document(
        text=new_history, cursor_position=len(new_history)
    )


input_field.accept_handler = submit_command

container = HSplit(
    [
        VSplit(
            [status_field, Window(width=1, char="|", style="class:line"), history_field]
        ),
        Window(height=1, char="-", style="class:line"),
        input_field,
        search_field,
    ]
)


# Define application.
style = Style(
    [
        ("input-field", "bg:#000000 #ffffff"),
        ("history-field", "bg:#111111 #ffffff"),
        ("status-field", "bg:#000000 #ffffff"),
        ("line", "#004400"),
    ]
)
application = Application(
    layout=Layout(container, focused_element=input_field),
    key_bindings=kb,
    style=style,
    # mouse_support=False,
    full_screen=True,
)

if __name__ == "__main__":
    update_status_text()
    application.run()

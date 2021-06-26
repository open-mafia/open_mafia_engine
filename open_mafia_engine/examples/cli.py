"""Example command-line application built using prompt_toolkit and open_mafia_engine."""

try:
    import prompt_toolkit
except ImportError:
    raise ImportError(
        "Please install prompt_toolkit, either directly or via extras:\n"
        "pip install open_mafia_engine[examples]",
        name="prompt_toolkit",
    )

import shlex
import traceback
from textwrap import indent

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import SearchToolbar, TextArea

import open_mafia_engine.api as mafia

if mafia.PYGMENTS_AVAILABLE:
    from prompt_toolkit.lexers import PygmentsLexer

    lexer = PygmentsLexer(mafia.MafiaCliLexer)
else:
    lexer = None

help_str = """
Non-mafia commands:
  exit - exit the application (also works with Ctrl-C twice, or Ctrl-Q twice)
  help - show this help

Mafia command structure:
  USER COMMAND [ARG1 ...]

Basic commands:
  USER join               Joins the game.
  USER out                Leaves the game.
  ADMIN create-game test  Creates the "test game".
  ADMIN phase             Change the phase.
  USER vote TARGET        Votes for the TARGET.
  USER do action ARG      Does an action, with one or more arguments.
"""

# Create the Mafia command runner, which controls the lobby and game
runner = mafia.CommandRunner[str](
    parser=mafia.ShellCommandParser(),
    lobby=mafia.AutoAddStrLobby(admin_names=["admin"]),
)

# Add key bindings.
kb = KeyBindings()


@kb.add("c-c", "c-c")
@kb.add("c-q", "c-q")
async def _(event):
    "Pressing Ctrl-Q or Ctrl-C twicw will exit the user interface."

    get_app().exit()


history_field = TextArea(
    style="class:history-field",
    text="",
    lexer=lexer,
)
status_field = TextArea(
    style="class:status-field",
    text="Current status will appear here.",
)


def set_status_text(msg: str):
    """Sets the status field text."""
    new_text = "Current Status: " + msg
    status_field.buffer.document = Document(
        text=new_text, cursor_position=len(new_text)
    )


SEP = "-----------------"


def update_status_text():
    admstr = ", ".join(runner.lobby.admin_names)
    if runner.in_game:
        game: mafia.Game = runner.game

        # Game status
        txt = f"[In Game]\n\nAdmins: {admstr}\nPhase: {game.current_phase.name}\n"

        # Actor status
        txt += "\nActor Status:"
        for act in game.actors:
            txt += (
                f"\n\n{SEP}\n"
                + f"{act.name} - {', '.join(f.name for f in act.factions)}"
                + "\n"
                + indent(
                    "\n".join([abil.full_description() for abil in act.abilities]),
                    "  ",
                )
            )
            if len(act.status) > 0:
                txt += "\nStatus:\n" + "\n".join(
                    [f"  {k}: {v}" for k, v in act.status.items()]
                )
        txt += f"\n\n{SEP}\n"

        # Display vote tally status
        tallies = game.aux.filter_by_type(mafia.LynchTally)
        if len(tallies) == 1:
            tally: mafia.LynchTally = tallies[0]

            vr = tally.results
            if len(vr.vote_counts) > 0:
                vres = ["Vote Count:"]
                # TODO: Make sure this is proper who-votes-for-whom behavior.
                for go, cnt, voters in vr.vote_map:
                    if cnt <= 0:
                        continue
                    if isinstance(go, mafia.Actor):
                        name = go.name
                    elif isinstance(go, mafia.VoteAgainstAll):
                        name = "No Lynch"
                    else:
                        name = str(go)
                    voter_str = ", ".join([v.name for v in voters])
                    vres.append(f"  {name} ({cnt}) - {voter_str}")

                try:
                    # This is less tested, but hopefully won't fail
                    vres.append("")
                    vres.append("Vote Leaders:")
                    vls = []
                    for vl in vr.vote_leaders:
                        if isinstance(vl, mafia.Actor):
                            vls.append(vl.name)
                        elif isinstance(vl, mafia.VoteAgainstAll):
                            vls.append("No Lynch")
                        else:
                            vls.append(str(vl))
                    vres.append("  " + ", ".join(vls))
                except Exception:
                    pass
                txt += "\n" + "\n".join(vres)
    else:
        txt = f"[In Lobby]\n\nAdmins: {admstr}\nPlayers:\n"
        if len(runner.lobby.players) == 0:
            txt += "  <no players>"
        else:
            txt += "\n".join(f"  {x}" for x in runner.lobby.player_names)
    set_status_text(txt)


def get_words():
    """Gets possible words for completion.

    NOTE: This runs and is called, but is ignored for some reason.
    """
    res = (
        ["exit", "help"]
        + runner.currently_available_commands(source="admin")
        + runner.lobby.admin_names
        + runner.lobby.player_names
    )
    if runner.in_game:
        res += runner.game.faction_names
        res += [x.name for x in runner.game.phase_system.possible_phases]
    return res


search_field = SearchToolbar()
input_field = TextArea(
    height=1,
    prompt=">>> ",
    style="class:input-field",
    multiline=False,
    wrap_lines=False,
    search_field=search_field,
    lexer=lexer,
    completer=FuzzyWordCompleter(get_words),
)


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

    if src == "exit":
        get_app().exit()
    elif src == "help":
        new_history += help_str + "\n"
    else:
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
        ("history-field", "bg:#000000 #ffffff"),
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


def main():
    # TODO: Add Typer arguments to load external modules.
    update_status_text()
    application.run()


if __name__ == "__main__":
    main()

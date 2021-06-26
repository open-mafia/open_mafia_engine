"""Optional Pygments lexer for the Mafia 'shell'-style language."""

from pygments.lexer import RegexLexer
from pygments.token import *

__all__ = ["MafiaCliLexer", "ImplicitMafiaCliLexer"]


class MafiaCliLexer(RegexLexer):
    """Custom Pygments lexer for 'multi-user' Mafia command-line parser.

    Current syntax:

        USER COMMAND <arg> <arg>

    No argument validation is done, only quoting.
    """

    name = "MultiMafia"
    aliases = ["multi-mafia"]
    filenames = []

    tokens = {
        "root": [
            (R"^\s*", Text, "user"),
        ],
        "user": [
            (R'"', Name.Variable, "user-quote"),
            (R"\b\S+\b", Name.Variable, "command"),
        ],
        "user-quote": [
            ('[^"]+', Name.Variable),
            ('"', Name.Variable, "command"),
        ],
        "command": [
            (R'"', Name.Exception, "command-quote"),
            (R"\b\S+\b", Name.Exception, "args"),
        ],
        "command-quote": [
            ('[^"]+', Name.Exception),
            ('"', Name.Exception, "args"),
        ],
        "args": [
            (R'"', String.Double, "args-quote"),
            (R"\b.*\n", Text, "root"),
            (R"\s+\n", Text, "root"),
        ],
        "args-quote": [
            ('[^"]+', String.Double),
            ('"', String.Double, "#pop"),
        ],
    }


class ImplicitMafiaCliLexer(RegexLexer):
    """Custom Pygments lexer for 'single-user' Mafia command-line parser.

    Current syntax:

        COMMAND <arg> <arg>

    No argument validation is done, only quoting.
    """

    name = "ImplicitMafia"
    aliases = ["implicit-mafia", "single-mafia"]
    filenames = []

    tokens = {
        "root": [
            (R"^\s*", Text, "command"),
        ],
        "command": [
            (R'"', Name.Exception, "command-quote"),
            (R"\b\S+\b", Name.Exception, "args"),
        ],
        "command-quote": [
            ('[^"]+', Name.Exception),
            ('"', Name.Exception, "args"),
        ],
        "args": [
            (R'"', String.Double, "args-quote"),
            (R"\b.*\n", Text, "root"),
            (R"\s+\n", Text, "root"),
        ],
        "args-quote": [
            ('[^"]+', String.Double),
            ('"', String.Double, "#pop"),
        ],
    }

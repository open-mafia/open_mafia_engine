"""Optional Pygments lexer for the Mafia 'shell'-style language."""

from pygments.lexer import RegexLexer, bygroups
from pygments.token import *

__all__ = ["MafiaCliLexer", "MultiMafiaCliLexer"]


class MafiaCliLexer(RegexLexer):
    """Custom Pygments lexer for Mafia command-line parser. Not very complete.

    Current syntax:

        COMMAND <arg> <arg>

    There is also support for multi-line comments, but they should be removed.
    It was mostly for testing highlighting support. :)
    """

    name = "Mafia"
    aliases = ["mafia"]
    filenames = []

    tokens = {
        "root": [
            (R"\b^[\w'-]+\b", Keyword),
            (R"/\*", Keyword.Pseudo, "comment"),
            (R"\"", Name.Variable, "complexquote"),
            (R"\s", Text),
        ],
        "complexquote": [
            (R"\"", Name.Variable, "#pop"),
            (R"\S", Name.Variable),
        ],
        "comment": [
            (R"[^*/]", Keyword.Pseudo),
            (R"/\*", Keyword.Pseudo, "#push"),
            (R"\*/", Keyword.Pseudo, "#pop"),
            (R"[*/]", Keyword.Pseudo),
        ],
    }


class MultiMafiaCliLexer(RegexLexer):
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
            (R'"', Text, "args-quote"),
            (R"\b.*\n", Text, "root"),
            (R"\s+\n", Text, "root"),
        ],
        "args-quote": [
            ('[^"]+', String),
            ('"', String, "#pop"),
        ],
    }

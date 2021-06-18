"""Optional Pygments lexer for the Mafia 'shell'-style language."""

from pygments.lexer import RegexLexer
from pygments.token import *

__all__ = ["MafiaCliLexer"]


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

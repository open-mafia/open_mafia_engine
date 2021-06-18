"""Optional Pygments lexer for the Mafia 'shell'-style language."""

from pygments.lexer import RegexLexer
from pygments.token import *

__all__ = ["MafiaLexer"]


class MafiaLexer(RegexLexer):
    """Custom Pygments lexer for mafia commands."""

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

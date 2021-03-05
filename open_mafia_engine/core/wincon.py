from __future__ import annotations
from typing import Dict, List, Optional, Type

from open_mafia_engine.util.hook import HookModel


class Wincon(HookModel):
    """Victory condition definition.

    To create custom wincons, subclass this and set the `type`.
    """

    type: str

    class Hook:
        subtypes: Dict[str, Type[Wincon]] = {}
        builtins: Dict[str, Wincon] = {}
        defaults: Dict[str, Wincon] = {}


class AlignmentEliminatedWincon(Wincon):
    """Win if the factions are eliminated."""

    type: str = "alignments_eliminated"
    alignments: List[str]


class AlignmentMajorityWincon(Wincon):
    """Win if the given alignments have a majority."""

    type: str = "alignments_majority"
    alignments: List[str]


class SurvivalWincon(Wincon):
    """Win if you are alive at the end of the game."""

    type: str = "survival"
    is_alive: Optional[bool] = True

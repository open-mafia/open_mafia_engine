from dataclasses import dataclass, field
from typing import Any, Dict, Tuple, TypeVar

from open_mafia_engine.errors import MafiaError

__all__ = ["TUser", "RawCommand", "MafiaBadCommand"]

TUser = TypeVar("TUser")  # User type in your application


@dataclass(frozen=True)
class RawCommand:
    """Raw parsed command"""

    source: str
    name: str
    args: Tuple = tuple()
    kwargs: Dict[str, Any] = field(default_factory=dict)


class MafiaBadCommand(MafiaError, KeyError):
    """Bad command was passed."""

    def __init__(self, rc: RawCommand) -> None:
        self.raw_command = rc
        super().__init__(f"Bad command: {rc!r}")
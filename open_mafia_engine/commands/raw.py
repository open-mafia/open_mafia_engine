from dataclasses import dataclass, field
from typing import Any, Dict, Tuple, TypeVar

__all__ = ["TUser", "RawCommand"]

TUser = TypeVar("TUser")  # User type in your application


@dataclass(frozen=True)
class RawCommand:
    """Raw parsed command"""

    source: str
    name: str
    args: Tuple = tuple()
    kwargs: Dict[str, Any] = field(default_factory=dict)

from __future__ import annotations

import logging
import shlex
from abc import ABC, abstractmethod
from typing import List

from .raw import RawCommand

logger = logging.getLogger(__name__)

__all__ = ["AbstractCommandParser", "ShellCommandParser"]


class AbstractCommandParser(ABC):
    """Base for command parsers."""

    @abstractmethod
    def parse(self, source: str, obj: str) -> List[RawCommand]:
        """Parses `obj` into zero, one or more `RawCommand` objects."""
        return []


class ShellCommandParser(AbstractCommandParser):
    """Implementation for shell-like command parsing."""

    def parse(self, source: str, obj: str) -> List[RawCommand]:
        if not isinstance(obj, str):
            # raise TypeError(f"Expected str, got {obj!r}")
            logger.warning(f"Cannot parse object, ignoring: {obj!r}")
            return []

        text = obj
        # TODO: keyword and flag arguments? Not just positional :)
        raw = shlex.split(text, posix=True)
        res = RawCommand(source, raw[0], args=tuple(raw[1:]))
        return [res]


if __name__ == "__main__":
    # For testing
    sp = ShellCommandParser()
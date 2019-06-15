class MafiaError(Exception):
    """Base class for :mod:`mafia` errors."""


class AmbiguousName(UserWarning):
    """Multiple objects found for this name."""

from enum import Enum


class ActionResolutionType(str, Enum):
    """How actions are resolved."""

    instant = "instant"
    end_of_phase = "end_of_phase"

    def __repr__(self):
        cn = type(self).__qualname__
        return f"{cn}({self.value!r})"


class Outcome(str, Enum):
    """Outcome (victory or defeat)."""

    victory = "victory"
    defeat = "defeat"

    def __repr__(self):
        cn = type(self).__qualname__
        return f"{cn}({self.value!r})"

from typing import Callable, Dict

from open_mafia_engine.core import Outcome
from open_mafia_engine.prefab import XOutcomeChecker, XModel, XConstraint, XAlignment


__patterns__: Dict[str, Callable] = {}


def pattern(pat: str):
    """Decorator"""

    def inner(func):
        global __patterns__
        __patterns__[pat] = func
        return func

    return inner


class Shorthand:
    """Shorthands for YAML definitions."""

    def __class_getitem__(cls, key: str) -> XModel:
        global __patterns__
        for pat, func in __patterns__.items():
            if key.startswith(pat):
                return func(key)
        return getattr(cls, key)

    # Constraints
    con_mafia_kill = XConstraint(
        type="KeywordActionLimitPerPhaseConstraint",
        params=dict(keyword="mafia_kill_limit"),
    )

    # Outcomes
    win_if_mafia_die = XOutcomeChecker(
        type="FactionEliminatedOutcome",
        params=dict(faction_names="mafia"),
        outcome=Outcome.victory,
    )
    lose_if_mafia_die = XOutcomeChecker(
        type="FactionEliminatedOutcome",
        params=dict(faction_names="mafia"),
        outcome=Outcome.defeat,
    )
    win_if_town_die = XOutcomeChecker(
        type="FactionEliminatedOutcome",
        params=dict(faction_names="town"),
        outcome=Outcome.victory,
    )
    lose_if_town_die = XOutcomeChecker(
        type="FactionEliminatedOutcome",
        params=dict(faction_names="town"),
        outcome=Outcome.defeat,
    )

    # Alignments
    vanilla_town = XAlignment(
        name="town", outcome_checkers=[win_if_mafia_die, lose_if_town_die]
    )
    vanilla_mafia = XAlignment(
        name="mafia", outcome_checkers=[win_if_town_die, lose_if_mafia_die]
    )


@pattern("win-if-dead:")
def _wid(pat: str):
    pre = "win-if-dead:"
    factions = pat[len(pre) :].split(":")
    return XOutcomeChecker(
        type="FactionEliminatedOutcome",
        params=dict(faction_names=factions, outcome=Outcome.victory),
    )


@pattern("lose-if-dead:")
def _lid(pat: str):
    pre = "lose-if-dead:"
    factions = pat[len(pre) :].split(":")
    return XOutcomeChecker(
        type="FactionEliminatedOutcome",
        params=dict(faction_names=factions, outcome=Outcome.defeat),
    )

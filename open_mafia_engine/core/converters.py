import warnings

from open_mafia_engine.core.game import Game
from open_mafia_engine.core.game_object import converter
from open_mafia_engine.core.naming import ABILITY, PATH_SEP, TRIGGER, get_parts
from open_mafia_engine.core.phase_cycle import Phase
from open_mafia_engine.core.state import Ability, Actor, Faction, Trigger
from open_mafia_engine.util.matcher import FuzzyMatcher


@converter.register
def get_faction_by_name(game: Game, obj: str) -> Faction:
    """Gets the Faction by exact or fuzzy name match."""

    matcher = FuzzyMatcher({f.name: f for f in game.factions}, score_cutoff=20)
    try:
        return matcher[obj]
    except Exception as e:
        raise ValueError(f"Could not find Faction by name: {obj!r}") from e


@converter.register
def get_actor_by_name(game: Game, obj: str) -> Actor:
    """Gets the Actor by exact or fuzzy name match."""
    matcher = FuzzyMatcher({a.name: a for a in game.actors}, score_cutoff=10)
    try:
        return matcher[obj]
    except Exception as e:
        raise ValueError(f"Could not find Actor by name: {obj!r}") from e


@converter.register
def get_ability_by_path(game: Game, obj: str) -> Ability:
    """Gets the ability by 'path' made of names.

    Assuming PATH_SEP is "/", this will parse as:

        "{actor_name}/ability/{ability_name}"

    This will do fuzzy matching on Actor and Ability separately.
    TODO: Maybe do fuzzy matching on total string?
    """
    try:
        owner_name, _abil, abil_name = get_parts(obj)

        assert _abil == ABILITY
    except Exception as e:
        raise ValueError(f"Bad/non-existing path for Ability: {obj}") from e

    owner: Actor = get_actor_by_name(game, owner_name)
    matcher = FuzzyMatcher({ab.name: ab for ab in owner.abilities}, score_cutoff=10)
    try:
        return matcher[abil_name]
    except Exception as e:
        raise ValueError(f"Could not find Ability by path: {obj!r}") from e


@converter.register
def get_trigger_by_path(game: Game, obj: str) -> Trigger:
    """Gets the trigger by 'path' made of names.

    Assuming PATH_SEP is "/", this will parse as:

        "{actor_name}/trigger/{trigger_name}"

    This will do fuzzy matching on Actor and Trigger separately.
    TODO: Maybe do fuzzy matching on total string?
    """
    try:
        owner_name, _trig, trig_name = get_parts(obj)

        assert _trig == TRIGGER
    except Exception as e:
        raise ValueError(f"Bad/non-existing path for Trigger: {obj}") from e

    owner: Actor = get_actor_by_name(game, owner_name)
    matcher = FuzzyMatcher({tr.name: tr for tr in owner.triggers}, score_cutoff=10)
    try:
        return matcher[trig_name]
    except Exception as e:
        raise ValueError(f"Could not find Trigger by path: {obj!r}") from e


@converter.register
def get_phase_by_name(game: Game, obj: str) -> Phase:
    """Gets the phase by name from the cycle. Can raise KeyError."""
    try:
        return game.phase_system[obj]
    except KeyError:
        pass

    # Make sure we don't infinitely loop through phases
    N_MAX = 20
    options = {}
    for i, p in enumerate(game.phase_system.possible_phases):
        if i > N_MAX:
            warnings.warn(f"Found over {N_MAX} phases; maybe infinite?")
            break
        options[p.name] = p
    matcher = FuzzyMatcher(options, score_cutoff=50)
    return matcher[obj]

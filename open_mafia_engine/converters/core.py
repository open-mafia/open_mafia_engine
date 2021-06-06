from open_mafia_engine.core.naming import PATH_SEP, get_parts
from open_mafia_engine.core.game import Game
from open_mafia_engine.core.game_object import converter
from open_mafia_engine.core.state import Ability, Actor, Faction


@converter.register
def get_faction_by_name(game: Game, obj: str) -> Faction:
    """Gets the Faction by exact name match.

    TODO: Add fuzzy matching here.
    """
    try:
        idx = game.faction_names.index(obj)
    except ValueError as e:
        raise ValueError(f"Could not find Faction by name: {obj!r}") from e
    return game.actors[idx]


@converter.register
def get_actor_by_name(game: Game, obj: str) -> Actor:
    """Gets the Actor by exact name match.

    TODO: Add fuzzy matching here.
    """
    try:
        idx = game.actor_names.index(obj)
    except ValueError as e:
        raise ValueError(f"Could not find Actor by name: {obj!r}") from e
    return game.actors[idx]


@converter.register
def get_ability_by_path(game: Game, obj: str) -> Ability:
    """Gets the ability by 'path' made of names.

    Assuming PATH_SEP is "/", this will parse as:

        "{actor_name}/{ability_name}"

    TODO: Add fuzzy matching here.
    """
    owner_name, abil_name = get_parts(obj)
    owner: Actor = get_actor_by_name(game, owner_name)
    try:
        idx = owner.ability_names.index(abil_name)
    except ValueError as e:
        raise ValueError(f"Could not find Ability by path: {obj!r}") from e
    return owner.abilities[idx]

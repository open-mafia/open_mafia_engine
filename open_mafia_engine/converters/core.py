from open_mafia_engine.core.game import Game
from open_mafia_engine.core.game_object import converter
from open_mafia_engine.core.state import Actor, Faction


@converter.register
def get_actor_by_name(game: Game, obj: str) -> Actor:
    try:
        idx = game.actor_names.index(obj)
    except ValueError as e:
        raise ValueError(f"Could not find Actor by name: {obj!r}") from e
    return game.actors[idx]


@converter.register
def get_faction_by_name(game: Game, obj: str) -> Faction:
    try:
        idx = game.faction_names.index(obj)
    except ValueError as e:
        raise ValueError(f"Could not find Faction by name: {obj!r}") from e
    return game.actors[idx]

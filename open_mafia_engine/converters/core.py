from open_mafia_engine.core.game_object import converter
from open_mafia_engine.core.game import Game, Actor


@converter.register
def to_actor(game: Game, obj: str) -> Actor:
    actor_names = [a.name for a in game.actors]
    try:
        idx = actor_names.index(obj)
    except ValueError as e:
        raise ValueError(f"Could not find Actor by name: {obj!r}") from e
    return game.actors[idx]

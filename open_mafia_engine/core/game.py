from typing import List
from open_mafia_engine.core.game_object import GameObject
from open_mafia_engine.util.repr import ReprMixin


class Actor(GameObject):
    def __init__(self, name: str):
        self.name = name


class Game(ReprMixin):
    """Defines a single game state."""

    def __init__(self, actors: List[Actor] = []):
        self.actors = actors
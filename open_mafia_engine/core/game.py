from __future__ import annotations

from typing import List
from open_mafia_engine.core.game_object import GameObject
from open_mafia_engine.core.state import Actor
from open_mafia_engine.util.repr import ReprMixin


class Game(ReprMixin):
    """Defines a single game state."""

    def __init__(self):
        self.actors: List[Actor] = []

    def add(self, object: GameObject):
        if isinstance(object, Actor):
            self.actors.append(object)
        # TODO

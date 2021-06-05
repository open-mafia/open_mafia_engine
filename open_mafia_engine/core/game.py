from __future__ import annotations

from typing import List
from open_mafia_engine.core.game_object import GameObject, converter
from open_mafia_engine.util.repr import ReprMixin


class Actor(GameObject):
    """Fake Actor object."""

    def __init__(self, game: Game, /, name: str):
        self.name = name
        self.abilities: List[Ability] = []
        super().__init__(game)

    def add(self, ability: Ability):
        self.abilities.append(ability)


class Ability(GameObject):
    """Fake Ability object."""

    def __init__(self, game: Game, /, owner: Actor):
        if not isinstance(owner, Actor):
            raise TypeError(f"Expected Actor, got {owner!r}")

        self.owner = owner
        super().__init__(game)
        owner.add(self)


class Game(ReprMixin):
    """Defines a single game state."""

    def __init__(self):
        self.actors: List[Actor] = []

    def add(self, object: GameObject):
        if isinstance(object, Actor):
            self.actors.append(object)
        # TODO

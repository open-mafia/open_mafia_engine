from __future__ import annotations

from typing import TYPE_CHECKING, List

from open_mafia_engine.core.game_object import GameObject

if TYPE_CHECKING:
    from open_mafia_engine.core.game import Game


class Faction(GameObject):
    """Faction, a.k.a. Alignment."""

    def __init__(self, game: Game, /, name: str):
        self.name = name
        self._actors: List[Actor] = []
        super().__init__(game)

    @property
    def actors(self) -> List[Actor]:
        return list(self._actors)

    def add_actor(self, actor: Actor):
        if not isinstance(actor, Actor):
            raise TypeError(f"Expected Actor, got {actor!r}")
        if actor in self._actors:
            return
        self._actors.append(actor)
        actor._factions.append(self)


class Actor(GameObject):
    """Actor object."""

    def __init__(self, game: Game, /, name: str):
        self.name = name
        self._abilities: List[Ability] = []
        self._factions: List[Faction] = []
        super().__init__(game)

    @property
    def abilities(self) -> List[Ability]:
        return list(self._abilities)

    @property
    def factions(self) -> List[Faction]:
        return list(self._factions)

    def add_ability(self, ability: Ability):
        """Adds this ability to self, possibly removing the old owner."""
        if not isinstance(ability, Ability):
            raise TypeError(f"Expected Ability, got {ability!r}")
        if ability in self._abilities:
            return
        self._abilities.append(ability)
        if ability._owner is not self:
            ability._owner._abilities.remove(ability)
            ability._owner = self


class Ability(GameObject):
    """Fake Ability object."""

    def __init__(self, game: Game, /, owner: Actor):
        if not isinstance(owner, Actor):
            raise TypeError(f"Expected Actor, got {owner!r}")

        self._owner = owner
        super().__init__(game)
        owner.add_ability(self)

    @property
    def owner(self) -> Actor:
        return self._owner

from typing import List

from open_mafia_engine.core.all import (
    Actor,
    Event,
    Faction,
    Game,
)


class ENotify(Event):
    """Base event purely for notifications."""

    def __init__(self, game: Game, /, message: str):
        self.message = message
        super().__init__(game)


class EFActorNotify(ENotify):
    """Event that causes a message to be sent to an Actor."""

    def __init__(self, game: Game, /, message: str, actor: Actor):
        super().__init__(game, message=message)
        self.actor = actor


class EFactionNotify(ENotify):
    """Event that causes a message to be sent to a faction."""

    def __init__(self, game: Game, /, message: str, faction: Faction):
        super().__init__(game, message=message)
        self.faction = faction

    @property
    def actors(self) -> List[Actor]:
        return self.faction.actors

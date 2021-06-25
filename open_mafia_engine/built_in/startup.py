from abc import abstractmethod
from typing import List

from open_mafia_engine.core.all import (
    Actor,
    EPrePhaseChange,
    Faction,
    Game,
    handler,
    Event,
)

from .auxiliary import TempPhaseAux


class ECreateFactionChat(Event):
    """Event that signals creating a faction chat."""

    def __init__(self, game: Game, /, faction: Faction):
        super().__init__(game)
        self.faction = faction

    @property
    def actors(self) -> List[Actor]:
        return self.faction.actors


class FactionChatCreatorAux(TempPhaseAux):
    """Base class to create the faction chat for some faction."""

    def __init__(self, game: Game, /, faction: Faction):
        self.faction = faction
        key = f"create chat for {self.faction.name}"
        super().__init__(game, key=key, use_default_constraints=False)

    @handler
    def handle_startup(self, event: EPrePhaseChange):
        if event.old_phase != self.game.phase_system.startup:
            return
        # NOTE: Rather than create an action, since it's startup, we should
        # just be able to trigger event responses.
        self.game.process_event(ECreateFactionChat(self.game, self.faction))

    @property
    def actors(self) -> List[Actor]:
        return self.faction.actors

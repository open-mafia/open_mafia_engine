from __future__ import annotations

from typing import List
from open_mafia_engine.core.auxiliary import AuxHelper, AuxObject
from open_mafia_engine.core.event_system import EventEngine, Event, ActionQueue, Action
from open_mafia_engine.core.game_object import GameObject
from open_mafia_engine.core.state import Actor, Faction
from open_mafia_engine.util.repr import ReprMixin


class Game(ReprMixin):
    """Defines a single game state."""

    def __init__(self):
        self._event_engine = EventEngine(self)
        self._action_queue = ActionQueue(self)
        self._actors: List[Actor] = []
        self._factions: List[Faction] = []
        self._aux = AuxHelper(self)

    @property
    def event_engine(self) -> EventEngine:
        return self._event_engine

    @property
    def action_queue(self) -> ActionQueue:
        return self._action_queue

    @property
    def actors(self) -> List[Actor]:
        return list(self._actors)

    @property
    def actor_names(self) -> List[str]:
        return [x.name for x in self._actors]

    @property
    def factions(self) -> List[Faction]:
        return list(self._factions)

    @property
    def faction_names(self) -> List[str]:
        return [x.name for x in self._factions]

    @property
    def aux(self) -> AuxHelper:
        return self._aux

    def add(self, obj: GameObject):
        """Adds the object to this game.

        This is automatically called during `obj.__init__()`
        """
        if isinstance(obj, Actor):
            if obj not in self._actors:
                self._actors.append(obj)
        elif isinstance(obj, Faction):
            if obj not in self._factions:
                self._factions.append(obj)
        elif isinstance(obj, AuxObject):
            self._aux.add(obj)
        # TODO

    def process_event(self, event: Event, *, process_now: bool = False):
        """Processes the action."""
        responses: List[Action] = self.event_engine.broadcast(event)
        for resp in responses:
            self.action_queue.enqueue(resp)

        process_now = process_now or False
        if process_now:
            self.action_queue.process_all()

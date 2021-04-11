from __future__ import annotations

from typing import List, Union

from open_mafia_engine.core.engine import Action, ActionContext, CoreEngine, Event
from open_mafia_engine.state.game import GameState
from open_mafia_engine.state.prefab import Prefab

import open_mafia_engine.built_in.all as _  # noqa


class Game(object):
    """Core game object."""

    def __init__(self, engine: CoreEngine, state: GameState, context: ActionContext):
        self.engine = engine
        self.state = state
        self.context = context

    @classmethod
    def from_prefab(
        cls, names: List[str], prefab: Union[str, Prefab], variant: str = None
    ) -> Game:
        with CoreEngine() as engine:
            context = ActionContext()
            state = GameState.from_prefab(names=names, prefab=prefab, variant=variant)
        return cls(engine=engine, state=state, context=context)

    def process_event(self, event: Event):
        """Fully processes the event and its consequences."""

        with self.engine:
            responses: List[Action] = self.engine.get_responses(event)
            self.context.enqueue(responses)
            self.context.process(self.state)

    def process_action(self, action: Action):
        """Fully processes the action and its consequences."""

        with self.engine:
            self.context.enqueue(action)
            self.context.process(self.state)

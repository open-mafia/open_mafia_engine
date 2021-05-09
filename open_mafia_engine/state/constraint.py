from __future__ import annotations
from abc import abstractmethod


from typing import ClassVar, List, Optional
from open_mafia_engine.core.engine import (
    Action,
    ActionContext,
    CancelAction,
    EType,
    PreActionEvent,
    Subscriber,
)

from open_mafia_engine.util.hook import HookModel


class Constraint(HookModel, Subscriber):
    """Base constraint data type.

    To create a constraint, subclass this, change the 'type' default value,
    and make sure it's imported.
    """

    type: str

    class Hook:
        subtypes = {}
        builtins = {}
        defaults = {}

    class Action(CancelAction):
        def __init__(
            self,
            parent: Constraint,
            target: Action,
            *,
            priority: float = 0,
            canceled: bool = False,
        ):
            if not isinstance(target, Action):
                raise ValueError(f"Expected Action, got {target!r}")
            super().__init__(priority=priority, canceled=canceled, target=target)
            self.target = target
            self.parent = parent

        def __call__(self, game_state, context: ActionContext) -> None:
            # self.target.canceled = True
            pass

    def sub(self):
        """Runs the subscription."""
        self.subscribe_current(PreActionEvent)

    def respond(self, e: PreActionEvent) -> Optional[CancelAction]:
        """Delayed response to the Event with an Action (or None)."""
        if isinstance(e, PreActionEvent):
            ca = self.Action(parent=self, target=e.action)
            return ca

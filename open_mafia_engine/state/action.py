from typing import List, Optional
from open_mafia_engine.util.hook import HookModel
from open_mafia_engine.state.actor import Actor
from pydantic import BaseModel, validator


class Action(HookModel):
    """Base action.

    Attributes
    ----------
    type : str
    actor : None or Actor
        The actor performing the action. If None, the "environment" is assumed.
    priority : float
        The action priority for the queue. Default is 0.
    """

    type: str
    actor: Optional[Actor] = None
    priority: float = 0

    class Hook:
        subtypes = {}
        builtins = {}
        defaults = {}


class Event(HookModel):
    """Base event."""

    type: str

    class Hook:
        subtypes = {}
        builtins = {}
        defaults = {}


class EPreAction(Event):
    """Occurs before an action starts to resolve."""

    type: str = "pre-action"
    action: Action


class EPostAction(Event):
    """Occurs after an action resolves."""

    type: str = "post-action"
    action: Action


class ActionContext(BaseModel):
    """Context for actions and events, including a priority queue.

    Attributes
    ----------
    queue : List[Action]
        The list of enqueued actions.
        Ordering is by priority (desc) and adding time (ascending).
    history : List[Action]
        The history of actions that were taken.
    """

    queue: List[Action]
    history: List[Action] = []

    class Config:
        validate_assignment = True

    def enqueue(self, action: Action) -> None:
        # NOTE: This seems stupid, but it activates the validator
        self.queue = self.queue + [action]

    def process(self):
        """Processes all the actions in the queue."""

        # TODO: Implement

    @validator("queue", always=True)
    def _order_queue(cls, v):
        v = sorted(v, key=lambda x: -x.priority)
        return v
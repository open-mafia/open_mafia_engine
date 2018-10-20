"""Rudimentary test of the action overriding (bare bones)."""

import sys

from mafia.core import GameObject
from mafia.core.action import Action, PreActionEvent
from mafia.core.event import EventManager, Subscriber, ActionQueue

import logging
logger = logging.getLogger('mafia')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


class TestAction(Action):
    """Action that outputs a phrase."""

    _default_priority = 0

    def __init__(self, priority=_default_priority, phrase="hi"):
        super().__init__(priority=priority)
        self.phrase = phrase

    def _execute(self):
        super()._execute()
        print("TestAction: %s" % self.phrase)


class TestListener(GameObject, Subscriber):
    """Listener that changes the phrase."""

    def __init__(self, phrase="hmm"):
        self.phrase = phrase

    class TestResponseAction(Action):
        """Action that changes the phrase."""
        def __init__(self, his_action, phrase="hmm"):
            super().__init__()
            self.phrase = phrase
            self.his_action = his_action

        def _execute(self):
            print(
                "TestResponseAction: Saw event for action"
                " {}".format(self.his_action)
            )
            super()._execute()
            self.his_action.phrase = self.phrase

    def respond_to_event(self, event):
        if isinstance(event, PreActionEvent):
            if isinstance(event.action, TestAction):
                return TestListener.TestResponseAction(
                    event.action, self.phrase)


if __name__ == "__main__":
    tl = TestListener("haha i changed your phrase")
    EventManager.subscribe_me(tl, PreActionEvent)

    q1 = ActionQueue()
    q1.add(TestAction(0, "oi mate how you doin' pal?"))
    q1.execute()

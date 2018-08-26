
from mafia.core import GameObject
from mafia.core.action import Action, ActionQueue
from mafia.core.event import (
    InternalEvent, Subscriber, EventManager
)


class TestEvent(InternalEvent):
    """Simple event that holds generating action."""
    def __init__(self, my_action):
        self.my_action = my_action


class TestAction(Action):
    """Action that outputs a phrase."""
    def __init__(self, phrase="hi"):
        super().__init__()
        self.phrase = phrase

    def execute(self):
        # pre-action
        te = TestEvent(self)
        EventManager.handle_event(te)

        # do()
        print("TestAction: {}".format(self.phrase))

        # post-action


class TestListener(GameObject, Subscriber):
    """Listener that changes the phrase."""

    class TestResponseAction(Action):
        """Action that changes the phrase."""
        def __init__(self, his_action, phrase="hmm"):
            super().__init__()
            self.phrase = phrase
            self.his_action = his_action

        def execute(self):
            print(
                "TestResponseAction: Saw event for action"
                " {}".format(self.his_action)
            )
            self.his_action.phrase = self.phrase
        
    def respond_to_event(self, event):
        if isinstance(event, TestEvent):
            # print("Saw event {}".format(event))
            return TestListener.TestResponseAction(event.my_action, "hmm")


if __name__ == "__main__":
    tl = TestListener()
    EventManager.subscribe_me(tl, TestEvent)

    q1 = ActionQueue()
    q1.add(TestAction("oi"))
    q1.execute()

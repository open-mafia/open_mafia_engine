
from mafia.core import GameObject
from mafia.core.action import Action, ActionQueue
from mafia.core.event import (
    InternalEvent, Subscriber, EventManager
)


class TestEvent(InternalEvent):

    def __init__():
        pass


class TestAction(Action):

    def __init__(self, phrase="hi"):
        super().__init__()
        self.phrase = phrase

    def execute(self):
        # pre-action
        te = TestEvent()

        # do()
        print(self.phrase)

        # post-action


class TestResponseAction(Action):

    def __init__(self, phrase="hmm"):
        super().__init__()
        self.phrase = phrase

    def execute(self):
        print("saw phrase {}".format(self.phrase))
    

class TestListener(GameObject, Subscriber):

    def respond_to_event(self, event):
        if isinstance(event, TestEvent):
            print("Saw event")


em = EventManager()

tl = TestListener()
em.subscribe_me(tl, TestEvent)

q1 = ActionQueue()
q1.add(TestAction("oi"))
q1.execute()

""""""

from mafia.core import GameObject


class Action(GameObject):
    """Base class for all actions."""

    _default_priority = 0

    def __init__(self, priority=_default_priority):
        super().__init__()
        self.priority = priority

    def execute(self):
        # TODO: Implement Action.execute()
        # send pre-event
        # check()
        # do()
        # send post-event
        pass


class ActionQueue:
    """"""

    def __init__(self):
        self.members = []

    def add(self, action):
        """Adds action, with its priority, to the queue.

        Parameters
        ----------
        action : Action or None
            Passed action
        """
        if action is None:
            return
        self.members.append(action)

    def execute(self):
        """Executes all actions in queue."""

        # sort members by priority
        acts = sorted(self.members, key=lambda x: x.priority, reverse=True)        
        # Alt, but I don't like it:
        # from operator import attrgetter
        # sorted(self.members, key=attrgetter('priority'))

        # call members one at a time
        for act in acts:
            act.execute()

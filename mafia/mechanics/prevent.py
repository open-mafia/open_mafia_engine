"""Prevent actions from occurring by cancelling them."""

from mafia.core.event import Action


class PreventAction(Action):
    """Cancels the targeted action.

    Attributes
    ----------
    target : Action
        The action that will be prevented (canceled).
    canceled : bool
        Whether *this* action is canceled.
    """

    def __init__(self, target: Action, canceled: bool = False):
        if not isinstance(target, Action):
            raise TypeError(f"Expected Action, got {type(target)}")
        super().__init__(canceled=canceled)

    def __execute__(self) -> bool:
        if self.canceled:
            return False

        self.target.canceled = True
        return True

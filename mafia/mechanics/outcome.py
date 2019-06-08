"""Game-ending mechanics.

This module contains sample victory and losing conditions. 
"""

import logging
import typing
from mafia.core.event import Action, Event, Subscriber, PostActionEvent
from mafia.state.actor import Alignment
from mafia.mechanics.kill import KillAction


class FinalizeOutcome(Action):
    """An alignment has achieved an outcome condition.
    
    Attributes
    ----------
    alignment : Alignment
        The alignment that won/lost.
    victory : bool
        Whether the alignment won. If False, they lost. Defuault is True.
    canceled : bool
        Whether the victory was canceled.
    """

    def __init__(
        self, alignment: Alignment, victory: bool = True, canceled: bool = False
    ):
        if not isinstance(alignment, Alignment):
            raise TypeError(f"Expected Alignment, got {type(alignment)}.")
        super().__init__(canceled=canceled)
        self.alignment = alignment
        self.victory = victory

    def __execute__(self) -> bool:
        if self.canceled:
            return False

        result = "won" if self.victory else "lost"
        logging.getLogger(__name__).info(
            f"Alignment {self.alignment.name} has {result}."
        )
        return True


class OutcomeChecker(Subscriber):
    """Defines a win and/or lose condition.
    
    Checks the condition whenever some event is fired.

    Attributes
    ----------
    parent : Alignment
        The alignment that gets the result.
    """

    def __init__(self, parent: Alignment):
        self.parent = parent


class WhenEliminated(OutcomeChecker):
    """My (parent) alignment wins/loses if watched alignments are eliminated.
    
    Attributes
    ----------
    parent : Alignment
        The alignment that gets the result.
    watched : Alignment or list
        The alignment(s) whose well-being is checked.
    victory : bool
        Whether `parent` wins or loses when `watched` is eliminated.
        If True, they win. Default is True.
    """

    def __init__(
        self,
        parent: Alignment,
        watched: typing.Union[Alignment, typing.List[Alignment]],
        victory: bool = True,
    ):
        super().__init__(parent=parent)
        if isinstance(watched, Alignment):
            watched = [watched]
        self.watched = list(watched)
        self.victory = victory
        self.subscribe_to(PostActionEvent)

    def respond_to_event(self, event: Event) -> typing.Optional[Action]:
        if isinstance(event, PostActionEvent) and isinstance(event.action, KillAction):
            # check the 'watched' alignment
            for w in self.watched:
                for a in w.members:
                    if a.status.alive.value:
                        return None
            return FinalizeOutcome(alignment=self.parent, victory=self.victory)


class WhenHasOutcome(OutcomeChecker):
    """Set my (parent) outcome when watched alignment has an outcome.
    
    Attributes
    ----------
    parent : Alignment
        The alignment that gets the result.
    watched : Alignment
        The alignment whose outcome is checked.
    when_victory : None or bool
        Whether `parent` wins when `watched` wins. If None, no outcome.
    when_defeat : None or bool
        Whether `parent` wins when `watched` loses. If None, no outcome.
    """

    def __init__(
        self,
        parent: Alignment,
        watched: Alignment,
        when_victory: typing.Optional[bool] = None,
        when_defeat: typing.Optional[bool] = None,
    ):
        super().__init__(parent=parent)
        self.watched = watched
        self.when_victory = when_victory
        self.when_defeat = when_defeat
        self.subscribe_to(PostActionEvent)

    def respond_to_event(self, event: Event) -> typing.Optional[Action]:
        if isinstance(event, PostActionEvent):
            fo = event.action
            if isinstance(fo, FinalizeOutcome) and (fo.alignment is self.watched):
                res = self.when_victory if fo.victory else self.when_defeat
                if res is True:
                    return FinalizeOutcome(alignment=self.parent, victory=True)
                elif res is False:
                    return FinalizeOutcome(alignment=self.parent, victory=False)
                # Or None, in which case we don't care

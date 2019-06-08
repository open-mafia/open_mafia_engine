"""Game-ending mechanics.

This module contains sample victory and losing conditions. 

TODO
----
Figure out how to signal "game has ended".

Game-end-dependent wincons

    How to check if the game has finished? Can't just check 
    "all (other) alignments have won" because there can be multiple "undecided" ones.

Still need:

* Survivor (lose if killed, win when alive at end of game)

* Jester (win when lynched, lose when killed otherwise, lose when alive)

* Serial Killer (win when all non-SK are dead, lose when one is alive at end of game)

"""

import logging
import typing
from mafia.core.event import Action, Event, Subscriber, PostActionEvent
from mafia.state.game import Game, GameEndAction  # GameFinished,
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

    @property
    def priority(self) -> float:
        return float("+inf")

    def __execute__(self) -> bool:
        if self.canceled:
            return False

        if self.alignment.victory is not None:
            # We already know they won/lost, no use repeating it
            return False

        result = "won" if self.victory else "lost"
        logging.getLogger(__name__).info(
            f"Alignment {self.alignment.name} has {result}."
        )

        self.alignment.victory = self.victory
        return True


class GameEndChecker(Subscriber):
    """Automatically checks whether the game has ended.
    
    Attributes
    ----------
    game : Game
        The game that will be checked.
    """

    def __init__(self, game: Game):
        self.game = game
        self.subscribe_to(PostActionEvent)

    def respond_to_event(self, event: Event) -> typing.Optional[Action]:
        if isinstance(event, PostActionEvent):
            if isinstance(event.action, FinalizeOutcome):
                # one more outcome was finalized, check if all are
                for align in self.game.alignments:
                    if align.victory is None:
                        return None
                # All are set, so we end the game
                return GameEndAction(self.game)


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

    class TryFinalize(Action):
        def __init__(self, parent, canceled=False):
            super().__init__(canceled=canceled)
            self.parent = parent

        @property
        def priority(self) -> float:
            return float("-inf")

        def __execute__(self) -> bool:
            if self.canceled:
                return False
            for w in self.parent.watched:
                for a in w.members:
                    if a.status.alive.value:
                        return False
            return True

    def respond_to_event(self, event: Event) -> typing.Optional[Action]:
        if isinstance(event, PostActionEvent):
            if isinstance(event.action, KillAction):
                # check the 'watched' alignment
                return self.TryFinalize(parent=self)
            elif isinstance(event.action, self.TryFinalize):
                if event.action.parent is self:
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
                if res in [True, False]:
                    return FinalizeOutcome(alignment=self.parent, victory=res)
                # Or None, in which case we don't care

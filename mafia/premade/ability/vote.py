
# from mafia.core import GameObject  # , singleton
from mafia.core.event import InternalEvent, Subscriber, EventManager
from mafia.core.action import Action  # , PreActionEvent, PostActionEvent
from mafia.state.role import ActivatedAbility


class VoteBaseEvent(InternalEvent):
    """Base event for voting-related.
    
    Parameters
    ----------
    tally : VoteTally
        The tally to reset.
    """
    def __init__(self, tally):
        self.tally = tally


class VoteTally(Subscriber):
    """Object that handles voting.
    
    To extend this object, you can override _reset_tally() (most useful) 
    _cast_vote(), and respond_to_event().
    """
    def __init__(self):
        EventManager.subscribe_me(
            self, VoteTally.ResetRequestEvent, VoteTally.VoteCastRequestEvent)
        self.votes_for = {}

    def __repr__(self):
        return "{}()".format(self.__class__.__name__)

    def __str__(self):
        return "{0}({{{1}}})".format(
            self.__class__.__name__, 
            ", ".join(
                str(a) + "->" + str(b) 
                for a, b in self.votes_for.items()
            )
        )

    def respond_to_event(self, event):
        """Responds to ResetRequestEvent and VoteCastRequestEvent."""
        if isinstance(event, VoteBaseEvent) and event.tally is self:
            if isinstance(event, VoteTally.ResetRequestEvent):
                return VoteTally.ResetAction(self)
            elif isinstance(event, VoteTally.VoteCastRequestEvent):
                return VoteTally.DoVoteAction(self, event.source, event.target)

    class ResetRequestEvent(VoteBaseEvent):
        """Indicates that the vote tally should be reset.
        
        Parameters
        ----------
        tally : VoteTally
            The tally to reset.
        """
        def __init__(self, tally):
            super().__init__(tally=tally)

    class ResetAction(Action):
        """Action that resets the vote tally.
        
        Parameters
        ----------
        tally : VoteTally
            The tally to reset.
        """
        def __init__(self, tally):
            super().__init__()  # priority?
            self.tally = tally

        def _execute(self):
            self.tally._reset_tally()

    def _reset_tally(self):
        """Resets the vote tally, unconditionally.
        
        To do something useful, override this!
        """
        self.votes_for = {}

    class VoteCastRequestEvent(VoteBaseEvent):
        """Indicates that a vote has been cast.
            
        Parameters
        ----------
        tally : VoteTally
            The tally to cast the vote on.
        source, target : object
            The source votes for the target.
        """
        def __init__(self, tally, source, target):
            super().__init__(tally=tally)
            self.source = source
            self.target = target

    class DoVoteAction(Action):
        """Resets the vote tally.
        
        Parameters
        ----------
        tally : VoteTally
            The tally to cast the vote on.
        source, target : object
            The source votes for the target.
        """
        def __init__(self, tally, source, target):
            super().__init__()  # priority?
            self.tally = tally
            self.source = source
            self.target = target

        def _execute(self):
            self.tally._cast_vote(source=self.source, target=self.target)

    def _cast_vote(self, source, target):
        """Casts a vote from source to target."""
        self.votes_for[source] = target


# BELOW: IDK how to do this yet, but voting works.
# 


class VoteAction(Action):
    """"""

    def __init__(self, tally, source, target):
        self.tally = tally
        self.source = source
        self.target = target

    def _execute(self):
        pass  # Need to create a VoteCastRequestEvent somehow...   


class VoteAbility(ActivatedAbility):
    """Allows an actor to vote.
    
    Parameters
    ----------
    tally : VoteTally
        The tally the actor is allowed to vote in.
    """
    def __init__(self, tally):
        self.tally = tally

    # TODO: Add "do the vote thing" here.


# from mafia.core import GameObject  # , singleton
from mafia.core.event import InternalEvent, Subscriber, EventManager
from mafia.core.action import Action, PreActionEvent, PostActionEvent
from mafia.state.role import ActivatedAbility
from mafia.state.game import PhaseChangeAction
from mafia.premade.ability.kill import KillAction 


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

    Attributes
    ----------
    name : str
        Name of the tally.
    votes_for : dict
        Dictionary of {source: target} voting.
        If creating from scratch, leave this empty.
    voted_by : dict
        Dictionary of {target: [sources]} voting. (Property)
    vote_leaders : list
        List of targets with the most votes. (Property)

    Notes
    -----
    To extend this object, you can override :meth:`respond_to_event()` 
    and subscribe to other events. You may also want to override 
    :meth:`_cast_vote()` (for example, a list, for multi-voting) 
    or possibly :meth:`_reset_tally()`.
    """
    
    def __init__(self, name, votes_for={}):
        self.name = name
        EventManager.subscribe_me(
            self, 
            VoteTally.ResetRequestEvent, 
            VoteTally.VoteCastRequestEvent
        )
        self.votes_for = dict(votes_for)

    # Helper methods

    @property
    def voted_by(self):
        """Dict of {target: [sources]}"""
        res = {}
        for src, targ in self.votes_for.items():
            if targ not in res:
                res[targ] = []
            res[targ].append(src)
        return res

    @property
    def vote_leaders(self):
        """List of targets with the most votes."""
        res = []
        c_max = 0
        for targ, srcs in self.voted_by.items():
            if len(srcs) > c_max:
                c_max = len(srcs)
                res = [targ]
            elif len(srcs) == c_max:
                res.append(targ)
        return res

    # Responding to events

    def respond_to_event(self, event):
        """Responds to ResetRequestEvent and VoteCastRequestEvent."""
        if isinstance(event, VoteBaseEvent) and event.tally is self:
            if isinstance(event, VoteTally.ResetRequestEvent):
                return VoteTally.ResetAction(self)
            elif isinstance(event, VoteTally.VoteCastRequestEvent):
                return VoteTally.DoVoteAction(self, event.source, event.target)

    # Reset

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
        
        Attributes
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
        """Resets the vote tally, unconditionally."""
        self.votes_for = {}

    # Handle casting votes

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

    # Representation

    def __repr__(self):
        return "{}({}, votes_for={})".format(
            self.__class__.__name__, repr(self.name),
            repr(self.votes_for), 
        )

    def __str__(self):
        return "{0}[{1}]({{{2}}})".format(
            self.__class__.__name__, 
            self.name, 
            ", ".join(
                str(a) + "->" + str(b) 
                for a, b in self.votes_for.items()
            )
        )


class PhaseLimitedVoteTally(VoteTally):
    """A VoteTally that is limited to specific phases.
    
    Attributes
    ----------
    name : str
        Name of the tally.
    phases : list
        List of names of phases when this tally is active.
    votes_for : dict
        Dictionary of {source: target} voting.
        If creating from scratch, leave this empty.
    voted_by : dict
        Dictionary of {target: [sources]} voting. (Property)
    vote_leaders : list
        List of targets with the most votes. (Property)

    Notes
    -----
    To extend, override :meth:`_create_action()` (e.g. lynch a player).
    You can also override :meth:`respond_to_event()` and subscribe to 
    other events, but this probably isn't required.
    """

    def __init__(self, name, phases=[], votes_for={}):
        self.phases = list(phases) 
        super().__init__(name=name, votes_for=votes_for)
        EventManager.subscribe_me(
            self, PreActionEvent, PostActionEvent
        )

    def __repr__(self):
        return "{}({}, phases=[], votes_for={})".format(
            self.__class__.__name__, repr(self.name),
            repr(self.phases), repr(self.votes_for)
        )

    def _create_action(self):
        """Creates an Action based on current state.
        
        Override this!"""
        return None

    def respond_to_event(self, event):        
        if isinstance(event, PreActionEvent):
            if isinstance(event.action, PhaseChangeAction):
                # If this applies to us, process the vote
                ps = event.action.phase_state
                if ps.states[ps.current] in self.phases:
                    return self._create_action()
        elif isinstance(event, PostActionEvent):
            if isinstance(event.action, PhaseChangeAction):
                # If this applies to us, reset the vote
                ps = event.action.phase_state
                if ps.states[ps.current] in self.phases:
                    return VoteTally.ResetAction(self)
        # Other events
        super().respond_to_event(event)


class LynchAction(KillAction):
    """Represents the town lynch.

    Attributes
    ----------
    source : GameObject
        Who/what is killing; usually a :class:`LynchVoteTally`.
    target : GameObject
        Who/what is being killed; usually an :class:`Actor`). 
    """


class LynchVoteTally(PhaseLimitedVoteTally):
    """Phase-limited vote that leads to lynching the vote leader.

    In case of a tie, nobody is lynched.
    
    Attributes
    ----------
    name : str
        Name of the tally.
    phases : list
        List of names of phases when this tally is active.
    votes_for : dict
        Dictionary of {source: target} voting.
        If creating from scratch, leave this empty.
    voted_by : dict
        Dictionary of {target: [sources]} voting. (Property)
    vote_leaders : list
        List of targets with the most votes. (Property)

    Notes
    -----
    Default behavior is to no-lynch in case of a tie. 
    To change this, subclass and change :meth:`_decision_function`.
    """

    def _decision_function(self, leaders=[]):
        """Decides who to lynch out of the passed leaders.
        
        Default is to no-lynch in case of a tie.
        """
        if len(leaders) != 1:
            return None
        return leaders[0]

    def _create_action(self):
        """Creates an Lynch Action based on current state."""
        target = self._decision_function(self.vote_leaders)
        if target is None:
            return None
        return LynchAction(self, target)

# 


class VoteAction(Action):
    """Action that causes voting.
    
    Attributes
    ----------
    tally : VoteTally
        The vote tally to count on.
    source : GameObject
        Who/what is voting; usually an :class:`Actor`.
    target : GameObject
        Who/what is being voted for; usually an :class:`Actor`. 
    """

    def __init__(self, tally, source, target):
        self.tally = tally
        self.source = source
        self.target = target

    def _execute(self):
        """Creates and submits a VoteCastRequestEvent."""
        # VCRE = VoteTally.VoteCastRequestEvent
        VCRE = self.tally.VoteCastRequestEvent
        event = VCRE(self.tally, self.source, self.target)
        EventManager.handle_event(event)


class VoteAbility(ActivatedAbility):
    """Allows an actor to vote.
    
    Attributes
    ----------
    name : str
        Ability name (human-readable).
    tally : VoteTally
        The tally the actor is allowed to vote in.
    """

    def __init__(self, name, tally):
        super().__init__(name=name)
        self.tally = tally

    def activate(self, actor, target=None):
        print("voting from {} to {}".format(
            actor.name, getattr(target, 'name'))
        )
        # TODO: Add "do the vote thing" here.

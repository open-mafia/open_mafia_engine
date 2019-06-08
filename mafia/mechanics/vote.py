"""Voting mechanics module.

A :class:`VoteTally` keeps the votes (who voted for whom).
Typically this is used to decide who is lynched each day, however 
this is not always the case. 
"""

import typing
from mafia.util import ReprMixin
from mafia.core.ability import Action, ActivatedAbility, Restriction
from mafia.state.actor import Actor
from mafia.mechanics.kill import KillAction

import warnings


# from mafia.core.event import Subscriber
# from mafia.state.status import Status


class VoteTally(ReprMixin):
    """Object that handles voting.

    Parameters
    ----------
    name : str
        Name of the tally.
    votes_for : dict
        Dictionary of {source: target} voting.
        If creating from scratch, leave this empty.

    Attributes
    ----------
    voted_by : dict
        Dictionary of {target: [sources]} voting. (Property)
    vote_leaders : list
        List of targets with the most votes. (Property)
    """

    def __init__(self, name: str, votes_for: dict = {}):
        self.name = name
        self.votes_for = dict(votes_for)

    def __str__(self):
        # TODO: Maybe add compact representation?
        return f"{self.name}"

    def add_vote(self, source, target) -> None:
        """Adds a vote from source to target.
        
        By default, this removes any prior votes.
        
        Parameters
        ----------
        source : object
            Object that is voting, typically an :class:`Actor`.
        target : object
            Object that is being voted for.
        """
        self.votes_for[source] = target

    def remove_vote(self, source) -> None:
        """Removes (resets) all votes from source to anyone else.

        The result is for source to vote for nobody (removed from dict).
        
        Parameters
        ----------
        source : object
            Object to reset vote for, typically an :class:`Actor`.
        """
        del self.votes_for[source]

    def resolve(self) -> typing.Optional[Action]:
        """Resolves the vote tally.
        
        Override to have any practical use!
        
        Returns
        -------
        resolution : None or Action
            The action to run upon resolution.
        """
        return None

    @property
    def voted_by(self) -> typing.Dict[object, typing.List[object]]:
        """Dict of {target: [sources]}"""
        res = {}
        for src, targ in self.votes_for.items():
            if targ not in res:
                res[targ] = []
            res[targ].append(src)
        return res

    @property
    def vote_leaders(self) -> typing.List:
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


class VoteAction(Action):
    """Action that contitutes a vote.
    
    Attributes
    ----------
    tally : VoteTally
        The target state that will be changed.
    source : object
        The object that is voting.
    target : object or None
        The object being voted for. If None, resets source's vote.
    canceled : bool
        Whether the action is canceled. Default is False.
    """

    def __init__(self, tally: VoteTally, source, target=None, canceled: bool = False):
        if not isinstance(tally, VoteTally):
            raise TypeError(f"Expected VoteTally, got {type(tally)}")
        super().__init__(canceled=canceled)
        self.tally = tally
        self.source = source
        self.target = target

    def __execute__(self) -> bool:
        if self.canceled:
            return False

        if self.target is None:
            self.tally.remove_vote(self.source)
        else:
            self.tally.add_vote(self.source, self.target)
        return True


class VoteAbility(ActivatedAbility):
    """Ability to cast votes.
    
    Attributes
    ----------
    name : str
        Ability name (human-readable).
    owner : object
        The object that owns the ability. This will also be the source
    tally : VoteTally
        The vote tally that records this ability's votes.
    """

    def __init__(
        self,
        name: str,
        owner=None,
        restrictions: typing.List[Restriction] = [],
        tally: VoteTally = None,
    ):
        if not isinstance(tally, VoteTally):
            raise TypeError(f"tally should be a VoteTally, got {type(tally)}")
        super().__init__(name=name, owner=owner, restrictions=restrictions)
        self.tally = tally

    def is_legal(self, target=None) -> bool:
        """Check whether the vote ability usage is legal.

        The constructor prevents using this on a non-VoteTally. 
        You may want to override/extend this with stricter checks. 

        Parameters
        ----------
        target : object or None
            The target of the vote. If None, does removes all votes (unvote all).

        Returns
        -------
        can_use : bool
            Whether the ability usage is legal.
        """
        return super().is_legal(target=target)

    def activate(self, target=None) -> VoteAction:
        """Creates a VoteAction.
        
        If the activation is illegal, it will raise 
        an :class:`IllegalAbilityActivation` error.

        Parameters
        ----------
        target : object or None
            The target of the vote. If None, does removes all votes (unvote all).

        Returns
        -------
        action : VoteAction
            Resulting Action to put on the queue.

        Raises
        ------
        IllegalAbilityActivation
            If not `self.is_legal`.
        """
        super().activate(target=target)
        return VoteAction(tally=self.tally, source=self.owner, target=target)


class ResolveVotesAbility(ActivatedAbility):
    """Ability to resolve a VoteTally. Usually just given to the moderator.
    
    Attributes
    ----------
    tally : VoteTally
        The target state that will be changed.
    """

    def __init__(
        self,
        name: str,
        owner=None,
        restrictions: typing.List[Restriction] = [],
        tally: VoteTally = None,
    ):
        if not isinstance(tally, VoteTally):
            raise TypeError(f"tally should be a VoteTally, got {type(tally)}")
        super().__init__(name=name, owner=owner, restrictions=restrictions)
        self.tally = tally

    def is_legal(self) -> bool:
        """Check whether the phase change ability usage is legal.

        The constructor prevents using this on a non-VoteTally. 
        You may want to override/extend this with stricter checks. 

        Returns
        -------
        can_use : bool
            Whether the ability usage is legal.
        """
        return super().is_legal()

    def activate(self) -> Action:
        """Resolves the associated tally.
        
        If the activation is illegal, it will raise 
        an :class:`IllegalAbilityActivation` error.

        Returns
        -------
        action : Action
            Resulting Action to put on the queue.

        Raises
        ------
        IllegalAbilityActivation
            If not `self.is_legal`.
        """
        super().activate()
        return self.tally.resolve()


class LynchAction(KillAction):
    """Lynches a single target, then resets the tally.

    Parameters
    ----------
    source : LynchTally
        The vote tally that caused the lynch.
    target : Actor
        The target being killed.
    canceled : bool
        Whether the action is canceled. Default is False.

    Attributes
    ----------
    voted_for_target : list
        List of objects that voted for the target.
    """

    def __init__(self, source: VoteTally, target: Actor, canceled: bool = False):
        if not isinstance(source, LynchTally):
            raise TypeError(f"Expected LynchTally, got {type(source)}")
        super().__init__(source=source, target=target, canceled=canceled)

    @property
    def voted_for_target(self) -> typing.List:
        """List of objects that voted for the target."""

        tally = self.source
        try:
            return tally.voted_by[self.target]
        except KeyError:
            # This probably shouldn't happen...
            warnings.warn("Lynch target had no entry, but it was requested.")
            return []

    def __execute__(self) -> bool:
        kill_ok = super().__execute__()

        # NOTE: we still reset, even if the kill was stopped
        self.source.votes_for = {}

        if not kill_ok:
            warnings.warn("The lynch kill did not run, however tally was reset.")

        return True


class LynchTally(VoteTally):
    """Handles who voted for whom to be lynched.

    Parameters
    ----------
    name : str
        Name of the tally.
    votes_for : dict
        Dictionary of {source: target} voting.
        If creating from scratch, leave this empty.

    Attributes
    ----------
    voted_by : dict
        Dictionary of {target: [sources]} voting. (Property)
    vote_leaders : list
        List of targets with the most votes. (Property)
    """

    def resolve(self) -> typing.Optional[Action]:
        """Resolves the vote tally with a possible lynch.
        
        In case of a tie, no lynch is performed.
        
        Returns
        -------
        resolution : None or Action
            The action to run upon resolution.
        """
        leaders = self.vote_leaders

        if len(leaders) == 1:
            # Single vote leader, so we kill them
            return LynchAction(source=self, target=leaders[0])

        # Otherwise, we have a tie or no votes, so no lynch
        return None

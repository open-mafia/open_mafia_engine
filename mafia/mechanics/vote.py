"""Voting mechanics module.

A :class:`VoteTally` keeps the votes (who voted for whom).
Typically this is used to decide who is lynched each day, however 
this is not always the case. 
"""

import typing
from mafia.util import ReprMixin
from mafia.core.ability import Action, ActivatedAbility

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
    def voted_by(self) -> dict:
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
    """Ability to change phases. Usually just given to the moderator.
    
    Attributes
    ----------
    name : str
        Ability name (human-readable).
    owner : object
        The object that owns the ability. This will also be the source
    tally : VoteTally
        The vote tally that records this ability's votes.
    """

    def __init__(self, name: str, owner=None, tally: VoteTally = None):
        if not isinstance(tally, VoteTally):
            raise TypeError(f"tally should be a VoteTally, got {type(tally)}")
        super().__init__(name=name, owner=owner)
        self.tally = tally

    def is_legal(self, target=None) -> bool:
        """Check whether the phase change ability usage is legal.

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
        return True

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

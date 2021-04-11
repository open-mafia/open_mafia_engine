from collections import defaultdict
from typing import DefaultDict, List, Optional
import random

from pydantic import BaseModel

from open_mafia_engine.state.base import StateModel


class SingleVote(BaseModel):
    """A single vote, with a certain weight.

    TODO: Support "against everyone" votes?
    """

    source: str
    target: str
    weight: int = 1


class VoteTally(StateModel):
    """Vote tally, supporting weighted votes.

    TODO: Support votes "against everyone" and multi-voting.
    """

    votes: List[SingleVote] = []
    select_on_tie: bool = False

    @property
    def totals(self) -> DefaultDict[str, int]:
        """Returns the total votes for each ."""
        res = defaultdict(int)  # default is 0
        for v in self.votes:
            res[v.target] += v.weight
        return res

    @property
    def current_leaders(self) -> List[str]:
        """Returns the current vote leaders."""

        if len(self.votes) == 0:
            return []

        inv = defaultdict(list)
        for t, c in self.totals.items():
            inv[c].append(t)

        leaders = inv[max(inv.keys())]
        return leaders

    def select_leader(self) -> Optional[str]:
        """Selects one of the current leaders (or None)."""
        cl = self.current_leaders
        if len(cl) == 0:
            target = None
        elif len(cl) == 1:
            # Single vote-leader
            target = cl[0]
        else:
            # Tie
            if self.select_on_tie:
                target = random.choice(cl)
            else:  # Tie, but no lynch
                target = None
        return target

    def clear(self):
        """Removes all votes."""
        self.votes = []

    def unvote(self, source: str):
        """Removes all votes associated with the source."""
        uvs = [v for v in self.votes if v.source == source]
        for v in uvs:
            self.votes.remove(v)

    def add_vote(self, source: str, target: str, weight: int = 1):
        """Adds a vote, removing all previous votes by the source.

        TODO: Multi-voting?
        """
        self.unvote(source)
        self.votes.append(SingleVote(source=source, target=target, weight=weight))

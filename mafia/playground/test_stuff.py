"""Informal test of various systems

"""

# flake8: noqa

from mafia.core.event import EventManager, Subscriber, Action
from mafia.core.ability import (
    ActivatedAbility,
    TriggeredAbility,
    TryActivateAbility,
    IllegalAbilityActivation,
)
from mafia.state.actor import Alignment, Actor


class VoteAction(Action):
    """Fake vote action."""

    def __init__(self, source: Actor, target: Actor):
        self.source = source
        self.target = target

    def __execute__(self) -> bool:
        print("%s voted for %s" % (self.source.name, self.target.name))
        return True


class VoteAbility(ActivatedAbility):
    """Fake vote ability."""

    def is_legal(self, target: Actor):
        if not isinstance(target, Actor):
            return False
        return True

    def activate(self, target: Actor) -> VoteAction:
        super().activate(target=target)
        return VoteAction(self.owner, target)


em = EventManager()

with em:
    mafia = Alignment("mafia")
    town = Alignment("town")

    alice = Actor("Alice", alignments=[mafia], abilities=[VoteAbility("alice-vote")])
    bob = Actor("Bob", alignments=[town], abilities=[VoteAbility("bob-vote")])
    charlie = Actor("Charles", alignments=[town], abilities=[VoteAbility("c-vote")])

    def vote(src, trg):
        taa = TryActivateAbility(src.abilities[0], target=trg)
        em.handle_event(taa)


vote(alice, bob)  # this should work!

from typing import List, Optional, Union

from open_mafia_engine.converters.core import *
from open_mafia_engine.core.api import *
from open_mafia_engine.core.event_system import EPostAction, EPreAction

# Testing game state

game = Game()
town = Faction(game, name="Town")
mafia = Faction(game, name="Mafia")

alice = Actor(game, name="Alice")
a_abil = Ability(game, owner="Alice")
mafia.add_actor("Alice")
# mafia.add_actor(alice)  # also works

bob = Actor(game, name="Bob")
b_abil = Ability(game, owner="Bob")
# town.add_actor("Bob")  # also works
town.add_actor(bob)


# Testing events


class EFake(Event):
    """Fake event"""


class X1(Action):
    def doit(self):
        print("Doing X1")


class A(Subscriber):
    @handles(Event)
    def f(self, event: Event):
        print("f", self, event, sep=" | ")


class B(A):
    @handler
    def g(self, event: EFake) -> None:
        print("g", self, event, sep=" | ")


class C(Subscriber):
    @handles(EFake)
    def h1(self, event) -> List[X1]:
        return [X1(self.game)]

    @handler
    def h2(self, event: X1.Pre) -> List[Action]:
        print("h2: pre-action for X1")
        return []

    @handler
    def h3(self, event: X1.Post) -> None:
        print("h3: post-action for X1")

    # Also legal:
    # -> Union[List[Action], List[X1]]

    # Illegal handlers

    # @handles(Event)
    # def z1(self, event) -> Action:
    #     return Action(self.game)

    # @handles(Event)
    # def z2(self, event) -> Optional[Action]:
    #     return None


a = A(game)
b = B(game)
c = C(game)

e = EFake(game)

#

alice.status["hi"] = 1

# Normally process
game.process_event(e, process_now=True)

# What if we remove `c` from the subscriptions?
print("---- Removing subscriber c ----")
game.event_engine.remove_subscriber(c)
game.process_event(e, process_now=True)

#

game

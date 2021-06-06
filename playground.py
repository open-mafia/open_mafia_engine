from typing import List, Optional
from open_mafia_engine.core.api import *

from open_mafia_engine.converters.core import *

game = Game()
alice = Actor(game, name="Alice")
abil = Ability(game, owner="Alice")


class A(Subscriber):
    @handles(Event)
    def f(self, event: Event) -> Optional[List[Action]]:
        print("f", self, event)


class B(A):
    @handler
    def g(self, event: Event) -> Optional[List[Action]]:
        print("g", self, event)


class X1(Action):
    pass


a = A(game)
b = B(game)

e = Event(game)

X1.Pre

x1 = X1(game)
x1.pre()

# game.event_engine.broadcast(e)
game.process_event(e, process_now=True)

game

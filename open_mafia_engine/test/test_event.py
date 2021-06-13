from typing import List

from open_mafia_engine.builders.for_testing import make_test_game
from open_mafia_engine.core.event_system import (
    Action,
    Event,
    Subscriber,
    handler,
    handles,
)
from open_mafia_engine.core.state import EStatusChange


def test_events_and_subscribers():
    """General test of events and subscribers.

    Also makes sure order is deterministic.
    """

    actor_names = ["Alpha", "Bravo"]
    game = make_test_game(actor_names)

    log = []

    class EFake(Event):
        """Fake event"""

    class X1(Action):
        def doit(self):
            log.append("X1")

    class A(Subscriber):
        @handles(Event)
        def f(self, event: Event):
            log.append("A.f")

    class B(A):
        @handler
        def g(self, event: EFake) -> None:
            log.append("B.g")

    class C(Subscriber):
        @handles(EFake)
        def h1(self, event) -> List[X1]:
            log.append("C.h1")
            return [X1(self.game, self)]

        @handler
        def h2(self, event: X1.Pre) -> List[Action]:
            log.append("C.h2")
            return []

        @handler
        def h3(self, event: X1.Post) -> None:
            log.append("C.h3")

        # Also legal:
        # -> Union[List[Action], List[X1]]

        # Illegal handlers

        # @handles(Event)
        # def z1(self, event) -> Action:
        #     return Action(self.game, self)

        # @handles(Event)
        # def z2(self, event) -> Optional[Action]:
        #     return None

    a = A(game)
    b = B(game)
    c = C(game)

    e = EFake(game)
    game.process_event(e, process_now=True)

    assumed_log = [
        "B.g",
        "C.h1",
        "A.f",
        "A.f",
        "C.h2",
        "A.f",
        "A.f",
        "X1",
        "C.h3",
        "A.f",
        "A.f",
    ]
    assert log == assumed_log


def test_status_event():
    """Tests status change events."""

    actor_names = ["Alpha", "Bravo"]
    game = make_test_game(actor_names)

    log = []

    class Chk(Subscriber):
        @handler
        def f(self, event: EStatusChange):
            log.append(event.new_val)

    Chk(game)

    game.actors[0].status["key1"] = 2

    assert log == [2]

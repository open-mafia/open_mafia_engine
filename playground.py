from typing import List, Optional, Union

from open_mafia_engine.core.api import *


@game_builder("test")
def test_build(player_names: List[str]) -> Game:
    """Game builder for testing purposes."""

    N = len(player_names)
    assert N > 1

    game = Game()
    mafia = Faction(game, "Mafia")
    town = Faction(game, "Town")

    N_mafia = 1
    N_town = N - 1

    for i in range(N_mafia):
        act = Actor(game, player_names[i])
        mafia.add_actor(act)
        # TODO: Abilities

    for i in range(N_town):
        act = Actor(game, player_names[N_mafia + i])
        town.add_actor(act)
        # TODO: Abilities

    # Aux objects

    GameEnder(game)  # ends the game when all factions get an Outcome

    return game


# Testing game state

builder = GameBuilder.load("test")
game = builder.build(["Alice", "Bob"])

# Do fake stuff


def fake_action(self: Action):
    print("Fake action!")
    print(self.game.actor_names)


AcFake = Action.generate(fake_action, name="AcFake", doc="Fake action")
AbFake = Ability.generate(AcFake, name="AbFake", doc="Fake ability")


@Ability.generate
def AbFake2(self: Action):
    print("fake ability 2")
    print(self.game.actor)


a_abil = AbFake(game, owner="Alice", name="a_abil")
b_abil = AbFake2(game, owner="Bob", name="b_abil")

alice = game.actors[0]
bob = game.actors[1]

# Testing events

print("----- Test ability activation ----")
# game.process_event(EActivate(game, a_abil), process_now=True)
game.process_event(EActivate(game, "Alice/ability/a_abil"), process_now=True)


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

# Normally process
print("---- Testing subscribers ----")
game.process_event(e, process_now=True)

# What if we remove `c` from the subscriptions?
print("---- Removing subscriber c ----")
game.event_engine.remove_subscriber(c)
game.process_event(e, process_now=True)

#
print("---- Changing Alice's status ----")
alice.status["hi"] = 1

game

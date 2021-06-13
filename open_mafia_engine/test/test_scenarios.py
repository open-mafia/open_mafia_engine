"""Tests for various longer scenarios."""

from open_mafia_engine.core.all import *
from open_mafia_engine.built_in.all import *
from open_mafia_engine.builders.all import *


def test_example_1():
    """"""
    builder = GameBuilder.load("test")
    game = builder.build(["Alice", "Bob", "Charlie"])

    alice, bob, charlie = game.actors
    tally: Tally = game.aux.filter_by_type(Tally)[0]

    # Alice: Vote, Mafia Kill
    # Bob: Vote
    # Charlie: Vote, Protect

    # STARTUP
    # nothing yet
    game.change_phase()

    # DAY 1
    game.process_event(EActivate(game, "Alice/ability/Vote", target="Bob"))
    game.process_event(EActivate(game, "Bob/ability/Vote", target="Alice"))

    game.change_phase()
    assert not any(x.status["dead"] for x in game.actors)  # no-lynch, nobody dies

    # NIGHT 1
    # Mafia Alice tries to kill Bob
    game.process_event(EActivate(game, "Alice/ability/Mafia Kill", target=bob))
    # ... but Charlie protected bob, which has higher priority
    game.process_event(EActivate(game, "Charlie/ability/Protect", target=bob))

    # DAY 2
    game.change_phase()  # process the night phase - nobody died
    assert not bob.status["dead"]

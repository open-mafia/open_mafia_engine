"""Tests for various longer scenarios."""

from open_mafia_engine.core.all import *
from open_mafia_engine.built_in.all import *
from open_mafia_engine.builders.all import *


def test_scenario_1():
    """Tests a scenario where lots of night roles are at play."""

    builder = GameBuilder.load("test")
    game = builder.build(["Alice", "Bob", "Charlie", "Dave", "Emily"], n_mafia=1)

    alice, bob, charlie, dave, emily = game.actors[:5]
    tally: Tally = game.aux.filter_by_type(Tally)[0]

    # Alice: Vote, Mafia Kill
    # Bob: Vote
    # Charlie: Vote, Protect
    # Dave: Vote, Inspect
    res_key = FactionInspectAction.status_key()

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
    # Dave inspects Alice
    game.process_event(EActivate(game, "Dave/ability/Faction Inspect", target=alice))
    # ... but is redirected by Emily to Charlie, and so inspects as Town!
    game.process_event(
        EActivate(game, "Emily/ability/Redirect", target=dave, new_target=charlie)
    )

    game.change_phase()  # process the night phase

    # nobody died
    assert not bob.status["dead"]
    assert not any(x.status["dead"] for x in game.actors)

    # Dave got 1 result, but they got redirected! They think Alice is Town.
    dave_n1_results = dave.status[res_key]
    assert isinstance(dave_n1_results, list)
    assert len(dave_n1_results) == 1
    assert "town" in dave_n1_results[0].lower()

    # DAY 2

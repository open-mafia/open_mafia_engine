from open_mafia_engine.built_in.voting import Tally
from open_mafia_engine.core.state import EActivate
from open_mafia_engine.builders.for_testing import make_test_game

def test_activation_by_event():
    """Tests activation via events, directly or via converters."""

    game = make_test_game(["Alice", "Bob"])
    alice = game.actors[0]
    bob = game.actors[1]

    a_v = alice.abilities[0]  # VoteAbility(game, owner=alice, name="Vote")
    b_v = bob.abilities[0]  # VoteAbility(game, owner=bob, name="Vote")

    tally: Tally = game.aux.filter_by_type(Tally)[0]
    game.process_event(EActivate(game, a_v, target=bob), process_now=True)
    assert tally.results.vote_leaders == [bob]
    game.process_event(
        EActivate(game, "Alice/ability/Vote", target="unvote"), process_now=True
    )
    assert tally.results.vote_leaders == []

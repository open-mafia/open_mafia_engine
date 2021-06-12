from open_mafia_engine.built_in.voting import Tally
from open_mafia_engine.core.event_system import Action
from open_mafia_engine.core.state import Ability, EActivate
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


def test_gen_action_ability():
    """Tests action and ability generation."""

    actor_names = ["Alpha", "Bravo"]

    def fake_action(self: Action):
        assert self.game.actor_names == actor_names

    AcFake = Action.generate(fake_action, name="AcFake", doc="Fake action")
    AbFake = Ability.generate(AcFake, name="AbFake", doc="Fake ability")

    @Ability.generate
    def AbFake2(self: Action):
        """fake ability 2"""
        assert self.game.actor_names == actor_names

    game = make_test_game(actor_names)

    a_abil = AbFake(game, owner=game.actors[0], name="a_abil")
    a_abil.activate()

    b_abil = AbFake2(game, owner="Bravo", name="b_abil")
    b_abil.activate()
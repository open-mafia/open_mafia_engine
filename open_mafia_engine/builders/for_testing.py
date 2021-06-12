from typing import List

from open_mafia_engine.built_in.all import *
from open_mafia_engine.core.all import *


@game_builder("test")
def make_test_game(player_names: List[str], n_mafia: int = 1) -> Game:
    """Game builder for testing purposes.

    Always assigns mafia, then non-mafia, in player name order.
    """

    n = len(player_names)
    assert isinstance(n_mafia, int)
    assert n_mafia > 0
    assert n > n_mafia

    game = Game()
    mafia = Faction(game, "Mafia")
    town = Faction(game, "Town")

    # Aux objects
    GameEnder(game)  # ends the game when all factions get an Outcome
    tally = LynchTally(game)  # voting tally; TODO lynch tally

    n_town = n - 1

    for i in range(n_mafia):
        act = Actor(game, player_names[i])
        mafia.add_actor(act)
        # Voting
        vote = VoteAbility(game, act, name="Vote", tally=tally)
        PhaseConstraint(game, vote, phase="day")
        # Mafia kill
        mk = KillAbility(game, act, name="Mafia Kill")
        LimitPerPhaseKeyConstraint(game, mk, key="mafia_kill_limit")
        PhaseConstraint(game, mk, phase="night")

    for i in range(n_town):
        act = Actor(game, player_names[n_mafia + i])
        town.add_actor(act)
        # Voting
        vote = VoteAbility(game, act, name="Vote", tally=tally)
        PhaseConstraint(game, vote, phase="day")
        # TODO: Other abilities

    return game

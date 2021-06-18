from typing import List

from open_mafia_engine.built_in.all import *
from open_mafia_engine.core.all import *


@game_builder("test")
def make_test_game(player_names: List[str], n_mafia: int = 1) -> Game:
    """Game builder for testing purposes.

    Always assigns mafia, then non-mafia, in player name order.
    Must be at least 2 players (1 mafia, 1 town).

    Parameters
    ----------
    n_mafia : int = 1
        How many mafia players to add.
    """

    n_mafia = int(n_mafia)

    n = len(player_names)
    assert isinstance(n_mafia, int)
    assert n_mafia > 0
    assert n > n_mafia

    game = Game()
    mafia = Faction(game, "Mafia")
    OCLastFactionStanding(game, mafia)
    town = Faction(game, "Town")
    OCLastFactionStanding(game, town)

    # Aux objects
    GameEnder(game)  # ends the game when all factions get an Outcome
    tally = LynchTally(game)  # lynch tally

    n_town = n - 1

    for i in range(n_mafia):
        act = Actor(game, player_names[i])
        mafia.add_actor(act)
        # Voting
        vote = VoteAbility(game, act, name="Vote", tally=tally)
        PhaseConstraint(game, vote, phase="day")
        # Mafia kill
        mk = KillAbility(game, act, name="Mafia Kill")
        LimitPerPhaseActorConstraint(game, mk, limit=1)
        LimitPerPhaseKeyConstraint(game, mk, key="mafia_kill_limit")
        PhaseConstraint(game, mk, phase="night")
        ConstraintNoSelfFactionTarget(game, mk)
        if i == 2:
            # Second mafioso can roleblock
            block = RoleBlockAbility(game, act, name="Roleblock")
            PhaseConstraint(game, block, phase="night")
            LimitPerPhaseActorConstraint(game, block, limit=1)
            ConstraintNoSelfFactionTarget(game, block)

    for i in range(n_town):
        act = Actor(game, player_names[n_mafia + i])
        town.add_actor(act)
        # Voting
        vote = VoteAbility(game, act, name="Vote", tally=tally)
        PhaseConstraint(game, vote, phase="day")
        if i == 1:
            # Second townie is a protector/doctor
            prot = KillProtectAbility(game, act, name="Protect")
            PhaseConstraint(game, prot, phase="night")
            LimitPerPhaseActorConstraint(game, prot, limit=1)
            ConstraintNoSelfTarget(game, prot)
        elif i == 2:
            # Third townie is a detective
            insp = FactionInspectAbility(game, act, name="Faction Inspect")
            LimitPerPhaseActorConstraint(game, insp, limit=1)
            PhaseConstraint(game, insp, phase="night")
            ConstraintNoSelfTarget(game, insp)
            pass
        elif i == 3:
            # Fourth townie is a redirector
            redir = CreateRedirectAbility(game, act, name="Redirect")
            LimitPerPhaseActorConstraint(game, redir, limit=1)
            PhaseConstraint(game, redir, phase="night")
        # TODO: Other abilities

    return game

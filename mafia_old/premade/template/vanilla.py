"""Vanilla, or Mountainous, Mafia games. 

These typically have 
"""

# from mafia.core.event import EventManager
import random
from mafia.state.role import Role
from mafia.state.actor import Actor, Alignment

# from mafia.state.actor import ActorControlEvent
from mafia.state.game import GameState, PhaseState
from mafia.premade.ability.vote import VoteAbility, VoteTally, LynchVoteTally
from mafia.premade.ability.kill import KillAbility


class VanillaGame(GameState):
    """Vanilla game with only Mafia and Town players.
    
    Attributes
    ----------
    alignments : list
        Alignments used: town and mafia.
    vote_tally : VoteTally
        Object which keeps the vote.
    """

    def __init__(self, phase_state=[], alignments=[], vote_tally=None):
        if not isinstance(vote_tally, VoteTally):
            raise TypeError("vote_tally must be a VoteTally, got %r" % vote_tally)
        self.vote_tally = vote_tally
        super().__init__(phase_state=phase_state, alignments=alignments)

    @classmethod
    def generate(cls, players, n_mafia=None, mafia_name="mafia", town_name="town"):
        """Generates a random Vanilla game.
        
        Parameters
        ----------
        players : list or int
            Player names to assign. If int, gives a range of names. 
        n_mafia : None or int or float
            Quantity or portion of players that are assigned Mafia. 
            If None, uses floor(sqrt(# players) approximation of fairness. 
        mafia_name, town_name : str
            Names to use for town, mafia teams.

        Returns
        -------
        VanillaGame
        """

        # Create list of players and shuffle them
        try:
            players = list(players)
        except Exception:
            players = ["Player_%s" % k for k in range(players)]
        random.shuffle(players)

        N = len(players)

        if n_mafia is None:
            # Approx
            n_mafia = int(N ** 0.5)
        elif n_mafia < 1:
            # Portion
            n_mafia = int(N * n_mafia)

        # Create base objects
        vote_tally = LynchVoteTally("daily-lynch-tally", phases=["day"])
        align_town = Alignment(town_name)
        align_mafia = Alignment(mafia_name)

        for i, player in enumerate(players):
            abils = [VoteAbility("lynch-vote", tally=vote_tally)]

            if i < n_mafia:
                abils += [KillAbility("mafia-kill")]  # TODO: Add NightKill
                align = align_mafia
            else:
                align = align_town

            # Create Actor
            z = Actor(name=player, alignment=align, role=Role(abils), status={})
            z

        res = cls(
            phase_state=PhaseState(["day", "night"]),
            alignments=[align_town, align_mafia],
            vote_tally=vote_tally,
        )
        return res
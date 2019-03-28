from typing import List
from fastapi import APIRouter, HTTPException

from mafia.premade.template.vanilla import VanillaGame 
from mafia.core.event import EventManager
from mafia.state.actor import ActorControlEvent
# import multiprocessing as mp 
import random


class MafiaAPI(APIRouter):

    @classmethod
    def generate(cls, players=5):
        vg = VanillaGame.generate(players)
        ex = cls(vg)
        return ex
    
    def __init__(self, game):
        super().__init__()

        self.game = game

        # Status
        self.get("/")(self.root)
        self.get("/players", response_model=List[str])(self.list_players)
        self.get("/players/all", response_model=List[dict])(
            self.get_players_info_all)
        self.get("/players/{player_name}", response_model=dict)(
            self.get_player_info)
        self.get("/game", response_model=dict)(self.get_game_status)

        # Action
        self.post("/next-phase")(self.apply_next_phase)
        self.post("/ability/{source}")(self.apply_ability)
        self.post("/random/vote")(self.apply_vote_random)
        self.post("/random/mkill")(self.apply_mkill_random)
        
    def root(self):
        """Gets the API version."""
        return {'api-version': 0.1}

    def get_game_status(self):
        """Returns dict of phase, alignments, votes."""
        g = self.game 
        res = {
            'phase': g.phase_state.states[g.phase_state.current], 
            'alignments': [a.name for a in g.alignments],
            'vote_tally': {
                k.name: v.name
                for k, v in g.vote_tally.votes_for.items()
            }, 
        }
        return res

    def list_players(
        self, player_name: str = None, team_name: str = None, 
        alive: bool = None,
    ):
        """Returns list of players. Filters by name or team name."""

        def filt(a):
            Q = True
            if player_name is not None:
                Q = Q & (a.name.lower() == player_name.lower())
            if alive is not None:
                Q = Q & (a.status['alive'] == alive)
            return Q
                
        z = self._list_players(team=team_name, filt=filt)
        return [a.name for a in z]     

    def list_alive(self, team_name: str = None):
        """Returns list of players (names) that are alive."""
        return self.list_players(
            team=team_name, 
            filt=lambda ac: ac.status['alive']
        )

    def _list_players(self, team=None, filt=None):
        """Returns (filtered) list of players. 

        Internal function (not exposed as API).
        
        Parameters
        ----------
        team : None or str
            The Alignment to filter on.
        filt : None or callable
            Boolean function with argument :class:`Actor`.
        """
        if team is None:
            pool = self.game.actors
        else:
            pool = [
                al for al in self.game.alignments
                if al.name == team
            ][0].members

        if filt is None:
            def filt(x):
                return True

        act_alive = [
            ac for ac in pool
            if filt(ac)
        ]
        return act_alive

    def get_player_info(self, player_name: str):
        """Returns info for a single player, by their name."""

        found = [
            a for a in self.game.actors 
            if a.name.lower() == player_name.lower()
        ]
        if len(found) == 0:
            raise HTTPException(404, "No such player.")
        if len(found) > 1:
            raise HTTPException(400, "Ambiguous name.")

        act = found[0]
        aligns_names = [
            al.name for al in self.game.alignments 
            if act in al.members
        ]
        res = {
            'name': act.name, 
            'alignments': aligns_names, 
            'abilities': [abil.name for abil in act.role.abilities], 
            'status': dict(act.status),
        }
        return res

    def get_players_info_all(self):
        """Gets information for all players."""
        return [self.get_player_info(a.name) for a in self.game.actors]

    def get_winning_team(self):
        """Returns name of winning team, or None if no winner."""

        if len(self.list_alive(team='town')) == 0:
            return 'mafia'
        
        if len(self.list_alive(team='mafia')) == 0:
            return 'town'
        
        return None

    def apply_next_phase(self):
        """Bumps the phase."""
        next(self.game.phase_state)

    def apply_ability(self, source: str, ability_name: str, target: str):
        """Applies source's ability with given name to target."""

        source_actor = [
            ac for ac in self.game.actors
            if ac.name.lower() == source.lower()
        ][0]
        target_actor = [
            ac for ac in self.game.actors
            if ac.name.lower() == target.lower()
        ][0]

        ability = [
            a for a in source_actor.role.abilities 
            if a.name.lower() == ability_name.lower()
        ][0]
        
        ace = ActorControlEvent(source_actor, ability, target=target_actor)
        EventManager.handle_event(ace)

    def apply_vote_random(self):
        """Adds a random vote."""

        ability_name = 'lynch-vote'
        source, target = random.choices(self.list_alive(), k=2)
        self.apply_ability(source, ability_name, target)

    def apply_mkill_random(self):
        """Adds a random Mafia kill."""

        ability_name = 'mafia-kill'
        source = random.choice(self.list_alive(team='mafia'))
        target = random.choice(self.list_alive(team='town'))
        self.apply_ability(source, ability_name, target)

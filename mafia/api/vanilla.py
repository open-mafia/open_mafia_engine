# TODO: Force games to provide their own API, maybe?

from mafia.premade.template.vanilla import VanillaGame 
from mafia.core.event import EventManager
from mafia.state.actor import ActorControlEvent
# import multiprocessing as mp 
import random


class VanillaExecutor(object):
    """Temporary main engine API object thing?"""
    
    @classmethod
    def generate(cls, players=5):
        vg = VanillaGame.generate(players)
        ex = cls(vg)
        return ex

    def __init__(self, game):
        self.game = game

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

    def _list_players(self, team=None, filt=None):
        """Returns (filtered) list of players. 
        
        If `team` is specified, filters by team name.
        filt : <Actor> -> bool
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

    def list_players(self, team=None, filt=None):
        """Returns (filtered) list of players. 
        
        If `team` is specified, filters by team name.
        filt : <Actor> -> bool
        """
        z = self._list_players(team=team, filt=filt)
        return [a.name for a in z] 

    def list_alive(self, team=None):
        """Returns list of alive players. 
        
        If `team` is specified, filters by team name.
        """
        return self.list_players(team=team, filt=lambda ac: ac.status['alive'])

    def get_player_info(self, name):
        """Gets information for one player."""
        act = [a for a in self.game.actors if a.name == name][0]
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

    def get_players_info(self):
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

    def apply_ability(self, abil, src, trg):
        """Applies src's ability with given name to trg."""

        source = [
            ac for ac in self.game.actors
            if ac.name == src
        ][0]
        target = [
            ac for ac in self.game.actors
            if ac.name == trg
        ][0]

        ability = [
            a for a in source.role.abilities 
            if a.name == abil
        ][0]
        
        ace = ActorControlEvent(source, ability, target=target)
        EventManager.handle_event(ace)

    def apply_vote_random(self):
        """Adds a random vote."""

        abil = 'lynch-vote'
        src, trg = random.choices(self.list_alive(), k=2)
        self.apply_ability(abil, src, trg)

    def apply_mkill_random(self):
        """Adds a random Mafia kill."""

        abil = 'mafia-kill'
        src = random.choice(self.list_alive(team='mafia'))
        trg = random.choice(self.list_alive(team='town'))
        self.apply_ability(abil, src, trg)
        

# 

"""Alternative CLI app (non-fullscreen).

Far from being implemented.
"""


import sys
import requests
from prompt_toolkit import (
    PromptSession, print_formatted_text as print, 
)
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator

from multiprocessing import Process

from mafia.api.main import main as api_main


class CliApp(object):
    """"""

    def __init__(self):
        api_args = [
            '--host', 'localhost', 
            '--port', '8000', 
            '--log_level', 'warning',
        ]
        self.api_process = Process(
            target=api_main, args=[api_args], daemon=True)
        self.api_process.start()

    @property
    def base_url(self):
        return "http://localhost:8000"

    @property
    def game_status(self):
        return requests.get(self.base_url + '/game').json()

    @property
    def game_started(self):
        return self.game_status['started']

    @property
    def game_phase(self):
        return self.game_status['phase']

    @property
    def game_winner(self):
        try:
            return requests.get(self.base_url + '/game/winner').json()
        except Exception:
            return None

    def main(self, args=None):
        """Main loop."""
        if args is None:
            args = sys.argv[1:]

        while True:
            try:
                if self.game_started:
                    options = ['game', 'quit', ]
                else:
                    options = ['lobby', 'game', 'quit', ]

                p = PromptSession(
                    message="> ",
                    completer=WordCompleter(options),            
                    validator=Validator.from_callable(lambda x: x in options),
                )
                print("\n")
                print(options)
                r = p.prompt()
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            else:
                if r == 'quit':
                    return
                elif r == 'lobby':
                    self.m_lobby()
                elif r == 'game':
                    self.m_game()
                else:
                    print(r)

    def m_lobby(self):
        """Lobby menu."""

        options = ['back', 'add', 'remove']

        url = self.base_url + '/lobby'

        p = PromptSession(
            message="\n" "lobby > ",
            completer=WordCompleter(options),            
            validator=Validator.from_callable(lambda x: x in options),
        )
        while True:
            try:
                players = requests.get(url).json()
                print("\n")
                print("Current lobby:", players)
                print("Options:", options)
                r = p.prompt()
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            else:
                if r == 'back':
                    return
                elif r == 'add':
                    p_add = PromptSession(
                        message="name: ", 
                        validator=Validator.from_callable(
                            lambda x: x.lower() not in players
                        )
                    )
                    to_add = p_add.prompt().lower().split()
                    for name in to_add:
                        requests.post(
                            url + '/add?player_name={}'.format(name)
                        )
                elif r == 'remove':
                    p_rem = PromptSession(
                        message="name: ",
                        completer=WordCompleter(players),            
                        validator=Validator.from_callable(
                            lambda x: x.lower() in players + ['']
                        ),
                    )
                    to_remove = p_rem.prompt().lower().split()
                    for name in to_remove:
                        requests.post(
                            url + '/remove?player_name={}'.format(name)
                        )
                else:
                    print(r)

    def print_player_info(self):
        all_info = requests.get(
            self.base_url + '/players/all'
        ).json()
        for pi in all_info:
            z = "{nm} {team} - {alive} | {abils}".format(
                nm=pi['name'], team=pi['alignments'],
                alive=('ALIVE' if pi['status']['alive'] else 'DEAD'),
                abils=pi['abilities'],
            )
            print(z)

    def m_game(self):
        url = self.base_url + '/game'

        while True:
            try:
                print("\n")                

                if self.game_started:
                    winner = self.game_winner
                    if winner:
                        print("Winning team:", winner)
                        w_players = requests.get(
                            self.base_url 
                            + '/players?team_name={}'.format(winner)
                        ).json()
                        print("Winning players:", [p for p in w_players])
                    
                        options = ['back', 'players', 'end']
                    else:  # game in progress
                        print("Phase:", self.game_phase)
                        options = [
                            'back', 'next-phase', 
                            'players', 'ability', 
                            'end',
                        ]
                else:  # need to start game
                    print("Not started.")
                    options = ['back', 'start']

                p = PromptSession(
                    message="game > ",
                    completer=WordCompleter(options),            
                    validator=Validator.from_callable(lambda x: x in options),
                )
                    
                print("Options:", options)
                r = p.prompt()
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            else:
                if r == 'back':
                    return
                elif r == 'start':
                    requests.post(url + '/start')
                elif r == 'end':
                    requests.post(url + '/end')
                elif r == 'next-phase':
                    self.bump_phase()
                elif r == 'players':
                    self.print_player_info()
                elif r == 'ability':
                    self.m_ability()                    
                else:
                    print(r)

    def bump_phase(self):
        """Bumps to the next phase."""
        requests.post(self.base_url + '/game/next-phase')

    # def get_players(self, team=None, alive=None):

    def m_ability(self):
        url = self.base_url + '/ability'

        while True:
            try:
                if not self.game_started:
                    return

                if self.game_winner:
                    print("\n")
                    print("Game finished! Winner:", self.game_winner)
                    return

                phase = self.game_phase

                alive_players = requests.get(
                    self.base_url + '/players?alive=True'
                ).json()

                options = ['back', 'random', 'next-phase']

                if phase == 'day':
                    active_players = alive_players
                    active_abil = 'lynch-vote'
                else:  # night
                    active_players = requests.get(
                        self.base_url + '/players?alive=True&team_name=mafia'
                    ).json()
                    active_abil = 'mafia-kill'

                p = PromptSession(
                    message="players > ",
                    completer=WordCompleter(options + active_players),            
                    validator=Validator.from_callable(
                        lambda x: x.lower() in options + active_players),
                )
                    
                print("\n")
                print("Phase:", phase)
                print("Alive Players:", alive_players)
                print("Active Players:", active_players)
                print("Ability:", active_abil)
                if phase == 'day':
                    print("Votes:", self.game_status['vote_tally'])
                print("Options:", options + active_players)

                r = p.prompt().lower()
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            else:
                if r == 'back':
                    return
                elif r == 'next-phase':
                    self.bump_phase()
                elif r == 'random':
                    if phase == 'day':
                        requests.post(url + '/random/vote')
                    else:
                        requests.post(url + '/random/mkill')
                        self.bump_phase()
                else:
                    targ = PromptSession(
                        message="target: ",
                        completer=WordCompleter(alive_players),            
                        validator=Validator.from_callable(
                            lambda x: x.lower() in alive_players),
                    ).prompt()
                    requests.post(
                        url + '/{}?ability_name={}&target={}'.format(
                            r, active_abil, targ
                        )
                    )
                    if phase == 'night':
                        self.bump_phase()

              
#


if __name__ == "__main__":
    app = CliApp()
    app.main()

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
                    to_add = p_add.prompt().lower()
                    if to_add != '':
                        requests.post(
                            url + '/add?player_name={}'.format(to_add)
                        )
                elif r == 'remove':
                    p_rem = PromptSession(
                        message="name: ",
                        completer=WordCompleter(players),            
                        validator=Validator.from_callable(
                            lambda x: x.lower() in players + ['']
                        ),
                    )
                    to_remove = p_rem.prompt().lower()
                    if to_remove != '':
                        requests.post(
                            url + '/remove?player_name={}'.format(to_remove)
                        )
                else:
                    print(r)

    def m_game(self):
        url = self.base_url + '/game'

        while True:
            try:
                print("\n")                
                print("Status:", self.game_status)

                if self.game_started:
                    winner = self.game_winner
                    if winner:
                        print("Winning team:", winner)
                        w_players = requests.get(
                            self.base_url 
                            + '/players?team_name={}'.format(winner)
                        ).json()
                        print("Winning players:", [p for p in w_players])
                    
                        options = ['back', 'end']
                    else:  # game in progress
                        options = [
                            'back', 'next-phase', 
                            'players', 'ability', 
                            'end',
                        ]
                else:  # need to start game
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
                    requests.post(url + '/next-phase')
                elif r == 'players':
                    self.m_players()                    
                elif r == 'ability':
                    self.m_ability()
                else:
                    print(r)

    def m_players(self):
        pass

    def m_ability(self):
        pass


if __name__ == "__main__":
    app = CliApp()
    app.main()

from open_mafia_engine.core.game import *
from open_mafia_engine.core.game_object import *

from open_mafia_engine.converters.basic import *

game = Game()
Actor(game, name="Alice")
Ability(game, owner="Alice")

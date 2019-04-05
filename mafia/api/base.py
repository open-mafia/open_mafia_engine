from fastapi import APIRouter
from pydantic import BaseModel


class User(BaseModel):
    """Base API user class."""
    username: str


class MafiaAPI(APIRouter):
    """API router for a Mafia game.
    
    The API is from the point of view of a particular user. 
    Users need to be able to view/discover information ('get' requests) 
    and perform actions ('post' requests). This maps very well to REST. 

    If the user is a player, they are only aware of information that 
    is available to them "in-game". They can only act from their role.

    If the user is a moderator, they are aware of the entire game state. 
    They can act from any role (e.g. impersonating the user), and they 
    can also "operate" the game (e.g. changing phases, replacing or 
    mod-killing players, performing Acts of God, ...). 
    
    TODO
    ----

    * Create lobby system for users.
    * Attach games, assign Actors to players.
    * Add game info discoverability (e.g. existing alignments, alive players).
    * Add user info discoverability (e.g. self role, ally's role).
    * Add action creation.
    """

    # Players and Moderator
    #  get lobby info: /lobby/...
    #  get game info: /game/...
    #  get user (actor) info: /user/{username|'me'}/role/ alignment, actions, ...
    #  post action: /user/{username|'me'}/action/{action_name}?target={ABC}

    # Moderator only
    #  post game action: /game/action/ game-start, phase-change, game-end, ...
    #  post lobby action: /lobby/action/ replace-player, ...

"""Test the RestAPI for the game."""

import uvicorn
from mafia.playground.test_stuff import game
from mafia.api.rest import RestAPI

app = RestAPI(game)

if __name__ == "__main__":
    uvicorn.run(app)

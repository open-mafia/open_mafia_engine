# Open Mafia Engine

The Open Mafia Engine is a flexible, open-source game engine for Mafia-like games.

See the [Wikipedia article](https://en.wikipedia.org/wiki/Mafia_%28party_game%29)
for information on what Mafia/Werewolf is.

The Open Mafia Engine actually allows a much broader type of game to be played,
with custom roles and very intricate "setups". Most of these custom roles come
from either "real-life" games or online forums such as
[MafiaScum](https://wiki.mafiascum.net/index.php?title=Main_Page) and
[Bay12Games Mafia Subforum](http://www.bay12forums.com/smf/index.php?board=20.0).

## Features

- Event-based architecture, which allows for very complex interactions.
- Many built-in abilities, victory conditions, etc.
  (This is a lie, but we're working on it!)
- YAML `Prefab`s let you define a game in a (mostly) human-readable fashion.
- Open source & extensible, with a plugin system in the works.

## Installing

Install the latest stable version via pip:

`pip install open_mafia_engine`

See the [dev docs](development/installing_dev.md) to install for local
development (using Poetry).

## Getting started

This example starts a 5-player "vanilla" mafia game (1 mafioso vs 4 townies):

```python
from open_mafia_engine.api import Prefab

prefab = Prefab.load("Vanilla")
players = ['Alice', 'Bob', 'Charlie', 'Dave', 'Eddie']
game = prefab.create_game(players)
```

Actually running commands in the engine is pretty complicated for now.
We're working to improve the experience.

See `playground.py` in the repository for an example game.

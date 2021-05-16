# Open Mafia Engine

The Open Mafia Engine is a flexible, open-source game engine

## Features

- Event-based architecture, which allows for very complex interactions.
- Many built-in abilities, victory conditions, etc.
- YAML `Prefab`s let you define a game in a (mostly) human-readable fashion.
- Open source & extensible, with a plugin system in the works.

## Installing

It should be pretty easy to install:

`pip install open_mafia_engine`

## Getting started

This example starts a 5-player "vanilla" mafia game (1 mafioso vs 4 townies):

```python
from open_mafia_engine.api import Prefab

prefab = Prefab.load("Vanilla Mafia")
players = ['Alice', 'Bob', 'Charlie', 'Dave', 'Eddie']
game = prefab.create_game(players)
```

Actually running commands in the engine is pretty complicated for now.
We're working to improve that experience.

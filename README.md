# Open Mafia Engine

The Open Mafia Engine is a flexible, open-source game engine

## Features

- Event-based architecture, which allows for very complex interactions.
- Many built-in abilities, victory conditions, etc.
- YAML `Prefab`s let you define a game in a (mostly) human-readable fashion.
- Open source & extensible, with a plugin system in the works.

## Installing

### From PyPI

It should be pretty easy to install a stable version:

`pip install open_mafia_engine`

### For development

Development is done via [Poetry](https://python-poetry.org/), which is a
packaging and dependency management tool.

#### Poetry

[Install poetry](https://python-poetry.org/docs/#installation)

Clone the repo and install everything via poetry:

`git clone https://github.com/open-mafia/open_mafia_engine.git`

`poetry install`

This should become easier when [PEP 660](https://www.python.org/dev/peps/pep-0660/)
is implemented (will just be `pip install -e .`)

#### Conda

If you use `conda`, you can install `poetry` in any virtual environment:

`conda activate YOUR_ENV_NAME`

`conda install -c conda-forge poetry`

Then clone and install:

`git clone https://github.com/open-mafia/open_mafia_engine.git`

`poetry install`

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

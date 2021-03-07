# Welcome to MkDocs

For full documentation visit [mkdocs.org](https://www.mkdocs.org).

To get started:

```python
from open_mafia_engine.state.game import GameState

game = GameState.from_prefab(
    names=['Alice', 'Bob', 'Charlie', 'Dave', 'Eddie'], 
    prefab="Vanilla Mafia",
)
```

## Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

```bash
mkdocs.yml    # The configuration file.
docs/
    index.md  # The documentation homepage.
    ...       # Other markdown pages, images and other files.
```

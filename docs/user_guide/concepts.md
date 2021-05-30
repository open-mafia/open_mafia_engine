# Main Concepts

## Games and Prefabs

`Game` is the main class of the Engine. It does the following:

1. Holds all game state (players, alignments, phases, etc.)
2. Handles subscriptions, broadcasts and processes events.
3. Resolves actions in the proper order.

These things will be discussed later. The main thing to keep in mind for now
is that you can reach *anything* game-related via the `Game` instance.

A `Prefab` is a template for a game, which defines different roles, alignments,
and role combinations for different numbers of players.

### Creating a Game

You can load a Prefab:

- from a YAML file `Prefab.load_file(file_path)`
- by file name `Prefab.load("name.yml")`
- by prefab name `Prefab.load("Vanilla")`

In the last two cases, it will look through `default_search_paths` and
`extra_search_paths` for a matching Prefab. In the future, this may be cached.

To create a game from a Prefab:

```python
names = ["Alice", "Bob", "Charlie", "David", "Eevee"]
prefab = Prefab.load("Vanilla")
game = prefab.create_game(player_names=names)
# game = prefab.create_game(player_names=names, variant="5 players")
```

Note that `variant` can be omitted, since there is only a single 5-player variant.

## Actors, Alignments

The `Actor` class represents a player character (or NPC).

The `Alignment` class represents a particular "team"/"faction".
An `Alignment` has a particular name (for example, "town" or "mafia") and some
members (`Alignment.actors`).
Winning or losing is called an `Outcome`, and each Alignment also has particular
`OutcomeChecker`s associated with it - how they work will be explained later.

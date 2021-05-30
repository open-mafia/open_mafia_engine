# Prefabs and Creating a Game

A `Prefab` is a template for a game, which defines different roles, alignments,
and role combinations for different numbers of players.

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

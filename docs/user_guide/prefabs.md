# Prefabs

## Using Prefabs

### Loading a prefab

A `Prefab` is a template for a game, which defines different roles, alignments,
and role combinations for different numbers of players.

You can load a Prefab:

- from a YAML file `Prefab.load_file(file_path)`
- by file name `Prefab.load("name.yml")`
- by prefab name `Prefab.load("Vanilla")`

In the last two cases, it will look through `default_search_paths` and
`extra_search_paths` for a matching Prefab.
In the future, this may be cached, but currently it searches every time.

You can also make a Prefab via code, or load it via YAML or JSON strings.
Under the hood, `Prefab` is a `pydantic_yaml.YamlModel`;
see [pydantic](https://pydantic-docs.helpmanual.io/) and
[pydantic-yaml](https://github.com/NowanIlfideme/pydantic-yaml).
That means it should play well with JSON serialization and `FastAPI`, too.

### Creating a Game from a Prefab

To create a game from a Prefab, call `prefab.create_game()`:

```python
names = ["Alice", "Bob", "Charlie", "David", "Eevee"]
prefab = Prefab.load("Vanilla")
game = prefab.create_game(player_names=names)
# game = prefab.create_game(player_names=names, variant="5 players")
```

Note that `variant` can be omitted in this case, since there is only a single
5-player variant defined for the "Vanilla" prefab.

In cases where there are multiple variants with the same number of players,
a random one will be chosen that fits.

## Creating a Prefab

TODO - describe each section.

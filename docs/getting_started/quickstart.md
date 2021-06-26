# Quickstart

## Installing

Install the Open Mafia Engine package from PyPI, with recommended extras:

```sh
pip install open_mafia_engine[recommended]
```

This gives you the ability to run everything, and even create your own
abilities, factions, game types, etc.

## Running a simple game in the console

The Engine comes with a built-in "playground" where users can become familiar
with how the Engine works. You can run it from the command line (it's a console
application):

```sh
mafia-cli
```

You can enter `help` for a short introduction and command overview.

See the [Examples](../examples/index.md) or [Command Reference](../reference/commands.md)
for more information on how this app works.

## Creating your own game

The most important part of the Open Mafia Engine is that you can create your own
custom game, with different roles, factions, rule sets and so on.

To create a game with pre-existing roles, just make a
[game builder function][open_mafia_engine.core.builder.game_builder]
that takes player names (and maybe some other options).

```python
import open_mafia_engine.api as mafia

@mafia.game_builder("my_example")
def make_example_game(player_names: List[str]) -> mafia.Game:
    # Create the game object and some core helper objects
    game = mafia.Game()
    mafia.GameEnder(game)
    tally = mafia.LynchTally(game)

    # Create the main factions
    t = mafia.Faction(game, "Town")
    mafia.OCLastFactionStanding(game, t)

    m = mafia.Faction(game, "Mafia")
    mafia.OCLastFactionStanding(game, m)
    mafia.FactionChatCreatorAux(game, m)


    # Create the Town player
    a0 = mafia.Actor(game, player_names[0])
    t.add_actor(a0)
    # They can only vote
    vote = mafia.VoteAbility(game, a0, name="Vote", tally=tally)
    mafia.PhaseConstraint(game, vote, phase="day")


    # Create the Mafia player
    a1 = mafia.Actor(game, player_names[1])
    m.add_actor(a1)
    # They can vote...
    vote = mafia.VoteAbility(game, a1, name="Vote", tally=tally)
    mafia.PhaseConstraint(game, vote, phase="day")
    # ... and perform the Mafia kill (which has a lot of constraints)
    mk = mafia.KillAbility(
        game,
        a1,
        name="Mafia Kill",
        desc="Kill the target. Only 1 mafioso can use this.",
    )
    mafia.LimitPerPhaseActorConstraint(game, mk, limit=1)
    mafia.LimitPerPhaseKeyConstraint(game, mk, key="mafia_kill_limit")
    mafia.PhaseConstraint(game, mk, phase="night")
    mafia.ConstraintNoSelfFactionTarget(game, mk)

    return game
```

Then you can create the game object:

```python
game = make_example_game(["Alice", "Bob"])
```

Or, if saved in a model and imported:

```python
builder = mafia.GameBuilder.load("my_example")
game = builder.build(["Alice", "Bob"])
```

Technically, you could do this outside a function, but functions are much
more reusable. 😃

## Running your game in the console app

NOTE: This extra parameter doesn't work yet.

Assuming you have registered your function with the game builder, the Console
Application can load your Python module:

```sh
mafia-cli --import your_module.py
```

And you can load it inside the console app by the name you gave it:

```sh
admin create-game my_example
```

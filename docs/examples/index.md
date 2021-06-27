# Examples

Developing from scratch is difficult, which is why `open_mafia_engine` has
several built-in examples to help you get started and/or debug your custom
game objects.

## Console Application

The Mafia Console App is a full-screen console application written using the
`open_mafia_engine` and `prompt_toolkit`.

This is what it looks like:

![Example CLI Application](ExampleMafiaCLI.gif)

The left panel shows the current state, both when in a lobby and when in an
actual game. The right panel shows the command history. The input is at the
bottom, and it has some auto-completion and highlighting.

To be able to run it, make sure you installed `open_mafia_engine` with at least
the `examples` extra (`recommended` also works):

```bash
pip install open_mafia_engine[examples]
# or, if developing locally:
poetry install -E examples
```

To get started, run the app:

```bash
mafia-cli
# or
python -m open_mafia_engine.example.cli
```

This will give you an empty prompt. To view some basic commands, enter `help`.
The application runs like a command shell, using the syntax:

```bash
USER COMMAND arguments
```

The most useful commands are `NAME join`/`NAME in` (to add a player),
`admin create-game test` to start a test game, `admin phase` to change the phase
(note that the initial phase is always "startup" - make sure to phase to start
the game in earnest), `NAME vote TARGET` to perform vote actions (during the day)
and `NAME do ABILITY ARGS...` to activate abilities during the proper phase.

**TODO**: Explain how the application works.

The console app is useful not only for understanding how the Engine works, but it
also lets you test your own custom roles in an interactive environment.

## Tests

Another good resource for learning how the Open Mafia Engine works are the
[unit tests](https://github.com/open-mafia/open_mafia_engine/tree/master/open_mafia_engine/test),
(especially the `test_scenarios.py`) which go through the lower-level events.

## Discord Bot

The [Open Mafia Discord Bot](https://github.com/open-mafia/open_mafia_discord_bot)
is currently under development and will be released when it's up-to-date with
this version of the library.

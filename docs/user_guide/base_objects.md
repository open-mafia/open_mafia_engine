# User Guide

This page, along with the rest of the User Guide, will help you understand how
the Open Mafia Engine is built and how to build your own custom things on top.

## Game

[`Game`][open_mafia_engine.core.game.Game] is the main class of the Engine.
It does the following:

1. Holds all game state (players, alignments, phases, etc.)
2. Handles subscriptions, broadcasts and processes events.
3. Resolves actions in the proper order.

These things will be discussed later. The main thing to keep in mind for now
is that you can reach *anything* game-related via the `Game` instance.

## GameObject

All other classes inherit from [`GameObject`][open_mafia_engine.core.game_object.GameObject].
This class gives a reasonably readable `__repr__` for free, and also tracks
all non-abstract subclasses.

Each `GameObject` holds a refence to its parent `Game`, which allows it to
automatically use [converters][open_mafia_engine.core.game_object.inject_converters]
in the `__init__` method, or elsewhere, as long as you use the proper
[type hints](https://docs.python.org/3/library/typing.html).

These converters allow automatic conversion from external objects (such as strings)
`GameObject`s. For example, targeting some player by name will actually pass
in an `Actor` instance.

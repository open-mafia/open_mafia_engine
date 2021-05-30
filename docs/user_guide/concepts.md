# Main Concepts

## Game

`Game` is the main class of the Engine. It does the following:

1. Holds all game state (players, alignments, phases, etc.)
2. Handles subscriptions, broadcasts and processes events.
3. Resolves actions in the proper order.

These things will be discussed later. The main thing to keep in mind for now
is that you can reach *anything* game-related via the `Game` instance.

## Events, Actions and Subscribers

The Open Mafia Engine is primarily Event-based, see
[Event-driven Architecture on Wikipedia](https://en.wikipedia.org/wiki/Event-driven_architecture).

An `Event` typically represents some change in the game's state.

An `Action` is essentially a delayed function call.
Each `Action` object references its `source` (the entity that created the action),
some parameters, `priority` and whether it's `cancelled`.

A `Subscriber` is a very base object. It `subscribe`s to particular types of
events. `Subscriber.respond_to_event` takes an `Event` and `Game` context and
optionally returns an `Action` (the response).

## Core Logic

### Handling Events

Let's go through the event handling logic.

1. The `game` begins to `process_event(e)` for some event `e`.
2. The `game` goes through all `game.subscribers` that are relevant for `e`.
3. Each (relevant) `Subscriber` responds to the event, returning `None` or some `Action`.
4. Each non-None `Action` is added to the `game.action_queue`
5. Depending on the phase, the `ActionQueue` is proccessed either immediately or at the end of the phase.

Essentially, each `Subscriber` returns a delayed `Action` in response to the `Event`.

### Action Queues

An `ActionQueue` is just that - a queue of delayed actions.
The `Game` object contains the main queue, but more can be created temporarily
as part of the branching structure.

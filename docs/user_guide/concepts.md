# Main Concepts

## Game

`Game` is the main class of the Engine. It does the following:

1. Holds all game state (players, alignments, phases, etc.)
2. Handles subscriptions, broadcasts and processes events.
3. Resolves actions in the proper order.

These things will be discussed later. The main thing to keep in mind for now
is that you can reach *anything* game-related via the `Game` instance.

## GameObject

All engine objects inherit from `GameObject`. This class gives a reasonably readable
`__repr__` for free, and also tracks all non-abstract subclasses.

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
Actions are sorted by their `priority` (higher priority go first), then by the
order they were recieved. This means the action order should be deterministic.

The `Game` object contains the main queue, but more can be created temporarily
as part of the branching structure.

Each `ActionQueue` also holds the history of executed actions, for reference
(this may be needed by some other object).

### Processing the ActionQueue

`ActionQueue.process_all(game)` runs through all enqueued actions one by one.
For each action:

1. An `EPreAction` (pre-action `Event`) is created.
2. This `EPreAction` is broadcast to all relevant `Subscriber`s, who create `Action`s in response.
3. A new, secondary `ActionQueue` is formed using these actions, and that queue is run through.
4. If the current `Action` was cancelled,
5. Otherwise, `action.doit(game)` is run (i. e. the action occurs).
6. An `EPostAction` (post-action `Event`) is created and broadcast.
7. The responses to the `EPostAction` form their own `ActionQueue` that is also run through.
8. The history of all sub-queues is added to the current history, along with the action itself.

In reality, the above happens for all actions of the same priority, as a batch.
It's much easier to understand it as single actions, though:

1. "I'm about to do ACTION, any objections?"
2. "No, wait, I need to do PRE-RESPONSE first."
3. (PRE-RESPONSE occurs)
4. (action occurs, assuming PRE-RESPONSE didn't cancel it)
5. "OK, guys, I did ACTION."
6. "You did? Okay, let me POST-PRESPONSE."
7. (POST-RESPONSE occurs)

### Why make it this complicated?

This sort of event framework is common in many user interface applications,
though usually it's done in a top-down manner, with callbacks depending on
changes in the state.

In the Open Mafia Engine, you can think of `Subscriber`s as being the "callbacks",
and the `Action`s as their effects.

However, in order to allow "countering" or otherwise modifying actions (for example,
roleblocking and jailing, protection, passive abilities, and much more), these
actions *themselves* need to create their own events, and be able to be intercepted.

This flexibility is very similar to how action resolution works the game
*Magic: The Gathering*, where there is an action stack caused by activated and
triggered abilities. In fact, *MTG* had a large influence on the development
of the Open Mafia Engine.

Creating an action should be fairly simple, since all this response logic is
part of the Engine itself. It can make debugging action interaction difficult, though.

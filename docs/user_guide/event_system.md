# Event System

The Open Mafia Engine is primarily Event-based, see
[Event-driven Architecture on Wikipedia](https://en.wikipedia.org/wiki/Event-driven_architecture).
The Event/Action system is what drives all state change in the game.

## Events, Actions and Subscribers

An [`Event`][open_mafia_engine.core.event_system.Event] typically represents some change in the game's state.

An [`Action`][open_mafia_engine.core.event_system.Action] is essentially a delayed function call.
Each `Action` object references its `source` (the entity that created the action),
some parameters, `priority` and whether it's `cancelled`.

A [`Subscriber`][open_mafia_engine.core.event_system.Subscriber]
object subscribes to particular types of events through event handlers.
An [`EventHandler`][open_mafia_engine.core.event_system.EventHandler]
(usually a method wrapped in [`@handler`][open_mafia_engine.core.event_system.handler]
or [`@handles`][open_mafia_engine.core.event_system.handles])
takes particular types of `Event`s and returns zero or more `Action`s (the response).

## Event and Action Logic

### Handling Events

Let's go through the event handling logic.

1. The `game` begins to `process_event(e)` for some event `e`.
2. The `game` broadcasts to all event handlers for `e`.
3. Each handler responds to the event, returning `None` or a list of `Action`s.
4. Each `Action` is added to the `game.action_queue`
5. Depending on the phase, the [`ActionQueue`][open_mafia_engine.core.event_system.ActionQueue]
   is proccessed either immediately or at the end of the phase.

Essentially, each `EventHandler` a delayed `Action` in response to the `Event`.

### Action Queues

An [`ActionQueue`][open_mafia_engine.core.event_system.ActionQueue]
is just that - a queue of delayed actions.
Actions are sorted by their `priority` (higher priority goes first), then by the
order they were recieved. This means the action order should be deterministic.

The `Game` object contains the main queue, but more can be created temporarily
as part of the branching structure.

Each `ActionQueue` also holds the history of executed actions, for reference
(this may be needed by some other object).

### Processing the ActionQueue

`ActionQueue.process_all(game)` runs through all enqueued actions one by one.
For each action:

1. An [`EPreAction`][open_mafia_engine.core.event_system.EPreAction] (pre-action `Event`) is created.
2. This `EPreAction` is broadcast to all relevant `Subscriber`s, who create `Action`s in response.
3. A new, secondary `ActionQueue` is formed using these actions, and that queue is run through.
4. If the current `Action` was cancelled,
5. Otherwise, `action.doit(game)` is run (i. e. the action occurs).
6. An [`EPostAction`][open_mafia_engine.core.event_system.EPostAction] (post-action `Event`) is created and broadcast.
7. The responses to the `EPostAction` form their own `ActionQueue` that is also run through.
8. The history of all sub-queues is added to the current history, along with the action itself.

In reality, the above happens for all actions of the same priority, as a batch.
It's much easier to understand it as single actions, though:

1. You: "I'm about to do ACTION, any objections?"
2. Sub A: "No, wait, I need to do PRE-RESPONSE first."
3. (PRE-RESPONSE occurs)
4. (action occurs, assuming PRE-RESPONSE didn't cancel it)
5. You: "OK, guys, I did ACTION."
6. Sub B: "You did? Okay, let me POST-PRESPONSE."
7. (POST-RESPONSE occurs)

### Why make it this complicated?

This sort of event framework is common in many user interface applications,
though usually it's done in a top-down manner, with callbacks depending on
changes in the state.

In the Open Mafia Engine, you can think of `EventHandler`s as being the "callbacks",
and the `Action`s as their effects.

However, in order to allow "countering" or otherwise modifying actions (for example,
roleblocking and jailing, protection, passive abilities, and much more), these
actions *themselves* need to create their own events, and be able to be intercepted.

This flexibility is very similar to how action resolution works the game
*Magic: The Gathering*, where there is an action stack caused by activated and
triggered abilities. In fact, *MTG* had a large influence on the development
of the Open Mafia Engine.

Creating a simple action is fairly simple, since all this response logic is part
of the Engine itself. More involved actions can require multiple types (e. g. an
`Action`, `Ability` and some sort of watcher), but another framework would not be
this flexible. Events can make debugging interactions fairly difficult, though.

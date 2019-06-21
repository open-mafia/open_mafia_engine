Core Engine Concepts
====================

The entire engine is built around two main groups of concepts:

* Events, Actions, and Abilities (:ref:`the_event_system`)
  in the :mod:`mafia.core.event` and :mod:`mafia.core.ability` modules.

* The Game, Alignments, Actors, and their status (:ref:`the_state_system`)
  in the :mod:`mafia.state` subpackage.

The game rules are emergent properties of the game and each component part 
(most notably, the different :class:`Ability`'s of the :class:`Actor`'s).


.. _the_event_system:

The Event System
----------------

This system handles all the dynamics of the game, the "moving parts".

The :class:`mafia.core.event.Action` class represents a "delayed" action 
that is sent as a response to an :class:`mafia.core.event.Event` and placed 
in an :class:`mafia.core.event.ActionQueue` based on its priority. The queue 
is run over sequentially by the engine, triggering a 
:class:`mafia.core.event.PreActionEvent` before each action is executed. 
This allows "responses" to actions, possibly cancelling or otherwise 
modifying them. After a successful action execution, a 
:class:`mafia.core.event.PostActionEvent` is handled.

If you are familiar with the spell resolution stack in the game Magic: The 
Gathering, this is very similar to that (with a cancellation being like a 
"counterspell" in that game).

An :class:`mafia.core.ability.ActivatedAbility` is an "Action creator": it 
creates actions based on passed parameters. It also allows setting 
restrictions on when it can be used, and checking the restriction to prevent 
illegal uses (e.g. when the player is dead, or has already used it, or in 
the wrong phase, or ...). In contrast, a 
:class:`mafia.core.ability.TriggeredAbility` is a "passive" or "static" 
ability that creates actions in response to Events.

All the events, action queues, etc. are handled by an 
:class:`mafia.core.event.EventManager` that works on a "subscribe/broadcast" 
model. Each :class:`mafia.core.event.Subscriber` subscribes itself to the 
current active EventManager(s) in context along with the particular classes 
it listens to (to avoid calling every single object). Whenever any event 
is "handled", the EventManager calls all objects subscribed to that event 
type and recieves (optional) Actions, then executes the ActionQueue that 
is formed. Note that this can create even more ActionQueues.

.. _the_state_system:

The State System
----------------

The main object that holds game state is :class:`mafia.state.game.Game`, 
which acts as a context manager, EventManager, and holder of all the state 
information (somewhere in the hierarchy). :class:`mafia.state.actor.Actor`'s 
are the player or non-player characters that do all the actions. The "teams" 
concept is the job of the :class:`mafia.state.actor.Alignment`. There is 
normally only one Alignment per Actor, but it's possible to have multiple or 
none (e.g. a non-playing Moderator).

Beyond normal properties, some objects also have more "flexible" properties 
defined by a :class:`mafia.state.status.Status` with access control. I'm not 
entirely sure this is the best way to implement access control, but that's 
currently the way it is.

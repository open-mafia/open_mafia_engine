# Game State

As mentioned earlier, the [`Game`][open_mafia_engine.core.game.Game]
holds all the relevant state for the game.

## Phase and PhaseCycle

One peculiarity of Mafia games is that they usually proceed in "phases", such as
a "day - night" cycle. Sometimes games use more exotic phase structures, such as
"morning - day - evening - night", or include abilities that skip phases.

[`AbstractPhaseSystem`][open_mafia_engine.core.phase_cycle.AbstractPhaseSystem]
defines an abstract interface for these phase structures.
All will have a "startup" phase (for pre-game stuff) and a "shutdown" phase, for
when the game has ended.
[`SimplePhaseCycle`][open_mafia_engine.core.phase_cycle.SimplePhaseCycle]
has a "startup" phase, followed by endless cyclical phases
(defaults to "day" and "night"), exiting into a "shutdown" phase.

Each [`Phase`][open_mafia_engine.core.phase_cycle.Phase] has a name that
identifies it (e. g. "day" or "night 3") and an
[`ActionResolutionType`][open_mafia_engine.core.enums.ActionResolutionType]
(which is "instant" or "end_of_phase").

If `ActionResolutionType.instant`, which is the default for "day" phases, then
all actions in the base queue (`game.action_queue`) are immediately executed.
This corresponds to the usual "day action" activity: if you vote, your vote is
immediately counted; if you kill someone in broad daylight, the effect is immediate.

If `ActionResolutionType.end_of_phase`, which is the default for "night" phases,
then all actions in the base queue are accumulated, then executed right before
the phase ends. This corresponds to the usual "night action" activity: actions
happen in priority order, irrespective of what time they were actually submitted.

## Factions

The [`Faction`][open_mafia_engine.core.state.Faction] class represents a
particular "team"/"faction". It has a name (for example, "town" or "mafia")
and some members (`Faction.actors`).

Each `Faction` also has [`OutcomeChecker`s][open_mafia_engine.core.state.OutcomeChecker]
(to see who wins/loses), described [later in the tutorial](outcomes.md).

## Actors

The [`Actor`][open_mafia_engine.core.state.Actor] class represents a player
character (or NPC). Each actor has a name, one (or rarely more) `factions`,
some number of `abilities`, and a `status`.

### Abilities and Triggers

An [`Ability`][open_mafia_engine.core.state.Ability] is, broadly speaking, a thing
that allows some sort of `Action`, where the player has active control over when
the ability is used. An `Ability` responds to [`EActivate`][open_mafia_engine.core.state.EActivate]
events by creating an Action with the passed parameters.

A [`Trigger`][open_mafia_engine.core.state.Trigger], often called a "passive ability",
automatically responds to events.
For example, an "Unkillable" passive ability can be implemented as a `Trigger`
that nullifies all kill actions against the owner.

`Ability` and `Trigger` instances can have [`Constraint`s][open_mafia_engine.core.event_system.Constraint]
attached to them, which prevent the creation of `Action`s depending on some external or internal factors.

More information is available in the [Abilities guide](abilities.md).

### Status

Each `Actor` has a free-form [`Status`][open_mafia_engine.core.state.Status] object,
which acts like a `DefaultDict[str, Any]` with a default value of None.
Whenever an attribute is changed, the `Status` object emits an
[`EStatusChange`][open_mafia_engine.core.state.EStatusChange]
event, which is useful for tracking (or even undoing!) changes to status.

## Auxiliary Objects

The above objects can't cover all scenarios, so the engine also supports
arbitrary [`AuxObject`s][open_mafia_engine.core.auxiliary.AuxObject] to be added
to the `Game`. This is handled by the [`AuxHelper`][open_mafia_engine.core.auxiliary.AuxHelper]
class, available as `game.aux`.
Each `AuxObject` is a `Subscriber` with a particular `key` that should be unique.

A typical `AuxObject` is a [`Tally`][open_mafia_engine.built_in.voting.Tally],
such as a [`LynchTally`][open_mafia_engine.built_in.lynch_tally.LynchTally],
which tracks who the majority of players are voting for/want to eliminate.

Another useful aux object is the [`GameEnder`][open_mafia_engine.core.ender.GameEnder],
which ends the game (moves to the "shutdown" phase) when all `Faction`s have
achieved an `Outcome`.

Another important use for aux objects is to read out in-game events to an
external source, e.g. hooks for internal events to output to external systems.

Yet another use is to create self-deleting or self-resetting temporary objects,
such as for temporary (single-phase) protection or blocking abilities.
Some examples are [`TempPhaseAux`][open_mafia_engine.built_in.auxiliary.TempPhaseAux]
and [`CounterPerPhaseAux`][open_mafia_engine.built_in.auxiliary.CounterPerPhaseAux].

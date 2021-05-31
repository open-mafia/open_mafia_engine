# Game State

As mentioned earlier, the `Game` holds all the relevant state for the game.

## Phase and PhaseCycle

One peculiarity of Mafia games is that they usually proceed in "phases", such as
a "day - night" cycle. Sometimes games use more exotic phase structures, such as
"morning - day - evening - night", or include abilities that skip phases.

`AbstractPhaseCycle` defines an abstract interface for these phase structures.
`SimplePhaseCycle` has a "startup" phase, followed by N cyclical phases
(defaults to "day" and "night").

Each `Phase` has a name that identifies it (e. g. "day" or "night 3") and
`ActionResolutionType` (which is "instant" or "end_of_phase").

If `ActionResolutionType.instant`, which is the default for "day" phases, then
all actions in the base queue (`game.action_queue`) are immediately executed.
This corresponds to the usual "day action" activity: if you vote, your vote is
immediately counted; if you kill someone in broad daylight, the effect is immediate.

If `ActionResolutionType.end_of_phase`, which is the default for "night" phases,
then all actions in the base queue are accumulated, then executed right before
the phase ends. This corresponds to the usual "night action" activity: actions
happen in priority order, irrespective of what time they were actually submitted.

## Alignments

The `Alignment` class represents a particular "team"/"faction". It has a name
(for example, "town" or "mafia") and some members (`Alignment.actors`).

Each `Alignment` also has `OutcomeCheckers` (to see who wins/loses), described
[later in the tutorial](outcomes.md).

## Actors

The `Actor` class represents a player character (or NPC). Each actor has a
name, one (or more...) `alignments`, some number of `abilities`, and a `status`.

### Abilities

An `Ability` is, broadly speaking, a thing that allows some sort of `Action`.
It can be an `ActivatedAbility`, in which case the player has active control
over when the ability is used, or the ability can be triggered in some other
way (e. g. an "Unkillable" ability that nullifies all kill actions against
the owner).

More information will be given later in the [Abilities guide](abilities.md).

### Status

Each `Actor` has a free-form `Status` object, which acts like a
`DefaultDict[str, Any]` with a default value of None.
Whenever an attribute is changed, the `Status` object emits an `EStatusChanged`
event, which is useful for tracking (or even undoing!) changes to status.

## Auxiliary Objects

The above objects can't cover all scenarios, so the engine also supports
arbitrary `AuxGameObject`s to be added to the `Game`. This is handled by the
`AuxHelper` class, available as `game.aux`. Each `AuxGameObject` is a
`Subscriber`... and that's it, for now.

The most common `AuxGameObject` is probably an `AbstractVoteTally`, such as a
`SimpleLynchTally`, which tracks who the majority want to lynch.

Another use is to read out in-game events to an external source, such as the
`DebugNotifier` or `DebugMortician`, which log all events & deaths to the console
output, respectively.

Yet another use is to create self-deleting temporary objects, such as for temporary
(single-phase) protection or blocking abilities.

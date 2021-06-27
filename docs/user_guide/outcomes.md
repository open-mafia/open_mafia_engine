# Outcomes: Winning and Losing

## Outcome Basics

An [`Outcome`][open_mafia_engine.core.enums.Outcome] is a string enum,
with values `["victory", "defeat"]`.

An [`OutcomeChecker`][open_mafia_engine.core.state.OutcomeChecker] is a `Subscriber`
subclass that checks whether its parent `Faction` has won or lost (or neither).

Some examples of outcomes to check for:

- "Win when all mafia are eliminated" (a typical "town" win condition).
- "Win when we are the last faction alive" (for the "serial killer" alignment).
- "Lose when you are eliminated" (for the "survivor" alignment).

If an `OutcomeChecker` determines that its conditions apply, it responds to the
current event with an [`OutcomeAction`][open_mafia_engine.core.outcome.OutcomeAction].
Assuming nothing stops the faction from winning, the action runs, setting each
Actor's `actor.status['outcome']`. The `EPostAction` is actually a subclass called
[`EOutcomeAchieved`][open_mafia_engine.core.outcome.EOutcomeAchieved], which can
be listened to specifically.

An `EOutcomeAchieved` event represents a `Faction` *achieving* an outcome,
i. e. the alignment has already won or lost. This doesn't necessarily mean that
the other factions have achieved an `Outcome`, though.

## Ending the game

The `EOutcomeAchieved` events don't end the game by themselves. If you want
the game to end after all alignments achieve an `Outcome`, add a
[`GameEnder`][open_mafia_engine.core.ender.GameEnder] auxiliary object - it keeps
track of all outcomes and creates the [`EndTheGame`][open_mafia_engine.core.ender.EndTheGame]
action, followed by the [`EGameEnded`][open_mafia_engine.core.ender.EGameEnded] event.

The action changes the current `Phase` to the "shutdown" phase.

Nothing else actually happens when the game ends, but you can subscribe
to the `EGameEnded` event in your own application (via `AuxObject`) to wrap
up the game and award the victory to the proper alignment(s).

## Wrapping Up

That's it! The User Guide is over, but you can look at the [Examples](../examples/index.md),
[Reference documentation](../reference/core.md), or the source code, for more info.

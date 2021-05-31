# Outcomes - Winning and Losing

## Outcome Basics

An `Outcome` is a string enum, with values `["victory", "defeat"]`.

An `OutcomeChecker` is a `Subscriber` subclass that checks whether its
parent `Alignment` has won or lost (or neither).

Some examples of outcomes to check for:

- "Win when all mafia are eliminated" (a typical "town" win condition).
- "Win when we are the last faction alive" (for the "serial killer" alignment).
- "Lose when you are eliminated" (for the "survivor" alignment).

If an `OutcomeChecker` determines that its conditions apply, it responds to the
current event with an `OutcomeAction`. The `EPreAction` for this outcome action
is actually the `EPreOutcome`. Assuming nothing stops the faction from winning,
the `EPostAction` is actually a subclass called `EAlignmentOutcome`

An `EAlignmentOutcome` event represents an `Alignment` *achieving* an outcome,
i. e. the alignment has already won or lost. This doesn't necessarily mean that
the other factions have achieved an `Outcome`, though.

## Ending the game

The `EAlignmentOutcome` events don't end the game by themselves. If you want
the game to end after all alignments achieve an `Outcome`, add a `GameEnder`
auxiliary object - it keeps track of all outcomes and creates the `EndTheGame`
action, followed by the `EGameEnded` event.

Currently, nothing actually happens when the game ends, but you can subscribe
to the `EGameEnded` event in your own application (via `AuxGameObject`) to wrap
up the game and award the victory to the proper alignment(s).

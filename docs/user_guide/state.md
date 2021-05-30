# Game State

The `Game` holds all the relevant state for the game.

## Alignments, Actors

The `Alignment` class represents a particular "team"/"faction". It has a name
(for example, "town" or "mafia") and some members (`Alignment.actors`).

The `Actor` class represents a player character (or NPC). Each actor has a
name, one (or more...) `alignments`, some number of `abilities`, and a `status`.

## Abilities

An `Ability` is, broadly speaking, a thing that allows some sort of `Action`.
It can be an `ActivatedAbility`, in which case the player has active control
over when the ability is used, or the ability can be triggered in some other
way (e. g. an "Unkillable" ability that nullifies all kill actions against
the owner).

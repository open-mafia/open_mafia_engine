# Abilities and Triggers

## Types of abilities

The most familiar type of ability for mafia players is the "activated" ability,
where the player decides when to "activate" the ability. This is represented in
the engine by the [`Ability`][open_mafia_engine.core.state.Ability] type.
Some examples: voting, night kills, protection, role blocking, double-voting.

"Automatic" or "passive" abilities are [`Triggers`][open_mafia_engine.core.state.Trigger],
which perform actions in response to external events.
Though the player may percieve these to be different (e. g. having multiple lives
seems different than being a Paranoid Gun Owner), the implementation is similar:
both handle particular `Event` types and create `Action`s in response.

Note that both are derived from [`ATBase`][open_mafia_engine.core.state.ATBase].
This class automatically applies [`Constraint`s][open_mafia_engine.core.event_system.Constraint]
to objects' event handlers.

## Abilities

An `Ability` is probably the easiest case to implement.
It handles [`EActivate`][open_mafia_engine.core.state.EActivate] events,
which signal that we want to activate a particular ability, and responds with
a corresponding `Action`, given the sent parameters.

To create a custom Ability, you can either `Ability` and override
the `activate()` (and possibly `__init__()`) method(s):

```python
class MyAbility(Ability):
    
    def activate(self, arg1: Actor, arg2: str) -> Optional[List[Action]]:
        return []
```

Alternatively, you can generate one from a function or pre-existing `Action`:

```python
MyAbility = Ability.generate(
    func, params=["arg1", "arg2"], name="MyAbility", desc="Does arg2 to arg1."
)
```

This does the same as the above, but auto-generates the `MyAbility` class.

## Triggers

Abilities that are triggered in other ways (e. g. passive abilities) should
subclass `Trigger` directly. You can add any event handlers you want, and the
trigger will automatically apply the correct `Constraint`s.

## Constraints

Generally, abilites can only be used under particular conditions.
The most typical ones are:

- The source (`Actor`, parent of `ability`) must be alive.
- The target must be alive (if an `Actor`).
- You can use the ability only during the (day) or (night).
- Only one player from your `Faction` may use this ability, and once per night.

These conditions are represented by [`Constraint`][open_mafia_engine.core.event_system.Constraint] objects.
If a `Constraint` is violated, the `Ability` or `Trigger` doesn't actually return
the action(s) back to the action queue that called it, which means the ability or
trigger don't actually run.

TODO: Update constraint docs, I removed the outdated section.

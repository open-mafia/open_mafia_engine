# Abilities

## Types of abilities

The most familiar type of ability for mafia players is the "activated" ability,
where the player decides when to "activate" the ability. This is represented in
the engine by the `ActivatedAbility` type. Some examples: voting, night kills,
protection, role blocking, double-voting.

"Automatic" or "passive" abilities are the other kind, which perform actions
in response to external events. Though the player may percieve these to be
different (e. g. having multiple lives seems different than being a Paranoid
Gun Owner), the implementation is similar: both `subscribe` to particular
`Event` types and create `Action`s in response.

## Activated Abilities

An `ActivatedAbility` is probably the easiest case to implement.
It `subscribe`s to an `EActivateAbility` event, which signals that we want to
activate a particular ability, and responds with a corresponding `Action`,
given the params.

The minimum needed to implement your own `ActivatedAbility` is to override
`ActivatedAbility.make_action(game, **params) -> Optional[Action]`.
Actually, an even easier way is to use the factory method:

```python
MyAbility = ActivatedAbility.create_type(MyAction, name="MyAbility")
```

An even more concise, but less readable method, is this:

```python
ActivatedAbility_MyAction = ActivatedAbility[MyAction]
```

This does the same as the above, but auto-generates the ability class name.

## Triggered Abilities

Abilities that are triggered in other ways (e. g. passive abilities) should
subclass `Ability` directly (there is no `TriggeredAbility` class currently).

Subscribe and respond to events exactly as a normal `Subscriber`, except you
should additionally check `Constraint`s (see below) to be sure it makes sense
for the ability to be triggered.

## Constraints

Generally, abilites can only be used under particular conditions.
The most typical ones are:

- The source (`Actor`, parent of `ability`) must be alive.
- The target must be alive (if an `Actor`).
- You can use the ability only during the (day) or (night).
- Only one player from your `Alignment` may use this ability, and once per night.

These conditions are represented by `Constraint` objects.

A `Constraint` is a `Subscriber` that additionally has an `is_ok()` method.

`is_ok()` is called by the `ActivatedAbility` to make sure that it can run.
If at least one constraint is violated, it returns `None` in response to the
`EActivateAbility` event.

When implementing a custom triggered `Ability`, make sure to check the constraints
before returning an `Action`. There may eventually be a specific interface required
a-la `TriggeredAbility`, but it's currently unclear what it would be.

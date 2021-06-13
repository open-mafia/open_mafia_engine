from open_mafia_engine.core.all import PhaseChangeAction, Ability


PhaseChangeAbility = Ability.generate(
    PhaseChangeAction,
    params=["new_phase"],
    name="PhaseChangeAbility",
    doc="Ability to change the phase. Typically admin-only.",
    desc="Change the phase (or just bump it).",
)

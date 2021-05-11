from open_mafia_engine.core import *
from open_mafia_engine.examples import *


# Create the game

game = Game()

town = Alignment(game, name="town")
mafia = Alignment(game, name="mafia")


def add_townie(name: str):
    a = Actor(game, name=name, alignments=[town])
    av = VoteAbility(owner=a, name="vote")
    PhaseConstraint(av, ["day"])
    AliveConstraint(av)
    return a


def add_mafioso(name: str):
    a = Actor(game, name=name, alignments=[town])
    av = VoteAbility(owner=a, name="vote")
    PhaseConstraint(av, ["day"])
    AliveConstraint(av)

    ak = KillAbility(owner=a, name="kill")
    PhaseConstraint(ak, ["night"])
    AliveConstraint(ak)
    return a


alice = add_townie("Alice")
bob = add_mafioso("Bob")
charlie = add_townie("Charlie")


def abil(actor: Actor, name: str) -> Ability:
    return [x for x in actor.abilities if x.name == name][0]


# Yell at everything
notifier = Notifier()
notifier.__subscribe__(game)
mortician = Mortician()
mortician.__subscribe__(game)

# Run stuff

# Start first day
game.process_event(ETryPhaseChange())

# Do some voting (note the order - priority doesn't matter because it's instant)
game.process_event(EActivateAbility(abil(alice, "vote"), target="Bob"))
game.process_event(EActivateAbility(abil(bob, "vote"), target="Alice", priority=2.0))

# Start first night
game.process_event(ETryPhaseChange())

# Voting will fail
game.process_event(EActivateAbility(abil(bob, "vote"), target="Charlie"))
# But the kill will succeed
game.process_event(EActivateAbility(abil(bob, "kill"), target="Charlie"))

print("This happens before votes for C, A")
# start second day
game.process_event(ETryPhaseChange())

print(game.action_queue)
print("Done.")

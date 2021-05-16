from open_mafia_engine.core import *
from open_mafia_engine.examples import *


# Create the game

game = Game()

town = Alignment(game, name="town")
mafia = Alignment(game, name="mafia")

game.aux.add(LynchTally())


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


# Yell at everything
notifier = Notifier()
notifier.__subscribe__(game)
mortician = Mortician()
mortician.__subscribe__(game)

# Run stuff

# Start first day
game.process_event(ETryPhaseChange())

# Do some voting (note the order - priority doesn't matter because it's instant)
game.process_event(EActivateAbility(alice.abilities["vote"], target=bob))
game.process_event(EActivateAbility(bob.abilities["vote"], target=alice, priority=2.0))
game.process_event(EActivateAbility(charlie.abilities["vote"], target=alice))

# Start first night
game.process_event(ETryPhaseChange())

# Voting will fail
game.process_event(EActivateAbility(bob.abilities["vote"], target=charlie))
# But the kill will succeed
game.process_event(EActivateAbility(bob.abilities["kill"], target=charlie))

# start second day
game.process_event(ETryPhaseChange())

print(game.action_queue)
print("Done.")

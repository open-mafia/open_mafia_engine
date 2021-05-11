from open_mafia_engine.core import *
from open_mafia_engine.examples import *


# Create the game

game = Game()

town = Alignment(game, name="town")
mafia = Alignment(game, name="mafia")

alice = Actor(game, name="Alice", alignments=[town])
av = VoteAbility(owner=alice, name="vote")
PhaseConstraint(av, ["day"])

bob = Actor(game, name="Bob", alignments=[mafia])
bv = VoteAbility(owner=bob, name="vote")
PhaseConstraint(bv, ["day"])
bk = KillAbility(owner=bob, name="kill")
PhaseConstraint(bk, ["night"])


charlie = Actor(game, name="Charlie", alignments=[town])
cv = VoteAbility(owner=charlie, name="vote")
PhaseConstraint(cv, ["day"])

# Yell at everything
notifier = Notifier()
notifier.__subscribe__(game)
mortician = Mortician()
mortician.__subscribe__(game)

# Run stuff

# Start first day
game.process_event(ETryPhaseChange())

# Do some voting (note the order - priority doesn't matter because it's instant)
game.process_event(EActivateAbility(av, target="Bob"))
game.process_event(EActivateAbility(bv, target="Alice", priority=2.0))

# Start first night
game.process_event(ETryPhaseChange())

# Voting will fail
game.process_event(EActivateAbility(bv, target="Charlie"))
# But the kill will succeed
game.process_event(EActivateAbility(bk, target="Charlie"))

print("This happens before votes for C, A")
# start second day
game.process_event(ETryPhaseChange())

print(game.action_queue)
print("Done.")

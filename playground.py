from open_mafia_engine.core import *
from open_mafia_engine.examples import *


# Create the game

game = Game()

town = Alignment(game, name="town")
mafia = Alignment(game, name="mafia")

alice = Actor(game, name="alice", alignments=[town])
av = VoteAbility(owner=alice, name="vote")
PhaseConstraint(av, ["day"])

bob = Actor(game, name="bob", alignments=[mafia])
bv = VoteAbility(owner=bob, name="vote")
PhaseConstraint(bv, ["day"])

charlie = Actor(game, name="charlie", alignments=[town])
cv = VoteAbility(owner=charlie, name="vote")
PhaseConstraint(cv, ["day"])

# Yell at everything
notifier = Notifier()
notifier.__subscribe__(game)

# Run stuff

# start first day
game.process_event(ETryPhaseChange())

# do some voting
game.process_event(EActivateAbility(av))
game.process_event(EActivateAbility(av, target="bob"))

# start first night
game.process_event(ETryPhaseChange())

# voting at night - these actions should happen at day end
# Actually, they shouldn't happen at all, due to the constraint
game.process_event(EActivateAbility(av, target="charlie"))
game.process_event(EActivateAbility(av, target="alice", priority=10))

print("This happens before votes for C, A")
# start second day
game.process_event(ETryPhaseChange())

print(game.action_queue)
print("Done.")

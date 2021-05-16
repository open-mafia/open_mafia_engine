from open_mafia_engine.core import *
from open_mafia_engine.built_in.all import *
from open_mafia_engine.prefab import Prefab

pf = Prefab.load("vanilla.yml")
# Other ways:
# yp = Path(__file__).parent / "vanilla.yml"
# pf = Prefab.parse_file(yp, content_type="application/yaml")
# pf = Prefab(**load_yaml(yp))
print("Loaded prefab:", pf.name)
game = pf.create_game(list("ABCDE"))
town, mafia = game.alignments

t1, t2, t3 = town.actors[0:3]
m1 = mafia.actors[0]

# Run stuff

# Start first day
game.process_event(ETryPhaseChange())

# Do some voting (note the order - priority doesn't matter because it's instant)
game.process_event(EActivateAbility(t1.abilities["Vote"], target=m1))
game.process_event(EActivateAbility(m1.abilities["Vote"], target=t1, priority=2.0))
game.process_event(EActivateAbility(t2.abilities["Vote"], target=t1))
game.process_event(EActivateAbility(t1.abilities["Vote"], target=None))  # or UnvoteAll
game.process_event(EActivateAbility(t1.abilities["Vote"], target=VoteAgainstAll))

# Start first night
game.process_event(ETryPhaseChange())

# Voting will fail
game.process_event(EActivateAbility(m1.abilities["Vote"], target=t2))
# But the kill will succeed
game.process_event(EActivateAbility(m1.abilities["Mafia Kill"], target=t2))
# The second kill won't succeed, due to the limit
game.process_event(EActivateAbility(m1.abilities["Mafia Kill"], target=t3))
# Neither will the rhid time!
game.process_event(EActivateAbility(m1.abilities["Mafia Kill"], target=t3))

# start second day
game.process_event(ETryPhaseChange())

# Dead tries to vote (this should fail)
game.process_event(EActivateAbility(t1.abilities["Vote"], target=m1))

# Alive actor tries to vote dead actor (this should fail)
game.process_event(EActivateAbility(t3.abilities["Vote"], target=t1))

# This should succeed
game.process_event(EActivateAbility(t3.abilities["Vote"], target=m1))

# End second day - this should vote off m1, who is the only mafioso
game.process_event(ETryPhaseChange())

print(game.action_queue)
print("Done.")

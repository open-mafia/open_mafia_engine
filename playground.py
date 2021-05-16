from open_mafia_engine.core import *
from open_mafia_engine.prefab import Prefab

pf = Prefab.load("vanilla.yml")
# Other ways:
# yp = Path(__file__).parent / "vanilla.yml"
# pf = Prefab.parse_file(yp, content_type="application/yaml")
# pf = Prefab(**load_yaml(yp))
print("Loaded prefab:", pf.name)
game = pf.create_game(list("ABCDE"))
town, mafia = game.alignments

t1, t2 = town.actors[0:2]
m1 = mafia.actors[0]

# Run stuff

# Start first day
game.process_event(ETryPhaseChange())

# Do some voting (note the order - priority doesn't matter because it's instant)
game.process_event(EActivateAbility(t1.abilities["Vote"], target=m1))
game.process_event(EActivateAbility(m1.abilities["Vote"], target=t1, priority=2.0))
game.process_event(EActivateAbility(t2.abilities["Vote"], target=t1))

# Start first night
game.process_event(ETryPhaseChange())

# Voting will fail
game.process_event(EActivateAbility(m1.abilities["Vote"], target=t2))
# But the kill will succeed
game.process_event(EActivateAbility(m1.abilities["Mafia Kill"], target=t2))

# start second day
game.process_event(ETryPhaseChange())

print(game.action_queue)
print("Done.")

"""Test API systems."""

# flake8: noqa

import logging

logging.basicConfig(level=logging.INFO)


from mafia.playground.test_stuff import *

# game, lynch_tally, phase_state, mafia_kill_tracker,
# Alignment: mafia, town, etc.
# Players: mod, a - g
# Non-API functions: vote, mafiakill, change_phase, print_status

gg = game.api


def vote2(src_name, trg_name):
    src_api = gg.get_actor_api(src_name)([src_name])
    src_api.use_activated_ability(game, "vote", target=trg_name)


def mafiakill2(src_name, trg_name):
    src_api = gg.get_actor_api(src_name)([src_name])
    src_api.use_activated_ability(game, "mafia-kill", target=trg_name)


def change_phase2(new_phase=None):
    mod_api = gg.get_actor_api("Mod")(["Mod"])
    mod_api.use_activated_ability(game, "resolve-votes")
    mod_api.use_activated_ability(game, "change-phase", new_phase=new_phase)


def print_status2():
    print("----------------")
    curr_phase = gg.get_status_api("phase").get_current_phase_name()
    print("Phase:", curr_phase)
    if curr_phase == "day":
        curr_votes = gg.get_status_api("tally").get_current_votes()
        vote_leaders = gg.get_status_api("tally").get_vote_leader_names()
        print("Current votes:", curr_votes)
        print("Vote leaders:", vote_leaders)
    #
    actors = gg.get_actor_names()
    alive_actors = []
    for actor in actors:
        a_api = gg.get_actor_api(actor)
        if a_api.get_status_value("alive"):
            alive_actors.append(actor)

    print("Alive players: ", alive_actors)
    print("----------------")


if __name__ == "__main__":
    # Player names:
    # Mafia: Alice Bob
    # Town: Charles Dave Emily
    # M-Ally: Fred
    # Jester: Gwen

    # Day 1
    print_status2()
    # lynch a townie
    vote2("Alice", "Bob")
    vote2("Bob", "Charles")
    vote2("Dave", "Charles")

    change_phase2()

    # Night 1
    print_status2()
    # mafia kill
    mafiakill2(a.name, e.name)
    mafiakill2(b.name, d.name)  # this will fail, correctly

    change_phase2()

    # Day 2 votes
    print_status2()
    # lynch the jester
    vote2(a.name, g.name)
    vote2(d.name, g.name)
    vote2(b.name, d.name)
    vote2(g.name, g.name)

    change_phase2()

    # Night 2
    print_status2()
    # mafia kill the final townie
    mafiakill2(b.name, d.name)

    # Day 3

    print_status2()

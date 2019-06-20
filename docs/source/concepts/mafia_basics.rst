Mafia Concepts
==============

Before going into the details of this particular library/engine, 
we should first define what a "mafia" game is, what the main parts 
and concepts are, etc.

The `Mafia game`_ was originally a party game that consisted of two 
teams, the innocent townsfolk (who don't know the role or team of any 
player but themselves) and the mafia (who know each other and coordinate 
to kill off the townsfolk). The base game has sprung a lot of other 
variations, still collectively called "Mafia" or "Werewolf". Changes 
include different game backstory and flavor, new player roles, game 
mechanics, even teams. Some "Mafia" games even stray fairly far away 
from the normal rules, using crazy or even hidden set-ups to increase 
fun at the expense of player and moderator sanity. :)

To really understand the game, I suggest looking at the Wikipedia 
article or, even better, going to the 
`mafiascum <https://www.mafiascum.net/>` website, where they have a good 
tutorial and explanation of various roles. You can play the game 
in real life or online on forums/chat services/etc.

The goal of the **Open Mafia Engine** is to support a wide range of 
mafia variants and mafia-like games. Because of this, the engine has 
a very flexible representation that may seem overkill for simpler 
games. We will go through the main concepts of the game on this page, 
while the library classes that correspond to them are covered mainly 
in the `module documentation <../_reference/modules.html>`_, though 
we will reference them here as well.

Teams (Alignments)
------------------

In a mafia game, all the players are split into teams, usually denoted 
as the "Mafia", the "Town", and the "Third Party" players who have their 
own win condition (such as survivors, serial killers, and jesters). 
A group of players with the same vistory/loss conditions corresponds to 
an :class:`mafia.state.actor.Alignment` [#outcome_footnote]_. A typical 
win condition is "eliminate the opposing faction while having at least 
one alive player on your own faction" [#technically_majority]_. 

Players (Actors)
----------------

Each player is given a "Role" with various "Abilities". As an example,
a standard role is "Mafia henchman", with two abilities: *Vote to Lynch*, 
which is usable during the day to vote for who to lynch, and *Mafia Kill*, 
which is the shared faction kill for the Mafia (usable by only one mafioso 
per night). Some abilities are activated (such as voting and killing), but 
some are passive (such as *Unkillable* or *Look Like Town to Inspections*).
There are abilities that can affect the actions of other abilities, such 
as blocking or redirection.

In the Mafia Engine, a player is represented as an 
:class:`mafia.state.actor.Actor` class, with their "Role" being their 
Alignment membership, their abilities (:class:`mafia.core.ability.Ability`), 
and possibly other helper objects. The abilities that players can actually 
"use" are :class:`mafia.core.ability.ActivatedAbility`'s, while the passive/
triggered ones are :class:`mafia.core.ability.TriggeredAbility`'s. Abilities 
create Actions - more details are given in :ref:`the_event_system`.

Game Flow
---------

The game moves through a phase cycle, typically *day* (where voting and 
lynching occurs) and *night* (where kills, inspections, and other 
covert actions happen). Most Abilities are restricted to being used in only 
a particular phase, as just noted. This cycle is controlled by the moderator; 
in the Engine, this can be an Actor that is a game participant, or one with 
no alignments. Some abilities or win conditions can be triggered by phases 
changing or certain phase numbers ("5th day") being reached.


.. _Mafia game: https://en.wikipedia.org/wiki/Mafia_(party_game)

.. [#outcome_footnote] The conditions themselves are given by 
   :class:`mafia.mechanics.outcome.OutcomeChecker`, if you want to skip 
   ahead. The game ends when all alignments have an outcome.

.. [#technically_majority] Typical Mafia rules require the Mafioso 
   faction to achieve the majority. However, because the Engine has no 
   fast way of checking whether a majority is actually a "forced win" 
   for the mafia (due to possible town or other roles with various 
   abilities), the game needs to be played through to the end.

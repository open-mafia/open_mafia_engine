
Open Mafia Engine
#################

.. image:: https://readthedocs.org/projects/open-mafia-engine/badge/?version=latest
    :target: https://open-mafia-engine.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Open-source, extendable mafia engine, written in Python.

Docs available at https://open-mafia-engine.rtfd.io (stable/master) 
or https://open-mafia-engine.readthedocs.io/en/dev/ (dev).

Currently under construction! Feel free to star and check back soonish! :)


Installation
============

The package isn't available on PyPI, as we are definitely not ready yet. 
To install from source:

1. Install ``miniconda`` (or ``anaconda``).

2. Clone this repository.

3. Create and activate the environment given:

    conda env create -f env.yml

    conda activate mafia-engine

4. In the activated environment, install the library in development mode:

    python setup.py develop

You can now import the library in Python. 

There is currently no "real" game to run, but ``mafia.playground.test_stuff`` has 
(most of) the latest developments.


Progress Update (2019-06-06)
============================

Code for version 0.1.0 has been moved to ``mafia_old`` for a while now.
A lot of the previous progress update has been fixed:

* The ``EventManager`` now operates as a context, and so does the ``Game`` object.

* Class members are added as required (which sometimes require rewrites, but that's better 
  than useless bloat, right?). Examples are ability owners and the ``Action.canceled`` 
  attribute, which both came up out of necessity.
  
* Information visibility will be controlled by ``Status`` objects and object access levels.

The API will be separate from the main code, but discoverability and pre-testability is 
being built into the engine already.


Progress Update (2019-03-30)
============================

A proof-of-concept version 0.1.0 is out! Feel free to install. 
We will make a release branch out of this, however it will not go to PyPI.

The plan for the future is a *rewrite* to fix many limiting factors:

* ``EventManager`` as a singleton class.

* ``UUID``'s everywhere prematurely.

* Low discoverability of the API.

* No native way to limit "visibility" of information.

Oh yeah, and the docs still suck. 
I see no reason to improve them before stability comes... 
However, they should at least build properly, so I fixed that.

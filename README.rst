
Open Mafia Engine
#################

|GitHub release| |Documentation Status| |GitHub license|

Open-source, extendable mafia engine, written in Python.

Docs available at https://open-mafia-engine.rtfd.io (latest/dev) 
or https://open-mafia-engine.rtfd.io/en/stable/ (stable/master).

Currently under construction! Feel free to star and check back soonish! :)


.. include:: docs/source/howto/quickstart.rst


Progress Update (2019-06-06)
============================

Code for version 0.1.0 has been moved to ``mafia_old`` for a while now.
A lot of the previous progress update has been fixed:

* The ``EventManager`` now operates as a context, and so does the 
  ``Game`` object.

* Class members are added as required (which sometimes require rewrites, 
  but that's better than useless bloat, right?). Examples are ability owners 
  and the ``Action.canceled`` attribute, which both came up out of necessity.
  
* Information visibility will be controlled by ``Status`` objects and object 
  access levels.

The API will be separate from the main code, but discoverability and 
pre-testability is being built into the engine already.


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



.. |Documentation Status| image:: https://readthedocs.org/projects/open-mafia-engine/badge/?version=latest
    :target: https://open-mafia-engine.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |GitHub license| image:: https://img.shields.io/github/license/open-mafia/open_mafia_engine.svg
   :target: https://github.com/open-mafia/open_mafia_engine/blob/master/LICENSE
   :alt: GitHub license

.. |GitHub release| image:: https://img.shields.io/github/release/open-mafia/open_mafia_engine.svg
   :target: https://github.com/open-mafia/open_mafia_engine/releases
   :alt: GitHub release

.. my-header

Quickstart
==========

When the project reaches a reasonable level of maturity, 
it will be uploaded to PyPI and you'll be able to run:

.. code-block:: sh
    
    pip install mafia-engine


There is currently no "real" game to run, but ``mafia.playground.test_stuff`` 
has (most of) the latest developments.


Install from Source
===================

1. Install ``miniconda`` or ``anaconda``.

2. Clone this repository (you might want the ``dev`` branch).

3. Create and activate the environment given:

    conda env create -f env.yml

    conda activate mafia-engine

4. In the activated environment, install the library in development mode:

    python setup.py develop

You can now import the library in Python!

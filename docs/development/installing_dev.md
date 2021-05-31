# Installing for Development

Development is done via [Poetry](https://python-poetry.org/), which is a
packaging and dependency management tool.

You can either install Poetry system-wide and use its virual environments,
or you can install Poetry inside a virtual environment (such as Conda envs).

## Using Poetry

[Install poetry](https://python-poetry.org/docs/#installation)

Clone the repo to some directory and install everything via poetry:

```bash
git clone https://github.com/open-mafia/open_mafia_engine.git
cd open_mafia_engine
poetry install
```

This should become easier when [PEP 660](https://www.python.org/dev/peps/pep-0660/)
is implemented (will just be `pip install -e .`)

## Using Conda

If you use `conda`, you can install `poetry` in any virtual environment:

`conda activate YOUR_ENV_NAME`

`conda install -c conda-forge poetry`

Then clone and install, as above:

```bash
git clone https://github.com/open-mafia/open_mafia_engine.git
cd open_mafia_engine
poetry install
```

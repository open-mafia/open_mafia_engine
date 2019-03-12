#!\usr\bin\python
"""Setuptools-based installation for open_mafia_engine."""

from os import path
from codecs import open  # To use a consistent encoding
from setuptools import setup, find_packages

from mafia import __version__

description = "Open Mafia Engine - framework for mafia/werewolf games."
try:
    here = path.abspath(path.dirname(__file__))
    with open(path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except Exception: 
    long_description = description

setup(
    name="mafia",
    version=__version__,
    description=description,
    long_description=long_description,
    author="Open Mafia Team",
    author_email="openmafiateam@gmail.com",
    url="https://github.com/open-mafia/open_mafia_engine",
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Natural Language :: English',
    ],
    install_requires=[
        
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
    extras_require={
        # Required for building documentation
        'docs': [
            "sphinx", "sphinxcontrib-apidoc",
            "sphinx_rtd_theme",
        ],
        'tests': [
            'nose',
        ]
    },
    packages=find_packages(),
)

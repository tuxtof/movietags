#!/usr/bin/env python

__version__ = "0.5"

from setuptools import setup, find_packages
setup(
name = 'movietags',
version= __version__,
author='tuxtof',
author_email='dev@geo6.net',
description='Automagicly movie tagger.',
url='http://github.com/tuxtof/movietags',
license='GPLv2',

long_description="""movie use themoviedb database to automaticly tag media file.""",

py_modules = ['movietags', 'tmdb_api'],


entry_points = {
    'console_scripts': [
        'movietags = movietags:main',
    ],
},

)

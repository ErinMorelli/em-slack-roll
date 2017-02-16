#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
EZ Slack Leguide module setup.

Copyright (c) 2015-2016 Erin Morelli

Additional codes, improvements, additional features :

Copyright (c) 2017 Gilles Dejeneffe

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.


"""

import os
from setuptools import setup


def gen_data_files(*dirs):
    """Generate list of files for package data installation."""
    results = []

    for src_dir in dirs:
        src_dir = os.path.join('slack_leguide', src_dir)
        for root, dirs, files in os.walk(src_dir):
            top = root.split(os.sep)
            top.pop(0)
            root = (os.sep).join(top)
            for item in files:
                results.append(os.path.join(root, item))
    return results


# Set up slack_roll package
setup(
    name='Ez-slack-leguide',
    version='1.7',
    author='Gilles Dejeneffe',
    author_email='blacksadum@gmail.com',
    url='http://leguide.herokuapp.com',
    license='MIT',
    platforms='Linux, OSX',
    description='RPG Servant on Slack.',
    long_description=open('README.md').read(),

    packages=[
        'slack_leguide',
        'slack_leguide.templates'
    ],

    package_data={
        'slack_leguide': gen_data_files('templates')
    },

    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'newrelic',
        'keen',
        'pkginfo',
        'psycopg2',
        'slacker'
    ]
)

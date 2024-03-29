#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Copyright (c) 2015-2021 Erin Morelli.

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

from setuptools import setup, find_packages


setup(
    name='em-slack-roll',
    version=open('VERSION').read(),
    author='Erin Morelli',
    author_email='me@erin.dev',
    url='https://slack-roll.herokuapp.com',
    license='MIT',
    platforms='Linux, OSX',
    description='Roll some dice on Slack.',
    long_description=open('README.md').read(),
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'cryptography',
        'Flask',
        'Flask-SQLAlchemy',
        'gunicorn',
        'itsdangerous',
        'keen',
        'mysqlclient',
        'newrelic',
        'pkginfo',
        'psycopg2-binary',
        'slacker'
    ]
)

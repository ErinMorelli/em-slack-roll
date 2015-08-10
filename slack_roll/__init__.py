#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# EM Slack Roll
# Copyright (c) 2015 Erin Morelli
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
'''
Module: slack_roll

    - Sets up Flask application and module constants
'''

import os
from flask import Flask
from datetime import date
from pkg_resources import get_provider


# =============================================================================
#  App Constants
# =============================================================================

# Set module name
__module__ = "slack_roll.{0}".format(__file__)


# Get module info
def set_project_info():
    ''' Set project information from setup tools installation
    '''

    # CUSTOMIZE THIS VALUE FOR YOUR OWN INSTALLATION
    base_url = 'http://slack-roll.herokuapp.com'

    # Get app info from the dist
    app_name = 'slack_roll'
    provider = get_provider(app_name)

    return {
        'name': app_name,
        'name_full': 'EM Slack Roll',
        'author_url': 'http://www.erinmorelli.com',
        'version': '0.1b2',
        'version_int': 0.112,
        'package_path': provider.module_path,
        'copyright': str(date.today().year),
        'base_url': base_url,
        'auth_url': '{0}/authorize'.format(base_url),
        'confirm_url': '{0}/confirm'.format(base_url)
    }

# Project info
PROJECT_INFO = set_project_info()

# Set the template directory
TEMPLATE_DIR = os.path.join(PROJECT_INFO['package_path'], 'templates')

# Allowed slash commands
ALLOWED_COMMANDS = [
    '/roll',
    '/rolldice',
    '/diceroll',
    '/roll_dice',
    '/dice_roll'
]


# =============================================================================
# Flask App Configuration
# =============================================================================

# Initalize flask app
APP = Flask(
    'em-slack-roll',
    template_folder=TEMPLATE_DIR,
    static_folder=TEMPLATE_DIR
)

# Set up flask config
# SET THESE ENV VALUES FOR YOUR OWN INSTALLATION
APP.config.update({
    'SQLALCHEMY_DATABASE_URI': os.environ['EMSR_DATABASE_URI'],
    'SECRET_KEY': os.environ['EMSR_SECRET_KEY']
})

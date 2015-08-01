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
import logging
from datetime import date
import slack_tableflip.roll as roll
from pkg_resources import get_provider
from flask import Flask, redirect, render_template, request


# =============================================================================
# App Logging
# =============================================================================

__logfile__ = os.path.join(os.path.expanduser("~"), 'logs', 'roll.log')

# Config logging
logging.basicConfig(
    filename=__logfile__,
    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s',
    level=30,
)

logging.log(30, "Started app logging")


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
    base_url = 'http://dev.erinmorelli.com/slack/roll'

    # Get app info from the dist
    app_name = 'slack_roll'
    provider = get_provider(app_name)

    return {
        'name': app_name,
        'name_full': 'EM Slack Roll',
        'author_url': 'http://www.erinmorelli.com',
        'version_int': 0.101,
        'package_path': provider.module_path,
        'copyright': str(date.today().year),
        'base_url': base_url
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

# Set Slack API token
WEBHOOK_URL = os.environ['EMSR_WEBHOOK_URL']


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
    'SECRET_KEY': os.environ['EMSR_SECRET_KEY']
})


# =============================================================================
# Flask Views
# =============================================================================

@APP.route('/', methods=['GET', 'POST'])
def table():
    ''' Return a dice roll from a Slack POST call
    '''

    if request.method == 'POST':
        return roll.make_roll(request.form)

    else:
        return render_template(
            'index.html',
            project=PROJECT_INFO,
            allowed_commands=ALLOWED_COMMANDS
        )

# Run the Flask app
if __name__ == '__main__':
    APP.run()

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Copyright (c) 2015-2018 Erin Morelli.

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
from datetime import date
from threading import Thread
from pkg_resources import get_provider
import keen
from flask import Flask


# =============================================================================
#  App Constants
# =============================================================================

# Set module name
__module__ = "slack_roll.{0}".format(__file__)


# Get module info
def set_project_info():
    """Set project information from setup tools installation."""
    # CUSTOMIZE THIS VALUE FOR YOUR OWN INSTALLATION
    base_url = 'https://slack-roll.herokuapp.com'

    # Get app info from the dist
    app_name = 'slack_roll'
    provider = get_provider(app_name)

    return {
        'name': app_name,
        'name_full': 'EM Slack Roll',
        'author_url': 'http://www.erinmorelli.com',
        'github_url': 'https://github.com/ErinMorelli/em-slack-roll',
        'version': '2.0',
        'version_int': 2.0,
        'package_path': provider.module_path,
        'copyright': '2015-{0}'.format(str(date.today().year)),
        'client_secret': os.environ['SLACK_CLIENT_SECRET'],
        'client_id': os.environ['SLACK_CLIENT_ID'],
        'base_url': base_url,
        'oauth_url': 'https://slack.com/oauth/authorize',
        'auth_url': '{0}/authenticate'.format(base_url),
        'valid_url': '{0}/validate'.format(base_url),
        'team_url': '{0}/authorize'.format(base_url),
        'team_scope': [
            'commands',
            'bot'
        ]
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


def report_event(name, event):
    """Asynchronously report an event."""
    # Set up thread
    event_report = Thread(
        target=keen.add_event,
        args=(name, event)
    )

    # Set up as asynchronous daemon
    event_report.daemon = True

    # Start event report
    event_report.start()


# =============================================================================
# Flask App Configuration
# =============================================================================

# Initialize flask app
APP = Flask(
    'em-slack-roll',
    template_folder=TEMPLATE_DIR,
    static_folder=TEMPLATE_DIR
)

# Set up flask config
# SET THESE ENV VALUES FOR YOUR OWN INSTALLATION
APP.config.update({
    'SECRET_KEY': os.environ['SECURE_KEY'],
    'SQLALCHEMY_DATABASE_URI': os.environ['DATABASE_URL'],
    'SQLALCHEMY_TRACK_MODIFICATIONS': True
})

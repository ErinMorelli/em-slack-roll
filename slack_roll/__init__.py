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

import os
from datetime import date
from threading import Thread

import keen
from flask import Flask
from pkg_resources import get_provider


# Common project metadata
__version__ = open('VERSION').read()
__app_name__ = 'EM Slack Roll'
__copyright__ = f'2015-{str(date.today().year)}'

# Project URLs
base_url = os.environ.get('BASE_URL')
github_url = os.environ.get('GITHUB_URL')


# Project info
project_info = {
    'name': __app_name__,
    'version': __version__,
    'copyright': __copyright__,
    'base_url': base_url,
    'github_url': github_url,
    'client_secret': os.environ.get('SLACK_CLIENT_SECRET'),
    'client_id': os.environ.get('SLACK_CLIENT_ID'),
    'oauth_url': os.environ.get('OAUTH_URL'),
    'auth_url': f'{base_url}/authenticate',
    'valid_url': f'{base_url}/validate',
    'team_url': f'{base_url}/authorize',
    'team_scope': [
        'commands',
        'bot'
    ]
}

# Set the template directory
template_dir = os.path.join(get_provider(__name__).module_path, 'templates')

# Allowed slash commands
allowed_commands = [
    '/roll',
    '/rolldice',
    '/diceroll',
    '/roll_dice',
    '/dice_roll'
]

# Initialize flask app
app = Flask(
    'em-slack-roll',
    template_folder=template_dir,
    static_folder=template_dir
)

# Set up flask config
app.config.update({
    'SECRET_KEY': os.environ.get('SECURE_KEY'),
    'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': True
})


def report_event(name, event):
    """Asynchronously report an event."""
    event_report = Thread(
        target=keen.add_event,
        args=(name, event)
    )

    # Set up as asynchronous daemon
    event_report.daemon = True

    # Start event report
    event_report.start()

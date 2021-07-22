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

from datetime import timedelta
from urllib.parse import urlencode

from flask import abort
from slacker import OAuth, Error
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from slack_roll import project_info, report_event
from slack_roll.storage import Team, db


# Create serializer
generator = URLSafeTimedSerializer(project_info['client_secret'])


def get_redirect():
    """Generate Slack authentication URL."""
    state_token = generator.dumps(project_info['client_id'])

    # URL encode params
    params = urlencode({
        'client_id': project_info['client_id'],
        'redirect_uri': project_info['valid_url'],
        'scope': ' '.join(project_info['team_scope']),
        'state': state_token
    })

    # Set full location
    location = f"{project_info['oauth_url']}?{ params}"

    # Return URL for redirect
    return location


def validate_state(state):
    """Validate state token returned by authentication."""
    state_token = None

    try:
        # Attempt to decode state
        state_token = generator.loads(
            state,
            max_age=int(timedelta(minutes=60).total_seconds())
        )

    except SignatureExpired:
        # Token has expired
        report_event('token_expired', {'state': state})
        abort(400)

    except BadSignature:
        # Token is not authorized
        report_event('token_not_authorized', {'state': state})
        abort(401)

    if not state_token or state_token != project_info['client_id']:
        # Token is not authorized
        report_event('token_not_valid', {
            'state': state,
            'state_token': state_token
        })
        abort(401)


def get_token(code):
    """Request a token from the Slack API."""
    oauth = OAuth()
    result = None

    try:
        # Attempt to make request
        result = oauth.access(
            client_id=project_info['client_id'],
            client_secret=project_info['client_secret'],
            redirect_uri=project_info['valid_url'],
            code=code
        )
    except Error as err:
        report_event('oauth_error', {
            'code': code,
            'error': str(err)
        })
        abort(400)

    if not result or not result.successful:
        report_event('oauth_unsuccessful', {
            'code': code,
            'result': result.__dict__
        })
        abort(400)

    # Setup return info
    info = {
        'token': result.body['access_token'],
        'team_id': result.body['team_id'],
        'bot_id': result.body['bot']['bot_user_id'],
        'bot_token': result.body['bot']['bot_access_token']
    }

    # Return info
    return info


def store_data(info):
    """Store validated data in the database."""
    team = Team.query.get(info['team_id'])

    if team is None:
        # Create new team
        new_team = Team(
            team_id=info['team_id'],
            token=info['token'],
            bot_id=info['bot_id'],
            bot_token=info['bot_token']
        )

        # Store new user
        report_event('team_added', {
            'team_id': info['team_id'],
            'bot_id': info['bot_id']
        })
        db.session.add(new_team)

    else:
        # Update team info
        team.bot_id = info['bot_id']
        team.set_token(info['token'])
        team.set_bot_token(info['bot_token'])
        report_event('team_updated', {
            'team_id': info['team_id'],
            'bot_id': info['bot_id']
        })

    # Update DB
    db.session.commit()


def validate_return(args):
    """Run data validation functions."""
    if not args['state'] or not args['code']:
        report_event('missing_args', args)
        abort(400)

    # Validate state
    validate_state(args['state'])

    # Get access token and info
    token_info = get_token(args['code'])

    # Set up storage methods
    store_data(token_info)

    # Return successful
    return f"{project_info['base_url']}?success=1"

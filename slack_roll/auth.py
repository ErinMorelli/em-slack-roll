#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# EM Slack Roll
# Copyright (c) 2015-2016 Erin Morelli
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
Module: slack_tableflip.auth

    - Confirms Slack API Token provided by the user is valid
    - Stores authorized token data
'''

from flask import abort
from urllib import urlencode
from datetime import timedelta
from slacker import OAuth, Error
from slack_roll import PROJECT_INFO
from slack_roll.storage import Teams, DB
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


# Create serializer
GENERATOR = URLSafeTimedSerializer(PROJECT_INFO['client_secret'])


def get_redirect():
    ''' Generates Slack authentication URL
    '''

    # Generate state token
    state_token = GENERATOR.dumps(PROJECT_INFO['client_id'])

    # URL encode params
    params = urlencode({
        'client_id': PROJECT_INFO['client_id'],
        'redirect_uri': PROJECT_INFO['valid_url'],
        'scope': ' '.join(PROJECT_INFO['team_scope']),
        'state': state_token
    })

    # Set full location
    location = "{0}?{1}".format(PROJECT_INFO['oauth_url'], params)

    # Return URL for redirect
    return location


def validate_state(state):
    ''' Validates state token returned by authentication
    '''

    try:
        # Attempt to decode state
        state_token = GENERATOR.loads(
            state,
            max_age=timedelta(minutes=60).total_seconds()
        )

    except SignatureExpired:
        # Token has expired
        abort(400)

    except BadSignature:
        # Token is not authorized
        abort(401)

    if state_token != PROJECT_INFO['client_id']:
        # Token is not authorized
        abort(401)

    # Return success
    return


def get_token(code):
    ''' Requests a token from the Slack API
    '''

    # Set OAuth access object
    oauth = OAuth()

    try:
        # Attempt to make request
        result = oauth.access(
            client_id=PROJECT_INFO['client_id'],
            client_secret=PROJECT_INFO['client_secret'],
            redirect_uri=PROJECT_INFO['valid_url'],
            code=code
        )

    except Error:
        abort(400)

    if not result.successful:
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
    ''' Stores a validated data in the database
    '''

    # Check if user exists
    team = Teams.query.get(info['team_id'])

    if team is None:
        # Create new team
        new_team = Teams(info['team_id'])
        new_team.token = info['token']
        new_team.bot_id = info['bot_id']
        new_team.bot_token = info['bot_token']

        # Store new user
        DB.session.add(new_team)

    else:
        # Update team info
        team.token = info['token']
        team.bot_id = info['bot_id']
        team.bot_token = info['bot_token']

    # Update DB
    DB.session.commit()

    return


def validate_return(args):
    ''' Wrapper function for data validation functions
        Stores new authenticated data
    '''

    # Make sure we have args
    if not args.get('state') or not args.get('code'):
        abort(400)

    # Validate state
    validate_state(args.get('state'))

    # Get access token and info
    token_info = get_token(args.get('code'))

    # Set up storage methods
    store_data(token_info)

    # Set success url
    redirect_url = '{0}?success=1'.format(PROJECT_INFO['base_url'])

    # Return successful
    return redirect_url

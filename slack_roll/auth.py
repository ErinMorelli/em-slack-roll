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
Module: slack_tableflip.auth

    - Confirms Slack API Token provided by the user is valid
    - Stores authorized token data
'''

from flask import abort
from urllib import urlencode
from datetime import timedelta
from slacker import Auth, Error
from slack_roll import PROJECT_INFO
from slack_roll.storage import Users, DB
from sqlalchemy.exc import IntegrityError as IntegrityError


def validate_token(token):
    ''' Retrieves token information from Slack API
    '''

    # Set auth object
    auth = Auth(token)

    # Make request
    result = auth.test()

    # Check for errors
    if not result.successful:
        abort(400)

    # Return user info
    return result.body


def confirm_token(args):
    ''' Wrapper function for data validation functions
        Stores new authenticated user data
    '''

    # Make sure we have args
    if not args.get('token'):
        abort(400)

    # Validate token and get info
    token_info = validate_token(args.get('token'))

    # Create new user
    new_user = Users(token_info['team_id'])
    new_user.token = args.get('token')

    try:
        # Attempt to store new user
        DB.session.add(new_user)
        DB.session.commit()

    except IntegrityError:
        # User already exists
        abort(409)

    # Set success url
    redirect_url = '{0}?success=1'.format(sr.PROJECT_INFO['base_url'])

    # Return successful
    return redirect_url

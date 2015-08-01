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
''' Script to start Flask server for hosted dice rolling
'''

import slack_roll.auth as auth
import slack_roll.roll as roll
from flask import redirect, render_template, request
from slack_roll import APP, PROJECT_INFO, ALLOWED_COMMANDS


@APP.route('/', methods=['GET', 'POST'])
def home():
    ''' Render app homepage template
    '''

    if request.method == 'POST':
        return roll.make_roll(request.form)

    else:
        return render_template(
            'index.html',
            project=PROJECT_INFO,
            allowed_commands=ALLOWED_COMMANDS
        )


@APP.route('/authorize')
def authorize():
    ''' Render API token authorization page
    '''
    return render_template(
        'authorize.html',
        project=PROJECT_INFO
    )


@APP.route('/confirm')
def confirm():
    ''' Confirm the API token provided for authorization
    '''
    return redirect(auth.confirm_token(request.args))


# Run the Flask app
if __name__ == '__main__':
    APP.run()

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# pylint: disable=invalid-name
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

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from slack_roll import APP


# Create database
DB = SQLAlchemy(APP)


class Teams(DB.Model):  # pylint: disable=too-few-public-methods
    """Table for storing api tokens."""

    __tablename__ = 'roll_teams'

    id = DB.Column(DB.String(16), primary_key=True)
    token = DB.Column(DB.String(255))
    bot_id = DB.Column(DB.String(16))
    bot_token = DB.Column(DB.String(255))
    added = DB.Column(DB.DateTime, default=datetime.now)

    def __init__(self, team_id, token, bot_id, bot_token):
        """Initialize new Team in db."""
        self.id = team_id
        self.token = token
        self.bot_id = bot_id
        self.bot_token = bot_token

    def __repr__(self):
        """Friendly representation of Team for debugging."""
        return f'<Team id={self.id} bot_id={self.bot_id}>'


try:
    # Attempt to initialize database
    DB.create_all()

except SQLAlchemyError:
    # Other wise, refresh the session
    DB.session.rollback()

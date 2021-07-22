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

import os
from datetime import datetime

from cryptography.fernet import Fernet
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from . import app


# Create database
db = SQLAlchemy(app)


class Team(db.Model):
    """Table for storing api tokens."""
    __tablename__ = 'roll_teams'
    __cipher = Fernet(os.environ.get('TOKEN_KEY', '').encode('utf8'))

    id = db.Column(db.String(16), primary_key=True)
    encrypted_token = db.Column(db.BLOB)
    bot_id = db.Column(db.String(16))
    encrypted_bot_token = db.Column(db.BLOB)
    added = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, team_id, token, bot_id, bot_token):
        """Initialize new Team in db."""
        self.id = team_id
        self.bot_id = bot_id
        self.set_token(token)
        self.set_bot_token(bot_token)

    def set_token(self, token):
        """Encrypt and set token value ."""
        if not isinstance(token, bytes):
            token = token.encode('utf-8')
        self.encrypted_token = self.__cipher.encrypt(token)

    def get_token(self):
        """Retrieve decrypted token."""
        return self.__cipher.decrypt(self.encrypted_token).decode('utf-8')

    def set_bot_token(self, bot_token):
        """Encrypt and set bot token value ."""
        if not isinstance(bot_token, bytes):
            bot_token = bot_token.encode('utf-8')
        self.encrypted_bot_token = self.__cipher.encrypt(bot_token)

    def get_bot_token(self):
        """Retrieve decrypted bot token."""
        return self.__cipher.decrypt(self.encrypted_bot_token).decode('utf-8')

    def __repr__(self):
        """Friendly representation of Team for debugging."""
        return f'<Team id={self.id} bot_id={self.bot_id}>'


try:
    # Attempt to initialize database
    db.create_all()
except SQLAlchemyError:
    # Other wise, refresh the session
    db.session.rollback()

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# pylint: disable=global-variable-not-assigned,global-statement
"""
EZ Slack Roll module: slack_leguide.roll.

    - Parses POST data from Slack
    - Parses user roll request
    - Retrieves and returns roll data

Copyright (c) 2015-2016 Erin Morelli

Additional codes, improvements, additional features :
Copyright (c) 2017 Gilles Dejeneffe


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

import re
import random
import argparse
from slacker import Auth, Chat, Error
from slack_leguide.storage import Teams
from slack_leguide import PROJECT_INFO, ALLOWED_COMMANDS, report_event


# Set globals
ERRORS = []
COMMAND = None

# Set not authenticated error message
AUTH_MSG = "{0} is not authorized to post in this team: {1}"
AUTH_ERROR = AUTH_MSG.format(
    PROJECT_INFO['name_full'],
    '*<{0}|Click here to authorize>*'.format(PROJECT_INFO['base_url'])
)


class RollParser(argparse.ArgumentParser):
    """Custom ArgumentParser object for special error and help messages."""

    def error(self, message):
        """Store all error messages in global errors list."""
        global ERRORS
        ERRORS.append(message)

    def print_help(self, dice_roll=None):
        """Generate help and list messages."""
        global ERRORS
        global COMMAND

        if dice_roll == 'help':
            help_msg = "*{app_name}* can roll anywhere from "
            help_msg += "*1-100 dice* with *4-100 sides* each.\n"
            help_msg += "Here are some examples:\n\n"
            help_msg += "`{command}`\n\tRolls a single 6-sided die\n\n"
            help_msg += "`{command} d20`\n\tRolls a single 20-sided die\n\n"
            help_msg += "`{command} 4d10`\n\tRolls 4 10-sided dice\n\n"
            help_msg += "`{command} 1d6+3`\n\t"
            help_msg += "Rolls a single 6-sided die with a +3 modifier\n\n"
            help_msg += "`{command} help`\n\tShows this message\n"
            help_msg += "`roim`\n\tRolls a D666 from INSMV\n\n"
            help_msg += "`fac`\n\tFlip a coin (roll 2 side dice)\n\n"

            ERRORS.append(help_msg.format(
                app_name=PROJECT_INFO['name_full'],
                command=COMMAND
            ))

        elif dice_roll == 'version':
            ERRORS.append('{app_name} v{version}'.format(
                app_name=PROJECT_INFO['name_full'],
                version=PROJECT_INFO['version']
            ))


class RollAction(argparse.Action):  # pylint: disable=too-few-public-methods
    """Custom Action object for validating and parsing roll arguments."""

    def __call__(self, parser, namespace, values, option_string=None):
        """Validate flip arguments and stores them to namespace."""
        dice_roll = values.lower()

        # Check for help
        if dice_roll in ['help', 'version']:
            parser.print_help(dice_roll)
            return

        # Set defaults
        count = 1
        sides = 6
        modifier = None
        modifier_count = None

        # Parse the roll
        result = re.match(r'(\d+)?d(\d+)(?:([-+])(\d+))?', dice_roll, re.I)

        # Check that roll is valid
        if result is None:
            report_event('roll_invalid', {
                'roll': dice_roll
            })
            parser.error(
                "'{0}' is not a recognized roll format".format(
                    dice_roll.encode('utf-8')
                )
            )

        else:
            # Get the number of dice
            if result.group(1) is not None:
                count = int(result.group(1))

                # Set 100 count max
                if count > 100:
                    count = 100

                # Set 1 count min
                if count < 1:
                    count = 1

            # Get the number of sides
            if result.group(2) is not None:
                sides = int(result.group(2))

                # Set 100 side max
                if sides > 100:
                    sides = 100

                # Set 4 side min
                if sides < 4:
                    sides = 4

            # Get the modifiers
            if result.group(3) is not None:

                if result.group(4) is None:
                    report_event('roll_modifier_invalid', {
                        'roll': dice_roll
                    })
                    parser.error(
                        "'{0}' is not a recognized roll format".format(
                            dice_roll.encode('utf-8')
                        )
                    )

                modifier = result.group(3)
                modifier_count = int(result.group(4))

        # Set values
        setattr(namespace, 'count', count)
        setattr(namespace, 'sides', sides)
        setattr(namespace, 'modifier', modifier)
        setattr(namespace, 'modifier_count', modifier_count)

        return


def get_parser():
    """Set up and returns custom ArgumentParser object."""
    # Create roll parser
    parser = RollParser()

    # Add valid args
    parser.add_argument('dice_roll', action=RollAction)

    return parser


def get_team(args):
    """Return authenticated team token data."""
    # Look for team in DB
    team = Teams.query.get(args['team_id'])

    # Return token
    return team


def is_valid_token(token):
    """Check that the team has a valid token."""
    # Set auth object
    auth = Auth(token)

    try:
        # Make request
        result = auth.test()

    except Error as err:
        # Check for auth errors
        report_event(str(err), {
            'token': token
        })
        return False

    # Check for further errors
    if not result.successful:
        report_event('token_invalid', {
            'token': token,
            'result': result.__dict__
        })
        return False

    # Return successful
    return True


def do_roll(roll, user):
    """Perform requested roll action."""
    # Trackers
    roll_sum = 0
    roll_result = []
    roll_modifier = ''

    # Roll dice
    for _ in range(0, roll.count):
        die_roll = random.randint(1, roll.sides)
        roll_sum += die_roll
        roll_result.append(die_roll)

    # Deal with modifier
    if roll.modifier is not None:
        roll_modifier = '  {0} {1}'.format(roll.modifier, roll.modifier_count)

        if roll.modifier == '-':
            roll_sum -= roll.modifier_count

        elif roll.modifier == '+':
            roll_sum += roll.modifier_count

    # Format message
    formatted_result = ',  '.join(str(result) for result in roll_result)

    # Set plural
    die_word = 'dice'

    # Set singular case
    if roll.count == 1:
        die_word = 'die'

    # Set response
    response = '_{user} rolled {count} {sides}-sided {die}:_'.format(
        user=user,
        count=roll.count,
        sides=roll.sides,
        die=die_word
    )

    # Return response with results
    return '{response}  *{sum}*  ( {results} ){modifier}'.format(
        response=response,
        sum=roll_sum,
        results=formatted_result,
        modifier=roll_modifier
    )


def send_roll(team, roll, args):
    """Post the roll to Slack."""
    # Set up chat object
    chat = Chat(team.bot_token)

    try:
        # Attempt to post message
        chat.post_message(
            args['channel_id'],
            roll,
            username='Roll Bot',
            icon_emoji=':game_die:'
        )

    except Error as err:
        report_event(str(err), {
            'team': team.__dict__,
            'roll': roll,
            'args': args
        })

        # Check specifically for channel errors
        if str(err) == 'channel_not_found':
            err_msg = "{0} is not authorized to post in this channel.".format(
                'The {0} bot'.format(PROJECT_INFO['name_full'])
            )
            err_msg += ' Please invite it to join this channel and try again.'
            return err_msg

        # Report any other errors
        return '{0} encountered an error: {1}'.format(
            PROJECT_INFO['name_full'],
            str(err)
        )

    # Return successful
    return


def make_roll(args):
    """Wrapper function for roll functions."""
    # Reset global error traker
    global ERRORS
    ERRORS = []
    print args

    # Make sure this is a valid slash command
    if args['command'] not in ALLOWED_COMMANDS:
        report_event('command_not_allowed', args)
        return '"{0}" is not an allowed command'.format(args['command'])

    else:
        # Set global command value to access later
        global COMMAND
        COMMAND = args['command']

    # Check to see if team has authenticated with the app
    team = get_team(args)

    # If the user, team token, and bot token are not valid, let them know
    if (
            not team or
            not is_valid_token(team.token) or
            not is_valid_token(team.bot_token)
    ):
        report_event('auth_error', {
            'args': args,
            'team': team.__dict__
        })
        return AUTH_ERROR

    # If there's no input, use the default roll
    if not args['text']:
        dice_roll = 'd6'
    else:
        dice_roll = args['text']

    # Get parser
    parser = get_parser()

    # Parse args
    result = parser.parse_args([dice_roll])

    # Report any errors from parser
    if len(ERRORS) > 0:
        report_event('parser_errors', {
            'errors': ERRORS
        })
        return ERRORS[0]

    # Get requested flip
    roll = do_roll(result, args['user_name'])

    # Post flip as user
    err = send_roll(team, roll, args)

    # If there were problems posting, report it
    if err is not None:
        return err

    # Return successful
    return ('', 204)

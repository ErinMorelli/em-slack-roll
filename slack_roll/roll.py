#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# pylint: disable=global-variable-not-assigned,global-statement
"""
Copyright (c) 2015-2019 Erin Morelli.

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
from slack_roll.storage import Teams
from slack_roll import PROJECT_INFO, ALLOWED_COMMANDS, report_event


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

    def print_help(self, dice_roll=None):  # pylint: disable=arguments-differ
        """Generate help and list messages."""
        global ERRORS
        global COMMAND

        if dice_roll == 'help':
            help_msg = "*{app_name}* can roll anywhere from "
            help_msg += "*1-100 dice* with *2-100 sides* each.\n"
            help_msg += "Here are some examples:\n\n"
            help_msg += "`{command}`\n\tRolls a single 6-sided die\n\n"
            help_msg += "`{command} d20`\n\tRolls a single 20-sided die\n\n"
            help_msg += "`{command} 4d10`\n\tRolls 4 10-sided dice\n\n"
            help_msg += "`{command} 1d6+3`\n\t"
            help_msg += "Rolls a single 6-sided die with a +3 modifier\n\n"
            help_msg += "`{command} 10d6 hit5`\n\t"
            help_msg += "Counts hits for rolls >= 5 and misses for < 5\n\n"
            help_msg += "`{command} help`\n\tShows this message\n"

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
        hit = None

        # Parse the roll
        result = re.match(
            r'(?P<count>\d+)?d(?P<sides>\d+)' +
            r'(?:(?P<mod>[-+])(?P<mod_count>\d+))?' +
            r'(?:\s(?P<hit>hit)(?P<hit_count>\d+)?)?',
            dice_roll,
            re.I
        )

        # Check that roll is valid
        if result is None:
            report_event('roll_invalid', {
                'roll': dice_roll
            })
            parser.error(
                "'{0}' is not a valid roll format".format(dice_roll)
            )

        else:
            # Get the number of dice
            if result.group('count') is not None:
                count = int(result.group('count'))

                # Set 100 count max
                if count > 100:
                    count = 100

                # Set 1 count min
                if count < 1:
                    count = 1

            # Get the number of sides
            if result.group('sides') is not None:
                sides = int(result.group('sides'))

                # Set 100 side max
                if sides > 100:
                    sides = 100

                # Set 2 side min
                if sides < 2:
                    sides = 2

            # Get the modifiers
            if result.group('mod') is not None:

                # Check that we have a number with the modifier
                if result.group('mod_count') is None:
                    report_event('roll_modifier_invalid', {
                        'roll': dice_roll
                    })
                    parser.error(
                        "'{0}' is not a valid roll format".format(dice_roll)
                    )

                # Set modifier data
                modifier = result.group('mod')
                modifier_count = int(result.group('mod_count'))

                # Set 100 modifier max
                if modifier_count > 100:
                    modifier_count = 100

            # Get the hit
            if result.group('hit') is not None:
                # Set default hit to 5 as per Shadowrun mechanics
                hit = 5

                # See if we have a hit threshold
                if result.group('hit_count') is not None:
                    hit = int(result.group('hit_count'))

                    # Set max hit to 100
                    if hit > 100:
                        hit = 100

                # Make sure we have enough sides
                if hit > sides:
                    report_event('roll_hit_invalid', {
                        'roll': dice_roll
                    })
                    parser.error(
                        "Hit threshold '{0}' is too big".format(hit)
                    )

        # Set values
        setattr(namespace, 'count', count)
        setattr(namespace, 'sides', sides)
        setattr(namespace, 'modifier', modifier)
        setattr(namespace, 'modifier_count', modifier_count)
        setattr(namespace, 'hit', hit)

        # Exit call
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
    roll_hits = 0
    roll_hits_crit = 0
    roll_misses = 0
    roll_misses_crit = 0

    # Roll dice
    for _ in range(0, roll.count):
        die_roll = random.randint(1, roll.sides)
        roll_sum += die_roll
        roll_result.append(die_roll)

        # Handle hits/misses
        if roll.hit is not None:

            # Hits
            if die_roll >= roll.hit:
                roll_hits += 1

                # Critical hits
                if die_roll == roll.sides:
                    roll_hits_crit += 1

            else:
                # Misses
                roll_misses += 1

                # Critical failures
                if die_roll == 1:
                    roll_misses_crit += 1

    # Deal with modifier
    if roll.modifier is not None:
        roll_modifier = '  {0} {1}'.format(roll.modifier, roll.modifier_count)

        if roll.modifier == '-':
            roll_sum -= roll.modifier_count

        elif roll.modifier == '+':
            roll_sum += roll.modifier_count

    # Format message
    formatted_result = ',  '.join(str(result) for result in roll_result)

    # Set singular/plural word
    die_word = 'die' if roll.count == 1 else 'dice'

    # Set response
    response = '_{user} rolled {count} {sides}-sided {die}:_'.format(
        user=user,
        count=roll.count,
        sides=roll.sides,
        die=die_word
    )

    # Default to no hit results
    hits = ''

    # Add hit results
    if roll.hit is not None:
        miss_crit = ''
        hit_crit = ''

        # Check if we have any critical hits
        if roll_hits_crit > 0:
            hit_crit = ' ({0} critical)'.format(roll_hits_crit)

        # Check if we had any critical misses
        if roll_misses_crit > 0:
            miss_crit = ' ({0} critical)'.format(roll_misses_crit)

        # Format the results
        hits = '  with {hit} hit{h}{hcrit} and {miss} miss{m}{mcrit}'.format(
            hit=roll_hits,
            h='' if roll_hits == 1 else 's',
            hcrit=hit_crit,
            miss=roll_misses,
            m='' if roll_misses == 1 else 'es',
            mcrit=miss_crit
        )

    # Return response with results
    return '{response}  *{sum}*  ( {results} ){modifier}{hits}'.format(
        response=response,
        sum=roll_sum,
        results=formatted_result,
        modifier=roll_modifier,
        hits=hits
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

    # Return no errors
    return None


def make_roll(args):
    """Run dice roll functions."""
    # Reset global error tracker
    global ERRORS
    ERRORS = []

    # Make sure this is a valid slash command
    if args['command'] not in ALLOWED_COMMANDS:
        report_event('command_not_allowed', args)
        return '"{0}" is not an allowed command'.format(args['command'])

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
    dice_roll = 'd6' if not args['text'] else args['text']

    # Get parser
    parser = get_parser()

    # Parse args
    result = parser.parse_args([dice_roll])

    # Report any errors from parser
    if ERRORS:
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

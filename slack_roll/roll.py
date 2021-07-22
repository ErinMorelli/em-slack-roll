#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# pylint: disable=global-variable-not-assigned,global-statement
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

import re
import random
import argparse
from slacker import Auth, Chat, Error

from slack_roll.storage import Team
from slack_roll import project_info, allowed_commands, report_event


# Set globals
errors = []
command = None

# Set not authenticated error message
auth_error = f"{project_info['name']} is not authorized to post in this team:" \
             f" *<{project_info['base_url']}|Click here to authorize>*"


class RollParser(argparse.ArgumentParser):
    """Custom ArgumentParser object for special error and help messages."""

    def error(self, message):
        """Store all error messages in global errors list."""
        global errors
        errors.append(message)

    def print_help(self, dice_roll=None):  # pylint: disable=arguments-differ
        """Generate help and list messages."""
        global errors
        global command

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

            errors.append(help_msg.format(
                app_name=project_info['name'],
                command=command
            ))

        elif dice_roll == 'version':
            errors.append(f"{project_info['name']} v{project_info['version']}")


class RollAction(argparse.Action):  # pylint: disable=too-few-public-methods
    """Custom Action object for validating and parsing roll arguments."""

    @staticmethod
    def _get_dice(result):
        """Parse the die count from roll. Default = 1."""
        if not result.group('count'):
            return 1

        # Convert to an integer
        count = int(result.group('count'))

        # Set 100 count max
        if count > 100:
            count = 100

        # Set 1 count min
        if count < 1:
            count = 1

        # Return the number of dice
        return count

    @staticmethod
    def _get_sides(result):
        """Parse the number of sides from the roll. Default = 6."""
        if not result.group('sides'):
            return 6

        # Convert to an integer
        sides = int(result.group('sides'))

        # Set 100 side max
        if sides > 100:
            sides = 100

        # Set 2 side min
        if sides < 2:
            sides = 2

        # Return number of sides
        return sides

    @staticmethod
    def _get_modifiers(result):
        """Parse the modifier data from the roll. Default = None, None."""
        if not result.group('mod'):
            return None, None

        # Set modifier data
        modifier = result.group('mod')
        modifier_count = int(result.group('mod_count'))

        # Set 100 modifier max
        if modifier_count > 100:
            modifier_count = 100

        # Return modifier type and count
        return modifier, modifier_count

    @staticmethod
    def _get_hits(result):
        """Parse the hit data from the roll. Default = None."""
        if not result.group('hit'):
            return None

        # Set default hit to 5 as per shadowrun mechanics
        hit = 5

        # See if we have a hit threshold
        if result.group('hit_count') is not None:
            hit = int(result.group('hit_count'))

            # Set max hit to 100
            if hit > 100:
                hit = 100

        # Return hit value
        return hit

    def __call__(self, parser, namespace, values, option_string=None):
        """Validate flip arguments and stores them to namespace."""
        dice_roll = values.lower()

        # Check for help
        if dice_roll in ['help', 'version']:
            parser.print_help(dice_roll)
            return

        # Parse the roll
        result = re.match(
            r'(?P<count>\d+)?d(?P<sides>\d+)' +
            r'(?:(?P<mod>[-+])(?P<mod_count>\d+))?' +
            r'(?:\s(?P<hit>hit)(?P<hit_count>\d+)?)?',
            dice_roll,
            re.I
        )

        # Check that roll is valid
        if not result:
            report_event('roll_invalid', {'roll': dice_roll})
            parser.error(f"'{dice_roll}' is not a valid roll format")

        # Get the number of dice
        count = self._get_dice(result)

        # Get the number of sides
        sides = self._get_sides(result)

        # Get the modifiers
        try:
            modifier, modifier_count = self._get_modifiers(result)
        except TypeError:
            report_event('roll_modifier_invalid', {'roll': dice_roll})
            parser.error(f"'{dice_roll}' is not a valid roll format")
            return

        # Get the hit
        hit = self._get_hits(result)
        if hit and hit > sides:
            report_event('roll_hit_invalid', {'roll': dice_roll})
            parser.error(f"Hit threshold '{hit}' is too big")
            return

        # Set values
        setattr(namespace, 'count', count)
        setattr(namespace, 'sides', sides)
        setattr(namespace, 'modifier', modifier)
        setattr(namespace, 'modifier_count', modifier_count)
        setattr(namespace, 'hit', hit)


def get_parser():
    """Set up and returns custom ArgumentParser object."""
    parser = RollParser()
    parser.add_argument('dice_roll', action=RollAction)
    return parser


def get_team(args):
    """Return authenticated team token data."""
    return Team.query.get(args['team_id'])


def is_valid_token(token):
    """Check that the team has a valid token."""
    auth = Auth(token)

    try:
        # Make request
        result = auth.test()

    except Error as err:
        # Check for auth errors
        report_event(str(err), {})
        return False

    # Check for further errors
    if not result.successful:
        report_event('token_invalid', {'result': result.__dict__})
        return False

    # Return successful
    return True


def format_roll_response(roll, user, roll_data):
    """Format bot response message."""
    formatted = ',  '.join(str(result) for result in roll_data['result'])

    # Set singular/plural word
    die_word = 'die' if roll.count == 1 else 'dice'

    # Set response
    response = f'_{user} rolled {roll.count} {roll.sides}-sided {die_word}:_'

    # Default to no hit results
    hits = ''

    # Add hit results
    if roll.hit is not None:
        miss_crit = ''
        hit_crit = ''

        # Check if we have any critical hits
        if roll_data['hits_crit'] > 0:
            hit_crit = f" ({roll_data['hits_crit']} critical)"

        # Check if we had any critical misses
        if roll_data['misses_crit'] > 0:
            miss_crit = f" ({roll_data['misses_crit']} critical)"

        # Format the results
        hit_plural = '' if roll_data['hits'] == 1 else 's'
        miss_plural = '' if roll_data['misses'] == 1 else 'es'

        hits = f"  with {roll_data['hits']} hit{hit_plural}{hit_crit} and" \
               f" {roll_data['misses']} miss{miss_plural}{miss_crit}"

    # Return formatted response
    return f"{response}  *{roll_data['sum']}*  " \
           f"( {formatted} ){roll_data['modifier']}{hits}"


def roll_die(roll, roll_data):
    """Perform a die roll and handle hits and misses"""
    die_roll = random.randint(1, roll.sides)
    roll_data['sum'] += die_roll
    roll_data['result'].append(die_roll)

    # Handle hits/misses
    if roll.hit is not None:
        # Add 1 for each regular hit/miss, 2 for critical
        if die_roll >= roll.hit:
            # Hits
            roll_data['hits'] += 2 if die_roll == roll.sides else 1
        else:
            # Misses
            roll_data['misses'] += 2 if die_roll == 1 else 1

    # Return updated roll data
    return roll_data


def do_roll(roll, user):
    """Perform requested roll action."""
    roll_data = {
        'sum': 0,
        'result': [],
        'modifier': '',
        'hits': 0,
        'hits_crit': 0,
        'misses': 0,
        'misses_crit': 0
    }

    # Roll dice
    for _ in range(0, roll.count):
        roll_data = roll_die(roll, roll_data)

    # Deal with modifier
    if roll.modifier is not None:
        roll_data['modifier'] = f'  {roll.modifier} {roll.modifier_count}'

        if roll.modifier == '-':
            roll_data['sum'] -= roll.modifier_count

        elif roll.modifier == '+':
            roll_data['sum'] += roll.modifier_count

    # Format message
    return format_roll_response(roll, user, roll_data)


def send_roll(team, roll, args):
    """Post the roll to Slack."""
    chat = Chat(team.get_bot_token())

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
            err_msg = f'The {project_info["name"]} bot is not ' \
                      f'authorized to post in this channel. ' \
                      f'Please invite it to join this channel and try again.'
            return err_msg

        # Report any other errors
        return f"{project_info['name']} encountered an error: {str(err)}"

    # Return no errors
    return None


def make_roll(args):
    """Run dice roll functions."""
    global errors
    errors = []

    # Make sure this is a valid slash command
    if args['command'] not in allowed_commands:
        report_event('command_not_allowed', args)
        return f'"{args["command"]}" is not an allowed command'

    # Set global command value to access later
    global command
    command = args['command']

    # Check to see if team has authenticated with the app
    team = get_team(args)

    # If the user, team token, and bot token are not valid, let them know
    if (
            not team or
            not is_valid_token(team.token) or
            not is_valid_token(team.bot_token)
    ):
        report_event('auth_error', {'args': args, 'team': team.__dict__})
        return auth_error

    # If there's no input, use the default roll
    dice_roll = 'd6' if not args['text'] else args['text']

    # Parse args
    parser = get_parser()
    result = parser.parse_args([dice_roll])

    # Report any errors from parser
    if errors:
        report_event('parser_errors', {'errors': errors})
        return errors[0]

    # Get requested flip
    roll = do_roll(result, args['user_name'])

    # Post flip as user
    err = send_roll(team, roll, args)

    # If there were problems posting, report it
    if err is not None:
        return err

    # Return successful
    return '', 204

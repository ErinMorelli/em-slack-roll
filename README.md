# [EM Slack Roll](http://dev.erinmorelli.com/slack/roll)
Roll some dice on [Slack](https://slack.com).

EM Slack Roll needs to be authorized to post to your team. Get authorized [here](http://dev.erinmorelli.com/slack/roll/authorize).

----------
## Setup

1. Add a new **Slash Command** by going to:

        https://{your-team}.slack.com/services/new/slash-commands

2. Use one of the following options as your new command:

        /roll
        /rolldice
        /diceroll
        /roll_dice
        /dice_roll

    **Note:** Table flipping will not work without one of these specific slash commands.

3. Set the **URL** field to:

        http://dev.erinmorelli.com/slack/roll/

    **Note:** The trailing slash matters!

4. Set the **Method** option to `POST`

5. Some optional, but useful extra steps:
    1. Check the box next to **Show this command in the autocomplete list**.
    2. Set the **Description** field to `"Roll some dice"`.
    3. Set the **Usage** hint field to `"[roll] (or 'help')"`.
    4. Set the **Descriptive Label** field to `"EM Slack Roll"`.

6. And finally, click the **Save Integration** button. Check out the [usage](#usage) section to get started flipping!

----------
## Usage

**Note:** These examples use `/roll` as the slash command, but yours may vary based on what you selected for step 2 during the [setup](#setup) process.

Use command `/roll help` to view this usage information from within Slack.

**Basic roll:**

    /roll

Rolls a single 6-sided die.

**Specify number of sides:**

    /roll d20

Rolls a single 20-sided die.

**Specify dice count:**

    /roll 4d10

Rolls a 4 10-sided dice.

**Specify a modifier:**

    /roll 1d6+3

Rolls a single 6-sided die with a +3 modifier.
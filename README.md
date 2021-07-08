# [EM Slack Roll](https://slack-roll.herokuapp.com)
Roll some dice on [Slack](https://slack.com).

[Click here](http://slack-roll.herokuapp.com) to setup EM Slack Roll for your team.

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ErinMorelli_em-slack-roll&metric=alert_status)](https://sonarcloud.io/dashboard?id=ErinMorelli_em-slack-roll)

----------
## Usage

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

**Track hits and misses:**

    /roll 10d6 hit5

Rolls 10 6-sided dice and counts hits for results >= 5 and misses for those < 5. Results will also count how many hits are critical (the highest possible roll value) and how many misses are critical (the lowest possible roll value, 1).

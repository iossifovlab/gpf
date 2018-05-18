'''
Created on Sep 14, 2016

@author: lubo
'''
from __future__ import unicode_literals
import re


def calc_race(race1, race2):
    if race1 == race2:
        return race1
    if race1 is None or race2 is None:
        return 'not-specified'
    if race1 == 'not-specified' or race2 == 'not-specified':
        return 'not-specified'

    return 'more-than-one-race'


def role_type(role_id):
    if role_id == 'mo':
        return 'mom'
    elif role_id == 'fa':
        return 'dad'
    elif role_id[0] == 'p':
        return 'prb'
    elif role_id[0] == 's' or role_id[0] == 'x':
        return 'sib'


# remove annoying characters
# https://stackoverflow.com/questions/6609895/efficiently-replace-bad-characters
ANNOYING_CHARACTERS = {
    '\xc2\x82': ',',        # High code comma
    '\xc2\x84': ',,',       # High code double comma
    '\xc2\x85': '...',      # Tripple dot
    '\xc2\x88': '^',        # High carat
    '\xc2\x91': "'",     # Forward single quote
    '\xc2\x92': "'",     # Reverse single quote
    '\xc2\x93': '"',     # Forward double quote
    '\xc2\x94': '"',     # Reverse double quote
    '\xc2\x95': ' ',
    '\xc2\x96': '-',        # High hyphen
    '\xc2\x97': '--',       # Double hyphen
    '\xc2\x99': ' ',
    '\xc2\xa0': ' ',
    '\xc2\xa6': '|',        # Split vertical bar
    '\xc2\xab': '<<',       # Double less than
    '\xc2\xbb': '>>',       # Double greater than
    '\xc2\xbc': '1/4',      # one quarter
    '\xc2\xbd': '1/2',      # one half
    '\xc2\xbe': '3/4',      # three quarters
    '\xca\xbf': '\x27',     # c-single quote
    '\xcc\xa8': '',         # modifier - under curve
    '\xcc\xb1': '',         # modifier - under line
    '\xe2\x89\xa4': '<=',
    '\xe2\x89\xa5': '>=',
    '\xbd': ' 1/2',
    '\x91': "'",
    '\x92': "'",
    '\x93': '"',
    '\x94': '"',
    '\x95': ' ',
    '\x96': '-',        # High hyphen
    '\x97': '--',       # Double hyphen
    '\x99': ' ',
}


def remove_annoying_characters(text):
    def replace_chars(match):
        char = match.group(0)
        return ANNOYING_CHARACTERS[char]

    return re.sub(
        '(' + '|'.join(list(ANNOYING_CHARACTERS.keys())) + ')',
        replace_chars, text
    )

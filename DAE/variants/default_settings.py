'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import unicode_literals
import os

DATA_DIR = os.environ.get(
    "DAE_DATA_DIR",
    None
)

CONFIG_FILE = os.environ.get(
    "DAE_CONFIG_FILE",
    "variants.conf"
)

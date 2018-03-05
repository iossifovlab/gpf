'''
Created on Feb 7, 2018

@author: lubo
'''
import os

DATA_DIR = os.environ.get(
    "DAE_DATA_DIR",
    "/home/lubo/Work/seq-pipeline/data-raw-dev/"
)

CONFIG_FILE = os.environ.get(
    "DAE_CONFIG_FILE",
    "variants.conf"
)

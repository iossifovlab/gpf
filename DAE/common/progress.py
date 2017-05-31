'''
Created on May 26, 2017

@author: lubo
'''
import sys


def progress(verbose=1):
    if verbose:
        sys.stderr.write('.')


def progress_nl(verbose=1):
    if verbose:
        sys.stderr.write('\n')

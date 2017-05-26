'''
Created on May 26, 2017

@author: lubo
'''
import sys


def progress(verbose):
    if verbose:
        sys.stderr.write('.')


def progress_nl(verbose):
    if verbose:
        sys.stderr.write('\n')

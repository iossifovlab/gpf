#!/usr/bin/python

from __future__ import unicode_literals
import hotshot.stats
import sys

stats = hotshot.stats.load(sys.argv[1])
# stats.strip_dirs()
stats.sort_stats('time', 'calls')
stats.print_stats(100)

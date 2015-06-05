#!/bin/env python

import sys

def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

hdL = sys.stdin.readline()
print hdL[(find_nth(hdL,"\t",1)+1):],
for l in sys.stdin:
   print l[(find_nth(l,"\t",3)+1):],

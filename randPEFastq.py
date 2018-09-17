#!/usr/bin/python

from __future__ import print_function
from __future__ import division
from builtins import range
from past.utils import old_div
import random
import sys

def write_random_records(fqa, fqb, N=100000):
	""" get N random headers from a fastq file without reading the
	whole thing into memory"""
	records = old_div(sum(1 for _ in open(fqa)), 4)

	print("there are %d records" % (records))

	rand_records = sorted([random.randint(0, records - 1) for _ in range(N)])

	fha, fhb = open(fqa),  open(fqb)
	suba, subb = open(fqa + ".subset", "w"), open(fqb + ".subset", "w")
	rec_no = - 1
	for rr in rand_records:

		while rec_no < rr:
    			rec_no += 1       
			for i in range(4): fha.readline()
			for i in range(4): fhb.readline()
		for i in range(4):
    			suba.write(fha.readline())
			subb.write(fhb.readline())
		rec_no += 1 # (thanks @anderwo)

	print("wrote to %s, %s" % (suba.name, subb.name), file=sys.stderr)

if __name__ == "__main__":
	write_random_records(sys.argv[1], sys.argv[2], int(sys.argv[3]))

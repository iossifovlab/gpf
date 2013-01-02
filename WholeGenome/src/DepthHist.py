#!/bin/env /data/software/local/bin/python


# filename : 
# generated : 
# author(s) : 
# origin : CSHL
# purpose : 
# caveates: 

import sys

buff = [ [], [], [], [] ];
hdr = sys.stdin.readline()

for line in sys.stdin:
	data = line.strip().split("\t")
	for c in range(3,7):
		d = int(data[c])
		while d >= len(buff[c-3]):
			buff[c-3].append(0)
			
		buff[c-3][d]+=1

D = max([len(x) for x in buff])
for d in range(D):
	print "\t".join([ str(buff[s][d]) if d<len(buff[s]) else "0" for s in range(4) ])
	

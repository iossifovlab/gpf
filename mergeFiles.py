#!/bin/env python


from __future__ import print_function
import optparse, os, sys, math

usage = "usage: %prog [options]"
parser = optparse.OptionParser(usage=usage)

parser.add_option("-r", "--ref", dest="refFile", default="",
                 metavar="REFERENCE", help="reference file")
parser.add_option("-i", "--input", dest="inputFile", default="",
                 metavar="INPUT", help="input File")
parser.add_option("-o", "--output", dest="outputFile", default="",
                  metavar="OUTPUT", help="output FILE")

ox, args = parser.parse_args()

outfile = open( ox.outputFile, 'w' )

ref = list()
try:
   with open( ox.refFile, 'r' ) as reffile:
	line = reffile.readline()

	outfile.write( line )

	for line in reffile:
		line = line.strip();
		x = line.split('\t')

		ref.append( (' '*(15-len(x[0]))) + x[0]+'\t'+ (' '*(15-len(x[1])))+ x[1] +'\t'+ x[2] )
		#print ref
except IOError as e:
	print(e)
	sys.exit(1)

try:
   with open( ox.inputFile, 'r' ) as infile:
	line = infile.readline()

	for line in infile:
		line = line.strip()
		x = line.split('\t')

		ref.append( (' '*(15-len(x[0]))) + x[0]+'\t'+ (' '*(15-len(x[1])))+ x[1] +'\t'+ x[2] )
except IOError as e:
	print(e)
	sys.exit(1)

ref.sort()
extra = list()
for line in ref:
	x = line.split('\t')
	
	ch = x[0].strip(' ')
	
	try:
		int(ch)
		outfile.write( ch +'\t'+ x[1].strip(' ') +'\t'+ x[2] +'\n' )
	except:
		extra.append( line )
	#outfile.write( line +'\n' )

for line in extra:
	x = line.split('\t')
	
	ch = x[0].strip(' ')
	
	outfile.write( ch +'\t'+ x[1].strip(' ') +'\t'+ x[2] +'\n' )
	#outfile.write( line +'\n' )

outfile.close()

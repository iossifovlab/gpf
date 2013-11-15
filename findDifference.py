#!/bin/env python 


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

ref = set()
try:
   with open( ox.refFile, 'r' ) as reffile:
	line = reffile.readline()
	for line in reffile:
		line = line.strip();
		x = line.split('\t')

		ref.add( x[0]+'>'+x[1] )
except IOError, e:
	print e
	sys.exit(1)

try:
   with open( ox.inputFile, 'r' ) as infile:
	outfile = open( ox.outputFile, 'w' )

	line = infile.readline()
	outfile.write( line )

	for line in infile:
		line = line.strip()
		x = line.split('\t')

		code = x[0] +'>'+ x[1]
		if code in ref:
			continue

		outfile.write( x[0] +'\t'+ x[1] +'\n' )
		#outfile.write( line +'\n' )

	outfile.close()
except IOError, e:
	print e
	sys.exit(1)

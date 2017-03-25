#!/usr/bin/env python

import sys, commands, optparse

def main():
   #copy of options for dnv2DAEc.py
   usage = "usage: %prog [options]" # <pedFile> <data VCF file>"
   parser = optparse.OptionParser(usage=usage)
   #parser.add_option("-p", "--pedFile", dest="pedFile", default="xxx.txt",
   #     metavar="pedFile", help="Pedgree file with certain format")
   #parser.add_option("-d", "--dataFile", dest="dataFile", default="data/SF_denovo_all_lofdmis_excl4.csv",
   #     metavar="dataFile", help="text format variant file")

   parser.add_option("-x", "--project", dest="project", default="VIP", metavar="project", help="project name [defualt:VIP]")
   parser.add_option("-l", "--lab", dest="lab", default="SF", metavar="lab", help="lab name [defualt:SF]")

   parser.add_option("-o", "--outputPrefix", dest="outputPrefix", default="dnv",
        metavar="outputPrefix", help="prefix of output 'de novo' file")
   parser.add_option("-m", "--delimiter", dest="delimiter", default="\t", metavar="delimiter", help="lab name [defualt:tab]")
   #parser.add_option("-o", "--out", dest="outFile", default="output/SF_denovo_all_lofdmis_excl4.txt",
   #     metavar="outFile", help="de novo format variant file")
   #parser.add_option("-f", "--famOut", dest="famOut", default="output/famData.txt",
   #     metavar="famOut", help="famData file")

   #parser.add_option("-c", "--columNames", dest="columnNames", default="pId,chrom,pos,ref,alt",
   #     metavar="columnNames", help="column names for pId,chrom,pos,ref,alt [defualt:pId,chrom,pos,ref,alt]")
   parser.add_option("-i", "--personIdColumn", dest="personIdColumn", default="personId", \
			metavar="personIdColumn", help="column names for personId")
   parser.add_option("-c", "--chrColumn", dest="chrColumn", default="chr", metavar="chrColumn", \
			help="column names for chromosome")
   parser.add_option("-p", "--posColumn", dest="posColumn", default="pos", metavar="posColumn", \
			help="column names for position")
   parser.add_option("-r", "--refColumn", dest="refColumn", default="ref", metavar="refColumn", \
			help="column names for reference allele")
   parser.add_option("-a", "--altColumn", dest="altColumn", default="alt", metavar="altColumn", \
			help="column names for altenative allele")

   ox, args = parser.parse_args()

   #main conversion
   columnNames = '{:s},{:s},{:s},{:s},{:s}'.format( ox.personIdColumn, \
					        ox.chrColumn, ox.posColumn, ox.refColumn, ox.altColumn )
   #cmd = ' '.join( ['dnv2DAEc.py', '-p', ox.pedFile, '-d', ox.dataFile, '-x', ox.project, '-l', ox.lab, \
   cmd = ' '.join( ['dnv2DAEc.py', '-p', args[0], '-d', args[1], '-x', ox.project, '-l', ox.lab, \
			'-o', 'x0.'+ox.outputPrefix, '-m', '"{:s}"'.format( ox.delimiter ), \
			'-c', '"{:s}"'.format(columnNames), ' > dnv.'+ox.outputPrefix+'.SUB.txt'] )
			#'-c', '"{:s}"'.format(ox.columnNames), ' > dnv.'+ox.outputPrefix+'.SUB.txt'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   if status: raise Exception("FAILURE AT: " + cmd)

   #tmp families info to target info
   cmd = ' '.join( ['\\mv', 'x0.'+ox.outputPrefix+'-families.txt', ox.outputPrefix+'-families.txt'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   if status: raise Exception("FAILURE AT: " + cmd)

   #annotate variant
   cmd = ' '.join( ['annotate_variants.py -x location -v variant ', 'x0.'+ox.outputPrefix+'.txt', 'x1.'+ox.outputPrefix+'.txt'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   if status: raise Exception("FAILURE AT: " + cmd)

   #annotate freqency
   cmd = ' '.join( ['annotateFreqTransm.py', 'x1.'+ox.outputPrefix+'.txt', 'direct > ', ox.outputPrefix+'.txt'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out 

   #remove tmp files
   cmd = ' '.join( ['\\rm', 'x?.'+ox.outputPrefix+'.txt*'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   if status: raise Exception("FAILURE AT: " + cmd)

if __name__ == "__main__":
   main()

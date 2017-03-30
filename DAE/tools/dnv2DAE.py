#!/usr/bin/env python

import sys, commands, optparse

def main():
   #copy of options for dnv2DAEc.py
   usage = "usage: %prog [options] <families pedigree file> <list of de novos file>"
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
   parser.add_option("-w", "--locColumn", dest="locColumn", default="",    metavar="locColumn", \
                        help="column names for location chr:pos format")
   parser.add_option("-c", "--chrColumn", dest="chrColumn", default="chr", metavar="chrColumn", \
			help="column names for chromosome")
   parser.add_option("-p", "--posColumn", dest="posColumn", default="pos", metavar="posColumn", \
			help="column names for position")
   parser.add_option("-r", "--refColumn", dest="refColumn", default="ref", metavar="refColumn", \
			help="column names for reference allele")
   parser.add_option("-a", "--altColumn", dest="altColumn", default="alt", metavar="altColumn", \
			help="column names for altenative allele")

   ox, args = parser.parse_args()

   tExt = lambda xxx: '.zZqZz{:d}'.format(xxx) if isinstance(xxx,int) else '.zZqZz{:s}'.format(xxx)
   #tmp files' extension

   #main conversion
   columnNames = '{:s},{:s},{:s},{:s},{:s},{:s}'.format( ox.personIdColumn, ox.locColumn, \
					        ox.chrColumn, ox.posColumn, ox.refColumn, ox.altColumn )
   #cmd = ' '.join( ['dnv2DAEc.py', '-p', ox.pedFile, '-d', ox.dataFile, '-x', ox.project, '-l', ox.lab, \
   cmd = ' '.join( ['dnv2DAEc.py', '-p', args[0], '-d', args[1], '-x', ox.project, '-l', ox.lab, \
			'-o', ox.outputPrefix+tExt(0), '-m', '"{:s}"'.format( ox.delimiter ), \
			'-c', '"{:s}"'.format(columnNames), ' > '+ox.outputPrefix+'-complex.txt'] )
			#'-c', '"{:s}"'.format(ox.columnNames), ' > '+ox.outputPrefix+'-complex.txt'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   if status: raise Exception("FAILURE AT: " + cmd)
   #tmp families info to target info
   cmd = ' '.join( ['\\mv', ox.outputPrefix+tExt(0)+'-families.txt', ox.outputPrefix+'-families.txt'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   if status: raise Exception("FAILURE AT: " + cmd)
   #annotate variant
   cmd = ' '.join( ['annotate_variants.py -x location -v variant ', ox.outputPrefix+tExt(0)+'.txt', ox.outputPrefix+tExt(1)+'.txt'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   if status: raise Exception("FAILURE AT: " + cmd)
   #annotate freqency
   cmd = ' '.join( ['annotateFreqTransm.py', ox.outputPrefix+tExt(1)+'.txt', 'direct > ', ox.outputPrefix+'.txt'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out 
   if status: raise Exception("FAILURE AT: " + cmd)
   #remove tmp files
   cmd = ' '.join( ['\\rm', ox.outputPrefix+tExt('*')+'.txt*'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   if status: raise Exception("FAILURE AT: " + cmd)

if __name__ == "__main__":
   main()

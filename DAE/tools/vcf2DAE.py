#!/usr/bin/env python

import sys, commands, optparse

def main():
   #copy of options for vcf2DAEc.py
   usage = "usage: %prog [options]"
   parser = optparse.OptionParser(usage=usage)
   #parser.add_option("-p", "--pedFile", dest="pedFile", default="data/svip.ped",
   #     metavar="pedFile", help="pedigree file and family-name should be mother and father combination, not PED format")
   #parser.add_option("-d", "--dataFile", dest="dataFile", default="data/svip-FB-vars.vcf.gz",
   #     metavar="dataFile", help="VCF format variant file")

   parser.add_option("-x", "--project", dest="project", default="VIP", metavar="project", help="project name [defualt:VIP")
   parser.add_option("-l", "--lab", dest="lab", default="SF", metavar="lab", help="lab name [defualt:SF")

   parser.add_option("-o", "--outputPrefix", dest="outputPrefix", default="transmission",
        metavar="outputPrefix", help="prefix of output transmission file")

   parser.add_option("-m", "--minPercentOfGenotypeSamples", dest="minPercentOfGenotypeSamples", type=float, default=25.,
        metavar="minPercentOfGenotypeSamples", help="threshold percentage of gentyped samples to printout [default: 25]")
   parser.add_option("-t", "--tooManyThresholdFamilies", dest="tooManyThresholdFamilies", type=int, default=10,
        metavar="tooManyThresholdFamilies", help="threshold for TOOMANY to printout [defaylt: 10]")

   ox, args = parser.parse_args()
   #main procedure
   #cmd = ' '.join( ['vcf2DAEc.py', '-p', ox.pedFile, '-d', ox.dataFile, '-x', ox.project, '-l', ox.lab, \
   cmd = ' '.join( ['vcf2DAEc.py', '-p', args[0], '-d', args[1], '-x', ox.project, '-l', ox.lab, \
			'-o', 'x0.'+ox.outputPrefix, '-m', str(ox.minPercentOfGenotypeSamples), \
			'-t', str(ox.tooManyThresholdFamilies), ' > trans.'+ox.outputPrefix+'.SUB.txt'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   #family file 
   cmd = ' '.join( ['\\mv', 'x0.'+ox.outputPrefix+'-families.txt', ox.outputPrefix+'-families.txt'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   #HW
   cmd = ' '.join( ['hw.py -c', 'x0.'+ox.outputPrefix+'.txt', 'x1.'+ox.outputPrefix+'.txt'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   #TOOMANY bgzip
   cmd = ' '.join( ['\\mv', 'x0.'+ox.outputPrefix+'-TOOMANY.txt', ox.outputPrefix+'-TOOMANY.txt;', \
		    'bgzip -f', ox.outputPrefix+'-TOOMANY.txt;', \
		    '\\mv', ox.outputPrefix+'-TOOMANY.txt.gz', ox.outputPrefix+'-TOOMANY.txt.bgz;', \
		    'tabix -S 1 -s 1 -b 2 -e 2', ox.outputPrefix+'-TOOMANY.txt.bgz'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   #annotate
   cmd = ' '.join( ['annotate_variants.py -c chr -p position -v variant ', 'x1.'+ox.outputPrefix+'.txt', \
		    '| bgzip -c > x2.'+ox.outputPrefix+'.txt.bgz'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   #annotate freq
   cmd = ' '.join( ['annotateFreqTransm.py', 'x2.'+ox.outputPrefix+'.txt.bgz', 'iterative ', \
		  '| bgzip -c > ', ox.outputPrefix+'.txt.bgz;', \
		    'tabix -S 1 -s 1 -b 2 -e 2', ox.outputPrefix+'.txt.bgz'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out
   #remove tmp files
   cmd = ' '.join( ['\\rm', 'x?.'+ox.outputPrefix+'.txt*'] )
   status, out = commands.getstatusoutput( cmd )
   print status, out

if __name__ == "__main__":
   main()

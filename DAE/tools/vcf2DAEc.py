#!/usr/bin/env python

import optparse, sys, os
import pysam, numpy
from collections import namedtuple, defaultdict
from itertools import izip
import itertools

#from vcf2DAEutil import *
import variantFormat as vrtF
from ped2NucFam import *

##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=GQ,Number=1,Type=Float,Description="Genotype Quality, the Phred-scaled marginal (or unconditional) probability of the called genotype">
##FORMAT=<ID=GL,Number=G,Type=Float,Description="Genotype Likelihood, log10-scaled likelihoods of the data given the called genotype for each possible genotype generated from the reference and alternate alleles given the sample ploidy">
##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read Depth">
##FORMAT=<ID=RO,Number=1,Type=Integer,Description="Reference allele observation count">
##FORMAT=<ID=QR,Number=1,Type=Integer,Description="Sum of quality of the reference observations">
##FORMAT=<ID=AO,Number=A,Type=Integer,Description="Alternate allele observation count">
##FORMAT=<ID=QA,Number=A,Type=Integer,Description="Sum of quality of the alternate observations">
#
# [('GT', (0, 0)), ('AD', (8, 0)), ('DP', 8), ('GQ', 0), ('PL', (0, 0, 234))]
#   genotype	     		   read depth  GT qual

def getGQ( dx ):
   try:
	return list(dx['GQ'])
   except TypeError, e:
	return [dx['GQ']]
   except KeyError, e:
	if ('QR' in dx) and ('QA' in dx):
		return [dx['QR']] + list(dx['QA'])
	else:
		return []

def percentageGentype( data ):
   tlx = len(data.samples)
   clx = 0
   for k, v in data.samples.items():
	#print >> sys.stderr, v['GT'][0], v['GT']
	if v['GT'][0] == None: continue
	clx += 1

   return 100.*clx/tlx

def getGT( sample, data ):
   try:
   	dx = data.samples[sample]
   except KeyError, e:
	print sample, 'not found on ', sorted(data.samples.keys())
	exit(1)

   GQ  = getGQ( dx )

   GT  = numpy.zeros( (len(data.alts)+1,), dtype=numpy.int)
   cnt = numpy.zeros( (len(data.alts)+1,), dtype=numpy.int)

   if None in dx['GT']:
	return False, GT, cnt, GQ

   gt = list(dx['GT'])
   for ix in gt: GT[ix] += 1

   if ('RO' in dx) and ('AO' in dx):
	cnt[:] = [dx['RO']] + list(dx['AO'])
   elif 'AD' in dx:
	cnt[:] = list(dx['AD'])
   elif ('NR' in dx) and ('NV' in dx):
	#print data.ref, data.alts, dx['GT'], dx['NR'], dx['NV']
	try:
	   if (len(cnt[:]) == len(list(dx['NR']) + list(dx['NV']))):
	   	cnt[:] = list(dx['NR']) + list(dx['NV'])
	   else:
		for ix in list(dx['GT']):
		   if ix == 0:	cnt[ix] = dx['NR'][ix]
		   else:	cnt[ix] = dx['NV'][ix-1]
		#print data.ref, data.alts, dx['GT'], dx['NR'], dx['NV'], cnt
	except ValueError, e:
		pass
		print e, data.ref, data.alts, dx['GT'], dx['NR'], dx['NV']
		#cnt[:] = [dx['NR']] + list(dx['NV'])

   return True, GT, cnt, GQ

def getVrtFam( fam, data ):
   flag = True

   GT  = numpy.zeros( (len(fam), len(data.alts)+1,), dtype=numpy.int)
   cnt = numpy.zeros( (len(fam), len(data.alts)+1,), dtype=numpy.int)
   strx = []
   #print fam
   for n, pid in enumerate(fam):
	fx, gt, cx, gq = getGT( pid, data )

	if not fx: flag = False

	GT[n,:]  = gt
	cnt[n,:] = cx

	strx.append( '/'.join(map(str,gq)) )

   return flag, GT, cnt, ','.join(strx)

def array2str( mx, ix, delim='' ):
   n0, n1, n2 = mx[:,0], mx[:,ix], mx.sum(1)
   n2 = n2 - n0 - n1

   s0 = map( str, n0 )
   s1 = map( str, n1 )
   s2 = map( str, n2 )
   
   strx = delim.join( s0 ) +'/'+ delim.join( s1 )
   if sum(n2) > 0:
	strx += ('/'+ delim.join( s2 ))

   return strx

def fixNonAutoX( GT, fam, pInfo ):
   #Sex (1=male; 2=female; other=unknown)
   #assume [numFam]x[genotype count] and genotype are 0,1,2 
 
   #father
   if sum(GT[1,:]) == 2 and sum( GT[1,:] == 1 ) > 0:
	return False
   else:
	GT[1,GT[1,:]==2] = 1

   for n, pid in enumerate(fam[2:]):
	if pInfo[pid].sex != '1': continue

	ix = n+2
	if sum(GT[ix,:]) == 2 and sum( GT[ix,:] == 1 ) > 0:
 	       return False
	else:
        	GT[ix,GT[ix,:]==2] = 1

   return True

# possible hap state
def hapState( cn ):
   if cn == 0: return [0]
   if cn == 1: return [0,1]

   return [1]

# primitive version of checking de-novo
def isDenovo( st ):
   for ix in xrange(st.shape[1]):
	ms = hapState( st[0,ix] )
	fs = hapState( st[1,ix] )
	#print ms, fs
	ps = set([a+b for a, b in itertools.product(ms,fs)] )
	flag = sum([ x not in ps for x in st[2:,ix]])

	if flag > 0: return True

   return False

# output: dict[pos] = (out,str)
def printSome( output, pos=None, wsize=1000 ):
   if pos == None:
	for k in sorted(output.keys()):
		v = output[k]
		print >> v[0], v[1]

	output.clear()
	return

   dk = []
   for k in sorted(output.keys()):
	if k[0] > pos - wsize: break

	dk.append( k )
	v = output[k]
	print >> v[0], v[1]

   for k in dk:
	del output[k]

def main():
   #svip.ped
   #svip-FB-vars.vcf.gz, svip-PL-vars.vcf.gz, svip-JHC-vars.vcf.gz
   #pfile, dfile = 'data/svip.ped', 'data/svip-FB-vars.vcf.gz'
   usage = "usage: %prog [options]"
   parser = optparse.OptionParser(usage=usage)
   parser.add_option("-p", "--pedFile", dest="pedFile", default="data/svip.ped",
	metavar="pedFile", help="pedigree file and family-name should be mother and father combination, not PED format")
   parser.add_option("-d", "--dataFile", dest="dataFile", default="data/svip-FB-vars.vcf.gz",
        metavar="dataFile", help="VCF format variant file")

   parser.add_option("-x", "--project", dest="project", default="VIP", metavar="project", help="project name [defualt:VIP")
   parser.add_option("-l", "--lab", dest="lab", default="SF", metavar="lab", help="lab name [defualt:SF")

   parser.add_option("-o", "--outputPrefix", dest="outputPrefix", default="transmission",
        metavar="outputPrefix", help="prefix of output transmission file")

   parser.add_option("-m", "--minPercentOfGenotypeSamples", dest="minPercentOfGenotypeSamples", type=float, default=25.,
        metavar="minPercentOfGenotypeSamples", help="threshold percentage of gentyped samples to printout [default: 25]")
   parser.add_option("-t", "--tooManyThresholdFamilies", dest="tooManyThresholdFamilies", type=int, default=10,
        metavar="tooManyThresholdFamilies", help="threshold for TOOMANY to printout [defaylt: 10]")


   ox, args = parser.parse_args()
   pfile, dfile = ox.pedFile, ox.dataFile

   #print famFile
   #fInfo: each fam has mom, dad and child personal ID, old and new Ids
   #pInfo: each person has raw info from "PED" file
   fInfo, pInfo = procFamInfo( pfile )
   FAMOUT = ox.outputPrefix +'-families.txt'
   printFamData( fInfo, pInfo, proj=ox.project, lab=ox.lab, out=open(FAMOUT,'w') )

   if os.path.isfile( ox.outputPrefix +'.txt' ):
	print >> sys.stderr, ox.outputPrefix +'.txt: already exist'
	exit(1)

   #setup to print transmission files
   OUT = ox.outputPrefix +'.txt'
   TOOMANY = ox.outputPrefix +'-TOOMANY.txt'
   out = open( OUT, 'w' )
   outTOOMANY = open( TOOMANY, 'w' )

   print >> out, '\t'.join( 'chr,position,variant,familyData,all.nParCalled,all.prcntParCalled,all.nAltAlls,all.altFreq'.split(','))
   print >> outTOOMANY, '\t'.join( 'chr,position,variant,familyData'.split(',') )

   fam = [x for x in sorted(fInfo.keys())]
   vf = pysam.VariantFile( dfile )
   
   digitP = lambda x: '{:.4f}'.format(x)
   cchr = ''
   output = {}
   for rx in vf:
	pgt = percentageGentype( rx )
	if pgt < ox.minPercentOfGenotypeSamples: continue
	#print >> sys.stderr, 'pcntg', pgt

	chrom = rx.chrom
	px, vx = vrtF.vcf2cshlFormat2( rx.pos, rx.ref, rx.alts ) #callVariant( rx.pos, rx.ref, rx.alts )
	
	#print output and make it empty
	if cchr != chrom:
		printSome( output )
		cchr = chrom
	#reduce burden of computer memory
	if len(output) > 10000:
		printSome( output, pos=rx.pos )

	nonAutoX = False
	if chrom == 'X' and (not vrtF.isPseudoAutosomalX(px[0])): nonAutoX = True

	dx = []
	#save ok families, check whether autosomal or de novo
	for fid in fam:
		flag, GT, cnt, qual = getVrtFam( fInfo[fid]['ids'], rx )
		#if 4235521 in px and fid == '14752.x6.m0-14752.x8':
		#	print fInfo[fid]
		#	print fid, flag, array2str(GT,1,delim=' '), '-', array2str(cnt,1,delim=' '), qual
		if not flag: continue #print px, vx, rx.chrom, rx.pos, rx.ref, rx.alts

		if nonAutoX:
			flag = fixNonAutoX( GT, fInfo[fid]['ids'], pInfo )
			if not flag: continue

		if isDenovo( GT ):
			#print GT
			continue

		dx.append( [fInfo[fid]['newFid'], GT, cnt, qual] )
	#skip none found
	if len(dx) < 1: continue
	#skip if failed families are more than certain threshold
	#if len(dx)/(1.*len(fam))*100. < ox.minPercentOfGenotypeFamilies: continue

	nPC = 2*len(dx)
	nPcntC = (1.*nPC)/(2*len(fam))*100.
	for n, (p,v) in enumerate(izip( px, vx )):
	   ix = n+1
	   #some occasion '*' as one of alternatives
	   if v.find( '*' ) >= 0: continue 

	   strx = []
	   cAlt, tAll = 0, 0
	   for x in dx:
		if sum(x[1][:,ix]) < 1: continue

		cAlt += sum(x[1][:2,ix])

		strx.append( x[0] +':'+ array2str(x[1],ix,delim='') +':'+ array2str(x[2],ix,delim=' '))
		#	     +':'+ x[3] )

	   fC = len(strx)
	   if fC < 1: continue

	   strx = ';'.join( strx )
	   #print strx
	   #assume that all of auto have 2 copy, X non-Autosomal 1, and Y male(1) and female(0)
	   if nonAutoX:
		tAll = 3*(nPC/2)
	   elif chrom == 'Y':
		continue
		#tAll = nPC/2
	   else:
		tAll = 2*nPC
	   #chr,position,variant,familyData,all.nParCalled,all.prcntParCalled,all.nAltAlls,all.altFreq
	   #fid:bestState:counts:qualityScore
	   #11948:2112/0110:40 20 20 40/0 20 20 0:0:0;... writing format
	   freqAlt = (1.*cAlt)/tAll*100.

	   pix = 0
	   while (p,pix) in output: pix += 1

	   if v.startswith( 'SUB' ):
		print >> sys.stdout, '\t'.join( [chrom, str(p), v, strx, str(nPC), digitP(nPcntC), str(cAlt),digitP(freqAlt)])
		continue

	   if fC >= ox.tooManyThresholdFamilies:
		output[(p,pix)] = (out, '\t'.join( [chrom, str(p), v, 'TOOMANY', str(nPC), digitP(nPcntC), str(cAlt), digitP(freqAlt)]) )
		output[(p,pix+1)] = (outTOOMANY, '\t'.join( [chrom, str(p), v, strx] ) )
	   else:
		output[(p,pix)] = (out, '\t'.join( [chrom, str(p), v, strx, str(nPC), digitP(nPcntC), str(cAlt),digitP(freqAlt)]) )

   printSome( output )

if __name__ == "__main__":
   main()

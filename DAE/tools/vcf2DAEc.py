#!/usr/bin/env python

from __future__ import print_function
from builtins import map
from builtins import str
from builtins import range
import optparse, sys, os
import pysam, numpy
from collections import namedtuple, defaultdict

import itertools

#from vcf2DAEutil import *
import variantFormat as vrtF
from ped2NucFam import *
import vrtIOutil as vIO

def percentageGentype( data ):
   tlx = len(data.samples)
   clx = 0
   for k, v in list(data.samples.items()):
	#print >> sys.stderr, v['GT'][0], v['GT']
	if v['GT'][0] is None: continue
	clx += 1

   return 100.*clx/tlx

def getGT( sample, data ):
   try:
   	dx = data.samples[sample]
   except KeyError as e:
	print(sample, 'not found on ', sorted(data.samples.keys()))
	exit(1)

   #GQ  = getGQ( dx )

   GT  = numpy.zeros( (len(data.alts)+1,), dtype=numpy.int)
   cnt = numpy.zeros( (len(data.alts)+1,), dtype=numpy.int) - 1 # default -1 for No Info

   if None in dx['GT']: #[0] is None:
	return False, GT, cnt#, GQ

   gt = list(dx['GT'])
   for ix in gt: GT[ix] += 1

   cx = vIO.getCount(dx)
   if len(cx) == len(cnt):	cnt[:] = cx
   #if cx and cnt not agree, then ignore

   return True, GT, cnt #, GQ

#add more data on fam Info
def makeFamInfoConv( fInfo, pInfo ):
   for k, v in list(fInfo.items()):
        lx = len(v['ids'])
        sx = numpy.zeros( (lx,), dtype=numpy.int )
        for n,mx in enumerate(v['newIds']):
                s = pInfo[mx].sex
                if s == '1': sx[n] = 1
        v['isMale'] = sx

        cl = len(v['famaIndex'])
        idxMF = numpy.zeros( (cl,3,), dtype=numpy.int )
	nC = list(range(lx))
        for n,(a,b) in enumerate(v['famaIndex'].items()):
                idxMF[n,:] = [a,b.fa,b.ma]
                nC.remove( a )
        v['iFM'] = idxMF
	v['notChild'] = numpy.array(nC)

   #print fInfo

def getVrtFam( fam, data ):
   flag = True

   GT  = numpy.zeros( (len(fam), len(data.alts)+1,), dtype=numpy.int)
   cnt = numpy.zeros( (len(fam), len(data.alts)+1,), dtype=numpy.int)
   #strx = []
   #print fam
   for n, pid in enumerate(fam):
	#fx, gt, cx, gq = getGT( pid, data )
	fx, gt, cx = getGT( pid, data )

	if not fx: flag = False

	GT[n,:]  = gt
	cnt[n,:] = cx

	#strx.append( '/'.join(map(str,gq)) )
   #print GT
   return flag, GT, cnt#, ','.join(strx)

def array2str( mx, ix, delim='' ):
   n0, n1, n2 = mx[:,0], mx[:,ix], mx.sum(1)
   n2 = n2 - n0 - n1

   s0 = list(map( str, n0 ))
   s1 = list(map( str, n1 ))
   s2 = list(map( str, n2 ))
   
   strx = delim.join( s0 ) +'/'+ delim.join( s1 )
   if sum(n2) > 0:
	strx += ('/'+ delim.join( s2 ))

   return strx

def fixNonAutoX( GT, isM ): #fam, pInfo ):
   #Sex (1=male; 2=female; other=unknown)
   #assume [numFam]x[genotype count] and genotype are 0,1,2 

   for n, im in enumerate(isM):
        if im == 0: continue #female

        if sum(GT[n,:]) == 2 and sum( GT[n,:] == 1 ) > 0:
               return False
        else:
                GT[n,GT[n,:]==2] = 1

   return True
 
# possible hap state
def hapState( cn ):
   if cn == 0: return [0]
   if cn == 1: return [0,1]

   return [1]

# mendel State
#
#(fa, ma, child) copy number
#       (ma,fa):(child) -- number of alleles
mStat = {  \
  #regular autosome 2 copies for all
  (2,2,2):{\
          (2,2):[2],  (2,1):[1,2],  (2,0):[1],  \
          (1,2):[1,2],(1,1):[0,1,2],(1,0):[0,1],\
          (0,2):[1],  (0,1):[0,1],  (0,0):[0] },\
  #X and male child, only from ma
  (1,2,1):{\
          (1,2):[1], (1,1):[0,1], (1,0):[0],   \
          (0,2):[1], (0,1):[0,1], (0,0):[0] }, \
  #X and female child
  (1,2,2):{\
          (1,2):[2], (1,1):[1,2], (1,0):[1],  \
          (0,2):[1], (0,1):[0,1], (0,0):[0] } }

# primitive version of checking de-novo
# autosome
def isDenovo( st, fm ): # fm : fa and ma index 
   assert sum(st.sum(1) != 2) == 0, 'copy number assume to be 2 for all'
   #mendel state for copy number 2 for all
   mdl = mStat[(2,2,2)]
   #all of them have ref state
   if sum(st[:,0] != 2) == 0: return False

   for c,f,m in fm: #fa ma child index
        for n,s in enumerate(st[c,:]):
           if s not in mdl[(st[f,n],st[m,n])]:
                #print st
                return True
           #print f,m,c,n,s, (st[f,n],st[m,n])

   return False

def isDenovoNonAutosomalX( st, fm, isM ): # fm : fa and ma index, isM: is Male array of 0 1(True) 
   assert sum(st.sum(1) != (2-isM)) == 0, 'copy number assume to be 2 for female, '+ \
                                          'and 1 for male male({:s}) copy({:s})'.format( \
                                          ','.join(map(str,isM)), ','.join( ['/'.join(map(str,s)) for s in st] ) )
   #mendel state for copy number, accordingly 
   mdl = [mStat[(1,2,2)],mStat[(1,2,1)]]
   #all of them have ref state
   if sum(st[:,0] != (2-isM)) == 0:
        #print 'ref only', ','.join( ['/'.join(map(str,s)) for s in st] ), ','.join(map(str,isM))
        return False
   
   for c,f,m in fm: #fa ma child index
        for n,s in enumerate(st[c,:]):
           if s not in mdl[isM[c]][(st[f,n],st[m,n])]:
                return True
           #print f,m,c,n,s, (st[f,n],st[m,n])

   return False

# output: dict[pos] = (out,str)
def printSome( output, pos=None, wsize=1000 ):
   if pos == None:
	for k in sorted(output.keys()):
	        v = output[k]
	        print(v[1], file=v[0])

	output.clear()
	return

   dk = []
   for k in sorted(output.keys()):
	if k[0] > pos - wsize: break

	dk.append( k )
	v = output[k]
	print(v[1], file=v[0])

   for k in dk:
	del output[k]

def famInVCF( fInfo, vcfs ):
   fam = []
   for fid in sorted(fInfo.keys()):
        flag = False

	mm = []
        for sm in fInfo[fid]['ids']:
	   if sm in vcfs: continue

	   flag = True
	   mm.append( sm )

	if flag:
	   print('\t'.join( ['family',  fid, 'notComplete', 'missing', ','.join( mm )] ), file=sys.stderr)
	   continue

        fam.append(fid)

   return fam

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

   parser.add_option("-s", "--missingInfoAsNone", action="store_true", dest="missingInfoAsNone", default=False,
                  metavar="missingInfoAsNone", help="missing sample Genotype will be filled with 'None' for many VCF files input")

   ox, args = parser.parse_args()
   pfile, dfile = ox.pedFile, ox.dataFile

   missingInfoAsRef = True
   if ox.missingInfoAsNone:
	missingInfoAsRef = False#; print NNN

   #print famFile
   #fInfo: each fam has mom, dad and child personal ID, old and new Ids
   #pInfo: each person has raw info from "PED" file
   fInfo, pInfo = procFamInfo( pfile )
   #add more info to fInfo such as 
   #    notChild: who is not children
   #    iFM     : fa and ma index for each child in families
   #    isMale  : sex info in the order of ids and newIds (they have the same order)
   makeFamInfoConv( fInfo, pInfo )

   if os.path.isfile( ox.outputPrefix +'.txt' ):
	print(ox.outputPrefix +'.txt: already exist', file=sys.stderr)
	exit(1)

   #setup to print transmission files
   OUT = ox.outputPrefix +'.txt'
   TOOMANY = ox.outputPrefix +'-TOOMANY.txt'
   out = open( OUT, 'w' )
   outTOOMANY = open( TOOMANY, 'w' )

   print('\t'.join( 'chr,position,variant,familyData,all.nParCalled,all.prcntParCalled,all.nAltAlls,all.altFreq'.split(',')), file=out)
   print('\t'.join( 'chr,position,variant,familyData'.split(',') ), file=outTOOMANY)

   #fam = [x for x in sorted(fInfo.keys())]
   #vf = pysam.VariantFile( dfile )
   vf = vIO.vcfFiles( dfile, missingInfoAsRef=missingInfoAsRef )
   fam = famInVCF( fInfo, vf )

   #print family Info in a format
   FAMOUT = ox.outputPrefix +'-families.txt'
   printFamData( fInfo, pInfo, proj=ox.project, lab=ox.lab, listFam=fam, out=open(FAMOUT,'w') )

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
                fIx = fInfo[fid]
	        #flag, GT, cnt, qual = getVrtFam( fIx['ids'], rx )
		flag, GT, cnt = getVrtFam( fIx['ids'], rx )
	        #if 4235521 in px and fid == '14752.x6.m0-14752.x8':
	        #       print fInfo[fid]
	        #       print fid, flag, array2str(GT,1,delim=' '), '-', array2str(cnt,1,delim=' '), qual
	        if not flag: continue #print px, vx, rx.chrom, rx.pos, rx.ref, rx.alts

	        if nonAutoX:
	                flag = fixNonAutoX( GT, fIx['isMale'] ) #fInfo[fid]['ids'], pInfo )
	                if not flag: continue #fail to fix

                        flag = isDenovoNonAutosomalX( GT, fIx['iFM'], fIx['isMale'] )
                        if flag: continue # denovo
                else:
	                flag = isDenovo( GT, fIx['iFM'] ) #isDenovo( GT ):
	                #print GT
	                if flag: continue # denovo

                #NOTE: main data set
	        #dx.append( [fIx['newFid'], GT, cnt, qual] )
                dx.append( [fIx['newFid'], GT, cnt, fIx['notChild']] )
                #notChild(index who is not child of any in this family)

	#NOTE: skip none found
	if len(dx) < 1: continue
	#skip if failed families are more than certain threshold
	#if len(dx)/(1.*len(fam))*100. < ox.minPercentOfGenotypeFamilies: continue

	nPC = 2*len(dx)
	nPcntC = (1.*nPC)/(2*len(fam))*100.
	for n, (p,v) in enumerate(zip( px, vx )):
	   ix = n+1
           # ref is index 0 and vx (variants) has only alternatives

	   #some occasion '*' as one of alternatives
	   if v.find( '*' ) >= 0: continue 

	   strx = []
	   cAlt, tAll = 0, 0
	   for (fid,GT,cnt,nCi) in dx: #dx: fid, GT, cnt, notChild(index who is not child of any in this family)
                #assume that all the ill-regualr genotype for X Y are correct
                #assume that all of auto have 2 copy, X non-Autosomal 1, and Y male(1) and female(0)
                tAll += sum(GT[nCi,:].sum(1))

	        if sum(GT[:,ix]) < 1: continue

	        cAlt += sum(GT[nCi,ix])
                # only concern about non children

	        strx.append( fid +':'+ array2str(GT,ix,delim='') +':'+ array2str(cnt,ix,delim=' '))

	   fC = len(strx)
	   if fC < 1: continue

	   strx = ';'.join( strx )
	   #print strx
	    
	   #chr,position,variant,familyData,all.nParCalled,all.prcntParCalled,all.nAltAlls,all.altFreq
	   #fid:bestState:counts:qualityScore
	   #11948:2112/0110:40 20 20 40/0 20 20 0:0:0;... writing format
	   freqAlt = (1.*cAlt)/tAll*100.

	   #pix = 0
	   #while (p,pix) in output: pix += 1

	   if v.startswith( 'complex' ) or (p,v) in output:
	        print('\t'.join( [chrom, str(p), v, strx, str(nPC), digitP(nPcntC), str(cAlt),digitP(freqAlt)]), file=sys.stdout)
	        continue

	   if fC >= ox.tooManyThresholdFamilies:
	        output[(p,v)] = (out, '\t'.join( [chrom, str(p), v, 'TOOMANY', str(nPC), digitP(nPcntC), str(cAlt), digitP(freqAlt)]) )
	        output[(p,v+'*')] = (outTOOMANY, '\t'.join( [chrom, str(p), v, strx] ) )
	   else:
	        output[(p,v)] = (out, '\t'.join( [chrom, str(p), v, strx, str(nPC), digitP(nPcntC), str(cAlt),digitP(freqAlt)]) )

   printSome( output )

if __name__ == "__main__":
   main()

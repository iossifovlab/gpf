#!/usr/bin/env python

from __future__ import print_function
import optparse, sys, os
import pysam, numpy
from collections import namedtuple, defaultdict
from itertools import izip

#from vcf2DAEutil import *
import variantFormat as vrtF
from ped2NucFam import *

#pedInfo = namedtuple( 'PED', 'fid,pid,fa,ma,sex,phenotype'.split(',') )
#pidInfo = namedtuple( 'PID', 'fid,fa,ma,sex,phenotype'.split(',') )
#Family ID
#Individual ID
#Paternal ID
#Maternal ID
#Sex (1=male; 2=female; other=unknown)
#Phenotype 
#    -9 missing 
#     0 missing
#     1 unaffected
#     2 affected

def procLine( line, delimiter="\t" ):
   if delimiter == "\t":
	return line.strip('\n').split(delimiter)

   terms = line.strip('\n').split('"')
   #print line.strip('\n')
   ret = []
   for n, rx in enumerate(terms):
	if n % 2 == 0:
		tmp = [x for x in rx.split(',')]
		if rx[0]  == ',': tmp = tmp[1:]
		if rx[-1] == ',': tmp = tmp[:-1]	
		ret += tmp
		continue

	ret.append( rx )

   return ret

def childState( ped ):
   strx = ''
   if ped.phenotype == '1':
	strx += 'sib'
   elif ped.phenotype == '2':
	strx += 'prb'
   else:
	strx += 'na'
   #Sex (1=male; 2=female; other=unknown)
   if ped.sex == '1':
	strx += 'M'
   elif ped.sex == '2':
	strx += 'F'
   else:
	strx += 'N'

   return strx

columnInfo=namedtuple( 'VrtInfo', 'pid,loc,chrom,pos,ref,alt'.split(',') )

def checkHeader( colI, hdr ):
   hdrS = set(hdr)

   for cn in 'familyId,location,variant,bestState,inChild'.split(','):
     if cn in hdrS:
	raise Exception('The column name "%s" SHOULD be RENAMED since conflicting with an OUTPUT column name'% cn )

   for cn in [colI.pid, colI.ref, colI.alt]:
       if cn not in hdrS:
             raise Exception('The column %s not found in the file header: ' %cn + "\n".join(hdr))

   if colI.loc == '':
       for cn in [colI.chrom, colI.pos]:
          if cn not in hdrS:
             raise Exception('The column %s not found in the file header: ' %cn + "\n".join(hdr))
   else:
      if colI.loc not in hdrS:
	raise Exception('The column %s not found in the file header: ' %colI.loc + "\n".join(hdr))

def getLoc( rx, colI ):
   if colI.loc == '':
	return rx[colI.chrom], rx[colI.pos]

   ch, pos = rx[colI.loc].split(':')
   return ch, pos

defaultCol = columnInfo( *['pid','','chrom','pos','ref','alt'] )
#pos of all vrt are the same 
#below: vrt is based on chrom pos ref alt
def printDenovo( vrt, famInfo, pInfo, header=[], cI=defaultCol, out=sys.stdout ): #cI :column info - see above
   fVrt = defaultdict( list )
   #variant happend to more than one child
   #make it variant based on family
   for rx in vrt:
	flag = False
	pid = rx[cI.pid] #'SP_id']
	for k1, v1 in famInfo.items():
	   if pid not in v1['ids']: continue
	   if v1['ids'].index(pid) < 2: continue

	   fVrt[k1].append( rx )
	   flag = True
	   break 

	if not flag:
		print('\t'.join( [pid, 'asChildNotFound'] ), rx, file=sys.stderr)
		#exit(1)
   #
   #handle based on family
   for k, v in fVrt.items():
	terms = v[0]

	chrom, pos = getLoc( rx, cI )

        fid, nfid = k, famInfo[k]['newFid'] #, rx[cI.chrom] #'CHROM']
	px, vx = vrtF.vcf2cshlFormat2( int(pos), rx[cI.ref], [rx[cI.alt]] )
        #px, vx = callVariant( int(rx[cI.pos]), rx[cI.ref], [rx[cI.alt]] ) #int(rx['POS']), rx['REF'], [rx['ALT']] )

	cS = []
	mId = []
	fIx = famInfo[fid]['ids']
	fs = len(fIx)

	if chrom == 'X' and (not vrtF.isPseudoAutosomalX(px[0])):
		tx = [pInfo[xx].sex for xx in fIx] #M:'1' F:'2'
		tx = [xx if xx in ['1','2'] else '2' for xx in tx]
		# correct if sex is not given and assume it as a girl
		bSts = [tx, ['0' for n in xrange(fs)]]
	else:	
		bSts = [['2' for n in xrange(fs)], ['0' for n in xrange(fs)]]

	#cnts = [['0' for n in xrange(fs)], ['0' for n in xrange(fs)]]
        for rx in v:
		#print rx
		pid = rx[cI.pid] # 'SP_id']
        	ped = pInfo[pid]
		cS.append( childState(ped) )
		#print famInfo[fid]
		ix = famInfo[fid]['ids'].index( pid )
		mId.append( famInfo[fid]['newIds'][ix] )

		if bSts[0][ix] == '1':
			bSts[0][ix] = '0'; bSts[1][ix] = '1'
		else:
			bSts[0][ix] = '1'; bSts[1][ix] = '1'	

		#cnts[0][ix] = rx['ref_DP']
		#cnts[1][ix] = rx['alt_DP']

	terms[cI.pid] = ','.join(mId)
	#terms['SP_id'] = ','.join(mId)

	#cnts[0][0] = rx['DP_mother']
	#cnts[0][1] = rx['DP_father']

	#cnts = ' '.join( cnts[0] ) +'/'+ ' '.join( cnts[1] )
	bSts = ' '.join( bSts[0] ) +'/'+ ' '.join( bSts[1] )

        #print ped
	#print terms['SP_id'] #'\t'.join( [nfid, '{}:{}'.format(chrom,str(px[0])), vx[0], bSts, ','.join( cS )] )     
	if vx[0].startswith( 'complex' ):
		print('\t'.join( [nfid, '{}:{}'.format(chrom,str(px[0])), vx[0], bSts, ','.join( cS )] + [terms[h] for h in header] ), file=sys.stdout)
		continue

        print('\t'.join( [nfid, '{}:{}'.format(chrom,str(px[0])), vx[0], \
			  #cnts, \
		          bSts, ','.join( cS )] + [terms[h] for h in header] ), file=out)     

def main():
   #svip.ped
   #svip-FB-vars.vcf.gz, svip-PL-vars.vcf.gz, svip-JHC-vars.vcf.gz
   #pfile, dfile = 'data/svip.ped', 'data/svip-FB-vars.vcf.gz'
   usage = "usage: %prog [options]"
   parser = optparse.OptionParser(usage=usage)
   parser.add_option("-p", "--pedFile", dest="pedFile", default="xxx.txt",
	metavar="pedFile", help="Pedgree file with certain format")
   parser.add_option("-d", "--dataFile", dest="dataFile", default="data/SF_denovo_all_lofdmis_excl4.csv",
        metavar="dataFile", help="VCF format variant file")

   parser.add_option("-x", "--project", dest="project", default="VIP", metavar="project", help="project name [defualt:VIP]")
   parser.add_option("-l", "--lab", dest="lab", default="SF", metavar="lab", help="lab name [defualt:SF]")

   parser.add_option("-o", "--outputPrefix", dest="outputPrefix", default="transmission",
        metavar="outputPrefix", help="prefix of output transmission file")
   parser.add_option("-m", "--delimiter", dest="delimiter", default="\t", metavar="delimiter", help="lab name [defualt:tab]")
   #parser.add_option("-o", "--out", dest="outFile", default="output/SF_denovo_all_lofdmis_excl4.txt",
   #     metavar="outFile", help="de novo format variant file")
   #parser.add_option("-f", "--famOut", dest="famOut", default="output/famData.txt",
   #     metavar="famOut", help="famData file")
   parser.add_option("-c", "--columNames", dest="columnNames", default="pId,chrom,pos,ref,alt",
	metavar="columnNames", help="column names for pId,chrom,pos,ref,alt [defualt:pId,chrom,pos,ref,alt]")

   ox, args = parser.parse_args()
   pfile, dfile = ox.pedFile, ox.dataFile

   OUT = ox.outputPrefix +'.txt'
   out = open( OUT, 'w' )
   #out = sys.stdout
   #fInfo: each fam has mom, dad and child personal ID
   #pInfo:   each person has raw info from "PED" file
   #fInfo, pInfo = procPED( pfile )
   fInfo, pInfo = procFamInfo( pfile )
   FAMOUT = ox.outputPrefix +'-families.txt'
   printFamData( fInfo, pInfo, proj=ox.project, lab=ox.lab, out=open(FAMOUT,'w') )

   denovo = defaultdict( list )
   hdr = []
   colI = columnInfo( *(ox.columnNames.split(',')) )

   with open( ox.dataFile ) as ifile:
      line = ifile.readline().strip('\n')
      hdr = line.translate(None,'[*]').split(ox.delimiter)

      #check header
      checkHeader( colI, hdr )
 
      for line in ifile:
        terms = procLine( line, delimiter=ox.delimiter )
        rx = {k:v for k, v in izip(hdr,terms)}
	rx['terms'] = terms
	#
	#idx = ','.join( ['%4s' %(rx['CHROM']), '%12s' %(rx['POS']), rx['REF'], rx['ALT']] )
        chrom, pos = getLoc( rx, colI )
	idx = ','.join( ['%4s' %(chrom), '%12s' %(pos), rx[colI.ref], rx[colI.alt]] )
	denovo[idx].append( rx )

   print('\t'.join( 'familyId,location,variant,bestState,inChild'.split(',') \
			+ hdr ), file=out)
   #colI = columnInfo( *(ox.columnNames.split(',')) )
   for k in sorted(denovo.keys()):
	v = denovo[k]
	printDenovo( v, fInfo, pInfo, header=hdr, cI=colI, out=out )

   #print hdr
   #print len(denovo)

if __name__ == "__main__":
   main()

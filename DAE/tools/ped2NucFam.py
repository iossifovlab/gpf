#!/usr/bin/env python

import optparse, sys, os
import pysam, numpy
from collections import namedtuple, defaultdict
from itertools import izip
import itertools

pedInfo = namedtuple( 'PED', 'fid,pid,fa,ma,sex,phenotype,aux'.split(',') )
pidInfo = namedtuple( 'PID', 'fid,fa,ma,sex,phenotype,aux'.split(',') )

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

#split family to nuclear
def procPED2Nuc( fname ):
  fInfo = defaultdict(list)
  pInfo = dict()

  clist, plist = set(), set()

  with open( fname ) as fin:
    line = fin.readline()
    hd = line.strip('\n').split('\t')
    aux = hd[6:]

    for line in fin:
	terms = line.strip('\n').split('\t')
	tx = { h:v for h,v in izip(hd,terms) }

	ped = pedInfo( *[tx['familyId'],tx['personId'],tx['dadId'],tx['momId'],tx['gender'],tx['status'], terms[6:] ] )  #*terms )
	pid = pidInfo( *[tx['familyId'],tx['dadId'],tx['momId'],tx['gender'],tx['status'], terms[6:] ] )  #*([terms[0]] + terms[2:]) )
	#print ped, pid
	pInfo[ped.pid] = pid

	if ped.fa == '0' and ped.ma == '0': continue

	fid = ped.ma +'-'+ ped.fa
	if fid not in fInfo:
                fInfo[fid] += [ped.ma, ped.fa]

	fInfo[fid].append( ped.pid )

	clist.add( ped.pid )
	plist |= set( [ped.ma, ped.fa] )

  mlist = { x:0 for x in clist & plist }
  #print mlist
  mInfo = dict() #
  for k, v in fInfo.items():
        newIds = []
        for pid in v:
           if pid in mlist:
                newIds.append( "%s.m%d" % ( pid, mlist[pid] ) )
                mlist[pid] += 1
           else:
                newIds.append( pid )

        newFid = newIds[0] +'-'+ newIds[1]

        mInfo[k] = { 'fid': k, 'newFid': newFid, 'ids': v, 'newIds': newIds }
  #for k, v in mInfo.items(): print k, v
  #print fInfo, pInfo, mInfo
  return mInfo, pInfo, aux

def pedState( ped ):
   role = ''
   if ped.phenotype == '1':
        role = 'sib'
   elif ped.phenotype == '2':
        role = 'prb'
   else:
        role = 'na'
   #Sex (1=male; 2=female; other=unknown)
   sex = ''
   if ped.sex == '1':
        sex = '1'
   elif ped.sex == '2':
        sex = '2'
   else:
        sex = '0'

   #if ped.ma == '0' and ped.fa == '0':
   #     if sex == 'M': role = 'dad'
   #     if sex == 'F': role = 'mom'

   return sex, role

# familyId,personId,momId,dadId,gender,status,[sampleId]
def printNucFamInfo( fInfo, pInfo, aux_head=[], out=sys.stdout ):
   flag = False
   for k, v in fInfo.items():
        if len([n for n,o in izip(v['ids'],v['newIds']) if n != o]) > 0:
                flag = True
                break

   if flag:
        print >> out, '\t'.join( 'familyId,personId,dadId,momId,gender,status,sampleId'.split(',') + aux_head )
   else:
        print >> out, '\t'.join( 'familyId,personId,dadId,momId,gender,status'.split(',') + aux_head )

   for k, v in sorted(fInfo.items()):
        nf = v['newFid']        #new family id
        nm = v['newIds']        #new id
        om = v['ids']           #original id

	xp = pInfo[om[0]]
	sex, role = pedState( xp )
	if flag:
                s = ''
                if nm[0] != om[0]: s = om[0]

                #print >> out, '\t'.join( [nf, nm[0], xp.fa, xp.ma, sex, xp.phenotype, s] )
                print >> out, '\t'.join( [nf, nm[0], '0', '0', sex, xp.phenotype, s] + xp.aux )
	else:
                #print >> out, '\t'.join( [nf, nm[0], xp.fa, xp.ma, sex, xp.phenotype] )
                print >> out, '\t'.join( [nf, nm[0], '0', '0', sex, xp.phenotype] + xp.aux )

	xp = pInfo[om[1]]
	sex, role = pedState( xp )
	if flag:
                s = ''
                if nm[1] != om[1]: s = om[1]

                #print >> out, '\t'.join( [nf, nm[1], xp.fa, xp.ma, sex, xp.phenotype, s] )
                print >> out, '\t'.join( [nf, nm[1], '0', '0', sex, xp.phenotype, s] + xp.aux )
	else:
                #print >> out, '\t'.join( [nf, nm[1], xp.fa, xp.ma, sex, xp.phenotype] )
                print >> out, '\t'.join( [nf, nm[1], '0', '0', sex, xp.phenotype] + xp.aux )

	for o, n in izip(om[2:],nm[2:]):
	   xp = pInfo[o]
	   sex, role = pedState( xp )
	   
	   s = ''
	   if o != n: s = o

	   if flag:
	        #print >> out, '\t'.join( [nf, n, xp.fa, xp.ma, sex, xp.phenotype, s] )
                print >> out, '\t'.join( [nf, n, nm[1], nm[0], sex, xp.phenotype, s] + xp.aux )
	   else:
                #print >> out, '\t'.join( [nf, n, xp.fa, xp.ma, sex, xp.phenotype] )
                print >> out, '\t'.join( [nf, n, nm[1], nm[0], sex, xp.phenotype] + xp.aux )

# familyId,personId,momId,dadId,gender,status,[sampleId]
def checkHeader( hd ):
  for tx in 'familyId,personId,momId,dadId,gender'.split(','):
	if tx not in hd:
                print >> sys.stderr, tx, 'not found on header'
                exit(1)

def famInfo2PID( ped ):
  return pidInfo(*[ped.fid, ped.fa, ped.ma, ped.sex, ped.phenotype, ped.aux])

def famInfo2PED( info ):
  #keep all the info as it is, except pid - sampleId is real id if not empty
  fid, pid, ma, fa, sx, pheno = info['familyId'],info['personId'],info['momId'],info['dadId'],info['gender'],info['status']

  nPid = pid
  if ('sampleId' in info) and info['sampleId'] != '' :  pid = info['sampleId']
   
  sex = '0'
  if sx == '1' or sx == 'M':
	sex = '1'
  elif sx == '2' or sx == 'F':
	sex = '2'
  #print nPid, pedInfo(*[fid, pid, fa, ma, sex, pheno])
  return nPid, pedInfo(*[fid, pid, fa, ma, sex, pheno, ''])

# accept Ped as it is
def procFamInfo( fname ):
  fInfo = defaultdict(dict)
  pInfo = dict()

  p2np = defaultdict(list) #pid to new Pid
  np2p = dict()

  with open( fname ) as fin:
      line = fin.readline()
      hd = line.strip('\n').split('\t')
      #check header whether it is satisfying required columns
      checkHeader( hd )
	
      for line in fin:
	fx = {h:v for h,v in izip(hd,line.strip('\n').split('\t'))}

	nPid, ped = famInfo2PED( fx ) #
	pid = famInfo2PID( ped ) #pidInfo( *([terms[0]] + terms[2:]) )
	#print ped, pid
	if nPid != ped.pid: pInfo[ped.pid] = pid
        pInfo[nPid] = pid

	p2np[ped.pid].append(nPid)
	np2p[nPid] = ped.pid
	#print ped.pid, nPid
	#if ped.fa == '0' and ped.ma == '0': continue
	#if ped.fid.find( nPid ) >= 0: continue

	fid = ped.fid
	if fid not in fInfo:
                fInfo[fid]['ids']    = []#[ped.ma, ped.fa]
                fInfo[fid]['newIds'] = []#[ped.ma, ped.fa]
                fInfo[fid]['fid']    = fid
                fInfo[fid]['newFid'] = fid

	fInfo[fid]['ids'].append( ped.pid )
	fInfo[fid]['newIds'].append( nPid )

  for k, v in fInfo.items():
	for n, p in enumerate(v['ids']):
                if p in p2np: continue
                
                fInfo[k]['ids'][n] = np2p[p]
	# To remember member of fInfo
	#mInfo[k] = { 'fid': k, 'newFid': newFid, 'ids': v, 'newIds': newIds }
  #print p2np, np2p
  #make dict for who are mother and father in the family even on large families
  fama = namedtuple( 'fama', ['fa','ma'] )
  for fid in fInfo.keys():
     fm = {}
     im = {}
     ids = fInfo[fid]['newIds'] #['ids']
     for n,ms in enumerate(ids):
        p = pInfo[ms]
        fa, ma = p.fa, p.ma
        #print ids, p, fa, ma
        if fa != '0' or ma != '0':
            #print 'inside', fa, ma
            #fa, ma = np2p[fa], np2p[ma]
            fm[ms] = fama( *[fa,ma] )
            im[n]  = fama( *[ids.index(fa),ids.index(ma)] )

     fInfo[fid]['famaName']  = fm
     fInfo[fid]['famaIndex'] = im
  #print fInfo; exit(0)
  return fInfo, pInfo

def pedState2( ped ):
   role = ''
   if ped.phenotype == '1':
        role = 'sib'
   elif ped.phenotype == '2':
        role = 'prb'
   else:
        role = 'na'
   #Sex (1=male; 2=female; other=unknown)
   sex = ''
   if ped.sex == '1':
        sex = 'M'
   elif ped.sex == '2':
        sex = 'F'
   else:
        sex = 'N'

   #if ped.ma == '0' and ped.fa == '0':
   #     if sex == 'M': role = 'dad'
   #     if sex == 'F': role = 'mom'

   return sex, role

def printFamData( fInfo, pInfo, proj='VIP', lab='SF', listFam=[], out=sys.stdout ):
   flag = False
   for k, v in fInfo.items():
	if len([n for n,o in izip(v['ids'],v['newIds']) if n != o]) > 0:
		flag = True
		break
   if flag:
	print >> out, '\t'.join( 'familyId,personId,Project,Lab,role,gender,sampleId'.split(',') )
   else:
	print >> out, '\t'.join( 'familyId,personId,Project,Lab,role,gender'.split(',') )

   for k, v in sorted(fInfo.items()):
	if (len(listFam) > 0) and (k not in listFam): continue

	nf = v['newFid']
	nm = v['newIds']
	om = v['ids']

	xp = pInfo[nm[0]]
	sex, role = pedState2( xp )
	if flag:
               s = ''
               if nm[0] != om[0]: s = om[0]
               print >> out, '\t'.join( [nf, nm[0], proj, lab, 'mom', sex, s] )
	else:
               print >> out, '\t'.join( [nf, nm[0], proj, lab, 'mom', sex] )

	xp = pInfo[nm[1]]
	sex, role = pedState2( xp )
	if flag:
                s = ''
                if nm[1] != om[1]: s = om[1]

                print >> out, '\t'.join( [nf, nm[1], proj, lab, 'dad', sex, s] )
	else:
                print >> out, '\t'.join( [nf, nm[1], proj, lab, 'dad', sex] )

	for o, n in izip(om[2:],nm[2:]):
	   xp = pInfo[n]
	   sex, role = pedState2( xp )
	   
	   s = ''
	   if o != n: s = o

	   sex, role = pedState2( pInfo[n] )
	   if flag:
	        print >> out, '\t'.join( [nf, n, proj, lab, role, sex, s] ) 
	   else:
                print >> out, '\t'.join( [nf, n, proj, lab, role, sex] )

if __name__ == "__main__":
   usage = "usage: %prog [options] <INPUT:ped file> <OUTPUT:nuclear ped file>"
   parser = optparse.OptionParser(usage=usage)
   #parser.add_option("-p", "--pedFile", dest="pedFile", default="data/svip.ped",
   #    metavar="pedFile", help="PED format file")
   #parser.add_option("-o", "--famOut", dest="famOut", default="output/famData.txt",
   #     metavar="famOut", help="famData file")

   ox, args = parser.parse_args()
   #fInfo,pInfo = procPED2Nuc( ox.pedFile )
   fInfo,pInfo,hdaux = procPED2Nuc( args[0] ) #ox.pedFile ) #hdaux: auxiliary info

   #fout = open( ox.famOut, 'w' )
   fout = open( args[1], 'w' ) #ox.famOut, 'w' )
   printNucFamInfo( fInfo, pInfo, aux_head=hdaux, out=fout )
   fout.close()

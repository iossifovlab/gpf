#!/data/software/local/bin/python

import gzip, pysam, sys, optparse, os
import numpy as np
# from DAE import *

class family:
	def __init__(self, fname):
	   try:
		self.familyID = ''
		self.member = []
		self.order  = dict()
		self.role   = dict()
		self.gender = dict()
		with open( fname, 'r' ) as infile:
			for line in infile.xreadlines():
				line = line.rstrip()
				x = line.split('=')
				#print x[0]
				if x[0] == 'sampleIds':
					x = x[1].rstrip().split(',')
					self.member = x
					self.order = dict( (x[n],n) for n in range(len(x)) )
				else:
				   y = x[0].split('.')
				   #print y[0]
				   if y[0] == 'sample':
					if y[2] == 'role':
						self.role[y[1]] = x[1]
					elif y[2] == 'gender':
						self.gender[y[1]] = x[1]
				   elif y[0] == 'quad':
					#print 'quad-line\t', line, x[0], x[1]
					self.familyID = x[1]
	   except IOError, e:
		print e
		exit(0)
	def Print( self ):
		print self.familyID
		print self.member
		print self.order
		print self.role
		print self.gender
	def Sample( self, idx ):
		if  (sample < self.member) & (sample >= 0):
			return self.member
		else:
			return ''
	def Id( self, sample ):
		if sample in self.order:
			return self.order(sample)
		else:
			return -1

	def Gender( self, sample ):
	   try:
		float(sample)
		if (sample < len(self.member)) and (sample >= 0):
			return self.gender[ self.member[sample] ]
		else:
			return ''
	   except:
		if sample in self.gender:
			return self.gender[ sample ]
		else:
			return ''
	def isMale( self, sample ):
		gd = self.Gender( sample );
		flag = (gd == 'M')
		return flag

	def areMale( self ):
		gd = [self.Gender(g) == 'M' for g in self.member]
		return gd

	def Role( self, sample ):
	   try:
		int(sample)
		if (sample < len(self.member)) and (sample >= 0):
			return self.role[ self.member[sample] ]
		else:
			return ''
	   except:
		if sample in self.gender:
			return self.role[ sample ]
		else:
			return ''
	def familyID( self ):
		return self.familyID
class alpha:
	def __init__(self, fname):
	   try:
		with open( fname, 'r' ) as infile:
			line = infile.readline()
			self.value = [float(n) for n in line.split()[1::2]]
			#self.CNVState = CNVState( self.value )
	   except IOError, e:
		print e
		exit(0)
	def getValue( self ):
		return self.value
	def Print( self ):
		print self.value

class ommission:
   def __init__( self, alph, male ):
	self.alpha = alph
	self.male  = male 

   def processI( self, xstr ):
	xstr = xstr.strip()
	cs = xstr.split();

	ch  = cs[0]
	pos = int(cs[1])

	cnt = np.array([[int(n) for n in x.split(',')] for x in cs[2:]])
	#print ch, pos, cnt
	return ch, pos, cnt
   # alpha should be used but not implimented yet
   def Genotype( self, allCnts, ch ):
	flag = False;
	gens = [];

	sACnts = np.sort(allCnts.sum(0))
	if sACnts[-2] == 0:
		return flag, gens

	sPAllCnts = np.sort(allCnts.sum(1))
	if ch == 'X':
		sPAllCnts = sPAllCnts[np.array(self.male)]
		#print sPAllCnts
	if sPAllCnts.min()<20:
		return flag, gens

	allOrd  = np.argsort(allCnts.sum(0))
	mjAll = allOrd[-1]
	mnAll = allOrd[-2]

	cnts = allCnts[:,[mjAll,mnAll]] 
	sPCnts = cnts.sum(1)

	zid = (sPCnts[np.array(self.male)] < 3)
	mnRtio = cnts[:,1].astype(float)
	if sum( zid ) > 0:
		mnRtio = cnts[:,1].astype(float)
		for n in range(len(mnRtio)):
		   if (sPCnts[n] < 3) and self.male[n]:
			mnRtio[n] = 1 
		   else:
			mnRtio[n] /= sPCnts[n]
		#print allCnts
		#print sPCnts, mnRtio
	else:
		mnRtio /= sPCnts

	gens = -1 * np.ones(4,dtype='int')
	gens[mnRtio<0.02] = 2
	gens[mnRtio>0.98] = 0
	gens[np.logical_and(mnRtio>0.2,mnRtio < 0.8)] = 1

	#if sum(zid) > 0:
	#	print gens

	if gens.min()==-1:
		return flag, gens

	flag = True
	#print flag, gens
	return flag, gens

   def processAuto( self, gens ):
	flag = False
	xstr = ''

	issues = []
	for c in xrange(2,4):
	    if gens[c]==1:
        	continue
	    for p in xrange(2):
	        if gens[p]!=1 and gens[p]!=gens[c]: # report which is lost
	            issues.append(str(p)+str(c))
	if not issues:
	    return flag, xstr

	flag = True
	xstr = "".join([str(g) for g in gens]) + "\t"+ ",".join(issues)

	return flag, xstr

   def pseudoAutoX( self, pos ):
	#hg19 pseudo autosomes region: chrX:60001-2699520 and chrX:154931044-155260560 are hg19's pseudo autosomal
	if (pos < 60001) or ((pos >= 2699520) and (pos < 154931044)) or (pos >= 155260560):
		return False

	return True

   def processX( self, gens ):
	flag = False
	xstr = ''
	#print 'before', gens, self.male
	if( sum( gens[ np.array(self.male) ] == 1 ) > 0 ): #already filtered pseudo autosomal region
		#flag, xstr = self.processAuto( gens )
		return flag, xstr

	gens[ np.array(self.male) & (gens>1)] = 1
	#print 'processX',gens
	issues = []
	for c in xrange(2,4):
	   if self.male[c]:
		if (gens[0] != 1 ) and (gens[0]/2 != gens[c]):
			issues.append(str(0)+str(c))
	   else:
		if gens[c] == 1:
			if ((gens[0] == 0) and (gens[1] == 0)) or ((gens[0] == 2) and (gens[1] == 1 )):
				issues.append(str(0)+str(c))
				issues.append(str(1)+str(c))
			continue

	       	if ((gens[1] > 0) and (gens[c] == 0)) or ((gens[1]==0) and (gens[c] == 2)):
			issues.append(str(1)+str(c)) #loss father
		if (gens[0] == 2 and gens[1] == 0 and gens[c] == 0) or (gens[1]>0 and gens[0] == 0 and gens[c] == 2):
			issues.append(str(0)+str(c)) #loss mother
           
	if not issues:
	    return flag, xstr

	flag = True
	xstr = "".join([str(g) for g in gens]) + "\t"+ ",".join(issues)

	return flag, xstr

   def Main( self, xstr ):
	flag = False
	rstr = ''

	ch, pos, allCnts = self.processI( xstr )
	xflag, gens = self.Genotype( allCnts, ch )

	if not xflag:
		return flag, rstr

	try:
		int(ch)
		#print ch, gens, allCnts
		flag, rstr = self.processAuto( gens )
	except:
		#print ch, gens, "\n", allCnts
		if (ch == 'X'):
		   if self.pseudoAutoX(pos):
			flag, rstr = self.processAuto( gens )
		   else:
			flag, rstr = self.processX( gens )

	return flag, rstr

usage = "usage: %prog [options]"
parser = optparse.OptionParser(usage=usage)

parser.add_option("-i", "--input", dest="inputFile", default="",
                  metavar="INPUT", help="input \"baseCntStat.bgz\"")
parser.add_option("-o", "--output", dest="outputFile", default="",
                  metavar="OUTPUT", help="write output to FILE")
parser.add_option("-f", "--family", dest="familyInfo", default='.',
                  metavar="familyInfo", help="family Info")
parser.add_option("-r", action="store_true", dest="reprocess", default=False,
                  metavar="reprocess", help="rewrite or reprocess, default [False]")


ox, args = parser.parse_args()

# f = gzip.open("/data/unsafe/autism/pilot2/quad/auSSC12950-wholeblood/baseCntStat.bgz")
f = gzip.open( ox.inputFile )

if os.path.exists(ox.outputFile) and (not ox.reprocess) :
	print ox.outputFile, '\t exists!\nto overwrite, put "-r" option'
	exit(1)

outfile = open( ox.outputFile, 'w' )

fam = family( ox.familyInfo + '/params.txt' )
alph = alpha(  ox.familyInfo + '/alpha.txt' )

#fam.Print()
#aph.Print()
#print 'SSC02357\t'+fam.Gender('SSC02357')+'\t'+fam.Role('SSC02357')
#print 'SSC02357\t'+fam.Gender(3)+'\t'+fam.Role(3)

# tbf = pysam.Tabixfile("/data/safe/autism/pilot2_STATELAB/objLinks/quad/auSSC12451-wholeblood/baseCntStat.bgz")

# 12451 16:29665166-30203695
# chr16: 29669778-30590277

alp = alph.getValue()
male = fam.areMale()

process = ommission( alp, male )

#print alp, gnd

ln = 0
try:
 with gzip.open( ox.inputFile ) as f:
   for line in f:
# for l in tbf.fetch("16", 29669778, 30590277):
	line = line.strip()
	flag, xstr = process.Main( line )

	ln+=1
	if ln%100000==0:
		print >>sys.stderr, ln

	'''
	allCnts  = np.array([[100, 1, 0, 0],
	                     [1, 50, 0, 0],
	                     [50, 1, 0, 0],
	                     [50, 50, 0, 0]])
	'''
	if( not flag ):
	    continue
	#print '%s\t%s'%( line, xstr )
	outfile.write( line+"\t" + xstr +"\n" )
except IOError, e:
	print e
	exit(1)


outfile.close()

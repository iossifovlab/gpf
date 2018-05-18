#!/usr/bin/env python

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from builtins import zip
from builtins import map
from builtins import range
from past.utils import old_div
import optparse, os, sys, math, gzip

#from pylab import *
from numpy import *
from scipy.stats import *
from numpy.random import *

from vrtIOutil import *

#family based data and mom and dad ordered state
#pp is even and num of people (count 2, mom and dad, per family)
#Alt count
#0 1, and 2 copy state of an alternattive allele
#not handling Y chromosome
def xMF( xstr, pp ):
	terms = xstr.split(';')	#only families which have alternatives
	cnt = [[0,0,0],[0,0,0]]

	diplo_flag = [True,True]

	#print xstr 
	for x in terms:
		#print x
		terms = x.split(':')
		fmid,bestStS,cntsS = terms[0], terms[1], terms[2]
		#print bestStS
		z = [list(map(int,rs)) for rs in bestStS.split('/')]
	        #print bestStS, z	
		cnt[0][z[1][0]] += 1	#mom
		cnt[1][z[1][1]] += 1	#dad

		if( z[0][0] + z[1][0] < 2 ) : diplo_flag[0] = False
		if( z[0][1] + z[1][1] < 2 ) : diplo_flag[1] = False

	cnt[0][0] = old_div(pp,2) - cnt[0][1] - cnt[0][2]
	cnt[1][0] = old_div(pp,2) - cnt[1][1] - cnt[1][2]

	return cnt, diplo_flag

# ob : observed 2
# p : frequency
# s : population size and EVEN number (num of male and female are the same)
# smpl_size : sample size
def randomSampling( cnt, genF, smpl_size=10000, flagX=False ):
	s = sum(cnt)
	eCnt = s*array(genF)

	T = sum( [1.*(c-e)*(c-e)/e for c,e in zip(cnt,eCnt)] )

	if flagX:
		p = old_div((1.0*cnt[1] + 2.*cnt[2]),(1.5*s))
		q = 1. - p

		v = multinomial( old_div(s,2), [q*q, 2*p*q, p*p], size=smpl_size )
		w = multinomial( old_div(s,2), [q, p, 0], size=smpl_size )

		x = v + w
	else:
		x = multinomial( s, genF, size=smpl_size )

	w = (x - eCnt)*(x - eCnt) / (1.*eCnt)
	n = sum( sum(w,1) > T )
	
	pv = old_div((1.*n),smpl_size)
	#print ','.join( [str(x) for x in cnt] ), ','.join( ['{0:.2f}'.format( x ) for x in eCnt] ), pv
	return pv

def G_test( cnt, eCnt ):
	df = len(cnt) - 2

	T = sum([ 2.*c*log(old_div(c,e)) for c,e in zip(cnt,eCnt) if c != 0])
	pv = 1. - chi2.cdf( sum(T), df )

	return pv

def Chi2_test( cnt, eCnt ):
	df = len(cnt) - 2	

	T = sum([ (c-e)*(c-e)/e for c,e in zip(cnt,eCnt) if e != 0])
	pv = 1. - chi2.cdf( sum(T), df )

	return pv

def Chi2_options( cnt, eCnt, genF, X=False ):
	if sum(array(eCnt)<5) < 1 :
		return Chi2_test( cnt, eCnt )

	if (cnt[0] == 0 and eCnt[0] < 1) or (cnt[2] == 0 and eCnt[2] < 1 ):
		return 1.

	return randomSampling( cnt, genF, flagX=X )

# global variable
# defalult is False 
# add -c to make it True
chi2_test_flag = True

def Test( cnt, eCnt, genF, X=False ):
	global chi2_test_flag
	
	if chi2_test_flag:
		pv = Chi2_options( cnt, eCnt, genF, X )
	else:
		pv = G_test( cnt, eCnt )

	return pv

def pval_count_autosome( cnt ):
	# cnt: [RR, RA, AA]
	N = sum(cnt)
	p = old_div((1.0*cnt[1] + 2.*cnt[2]),(2.*N))

	genF = [(1-p)*(1-p), 2.*(1-p)*p, p*p]
	eCnt = [ N*x for x in genF]

	pv = Test( cnt, eCnt, genF ) 

	return pv, eCnt

def pval_count_X( cnt ):
	# cnt: [RR, RA, AA]
	# or   [R, A, '']
	N = sum(cnt)
	p = old_div((1.0*cnt[1] + 2.*cnt[2]),(1.5*N))

	genF = [(1-p)*(1-p)/2.+old_div((1-p),2.), (1-p)*p + old_div(p,2.), p*p/2.]
	eCnt = [ N*x for x in genF]

	pv = Test( cnt, eCnt, genF, True )

	return pv, eCnt

def Rx( xstr, pp, AXY, pos ):
	xcnt, di_flag = xMF( xstr, pp )
	cnt = [ xcnt[0][n] + xcnt[1][n] for n in range(len(xcnt[0]))]

	if (AXY == 'X') and (not isPseudoAutosomalX( pos )):
		pv, eCnt = pval_count_X( cnt )
	else:
		pv, eCnt = pval_count_autosome( cnt )

	return pv, cnt, eCnt

def main():
	usage="usage: %prog options]"
	parser = optparse.OptionParser( usage=usage )

	#parser.add_option("-r", "--refFile", dest="refFile", default='',
        #          metavar="refFile", help="ref File" )
	#parser.add_option("-x", "--tooMany", dest="tooMany", default='',
        #          metavar="tooMany", help="TOOMANY file")
	#parser.add_option("-o", "--outFile", dest="outFile", default='',
        #          metavar="outFile", help="output file")
	parser.add_option("-c", "--chisq", action="store_true", dest="chisq", default=False,
                  metavar="chisq", help="chisq test, default [G-test]")

	ox, args = parser.parse_args()

	ref = ReaderStat( args[0] )
	mny = ReaderStat( tooManyFile(args[0]) )	

	ref.notExistExit()
	#if not ox.refFile:
	#	print 'require a ref file'
	#	exit(1)

	global chi2_test_flag
	if not ox.chisq:
		chi2_test_flag = False
		#print chi2_test_flag
	
	#ref = ReaderStat( ox.refFile )
	#mny = ReaderStat( ox.tooMany )	

	gzW = Writer( args[1] ) #gzip.open( args[1], 'wb' )
	#gzW = gzip.open( ox.outFile, 'wb' )
	gzW.write( ref.head +'\tHW\n' )

	flag = True;
	while flag :
		fi =  ref.getFamilyData()
		if 'TOOMANY' == fi :
		   if ref.cID == mny.cID:
			fi = mny.getFamilyData()
			#print 'right', ref.cID, mny.cID
			mny.readLine()
		   else:
			print('wrong', ref.cID, mny.cID)
			exit(1)

		cnt, pcnt = ref.getStat()

		terms = ref.cID.split(':')
		pv, cnt, eCnt = Rx( fi, cnt[0], terms[0], int(terms[1])  )

		gzW.write( ref.cLine +'\t{0:.4f}'.format( pv ) +'\n' )

		#if pv == 0: pv = 1000
		#else: pv = abs(-10.*log10(pv))

		#print ref.cLine +'\t{0:.2f}'.format( pv ) +'\t'+ ','.join( [str(c) for c in cnt] ) \
		#	+'\t'+ ','.join( ['{0:.1f}'.format( c ) for c in eCnt] ) 

		flag = ref.readLine()

	#gzW.close()

if __name__ == '__main__':
	main()

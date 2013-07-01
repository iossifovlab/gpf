import os
import sys
import itertools
from DAE import *
from GetVariantsInterface import *

#for x in vDB.getDenovoStudies():
#    print x
#
#for x in vDB.getStudyGroups():
#    print x
#    
#sys.exit()
 
#print "DAE_SOURCE_DIR",os.environ["DAE_SOURCE_DIR"]
#print "DAE_DB_DIR",os.environ["DAE_DB_DIR"]
#print "PHENO_DB_DIR",os.environ["PHENO_DB_DIR"]
#print "PHENO_DB_PREFIX",os.environ["PHENO_DB_PREFIX"]
#print "PYTHONPATH",os.environ["PYTHONPATH"]

args={}
#args['denovoStudies']='none'
#args['denovoStudies']='allweandtg'
args['transmittedStudy']='wig781'
args['inChild']='prb'
#args['transmittedType']='ultrarare'
args['transmittedType']='ultrarare'
args['geneSym']='CCDC18'
args['effectTypes']='missense'
#args['variantTypes']='All'
args['variantTypes']='sub'
args['familiesList']='13152'


f=open("out.csv","w")
getVariantsInterface(args,f)
f.close()

getVariantsInterface(args)

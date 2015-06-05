#!/bin/env python

import os
import sys 
import gzip
import checkSortCols

fDir = sys.argv[1] 
tDir = sys.argv[2]
freqAttF = sys.argv[3]

tmStudiesToAnnotate = set(['w1202s766e611'])
dnvStudiesToCopy = set(['LevyCNV2011','wig683'])

def isDenovoCalls(fn,zipped=False):
    cols = "location variant".split(' ')
    if zipped:
        f = gzip.open(fn)
    else:
        f = open(fn)

    hdr = f.readline().strip().split("\t")
    f.close()
   
    return all([cl in hdr for cl in cols])

ignoreBgz = False 
# ignoreBgz = True


print "SHELL=/bin/bash -o pipefail"
print ".DELETE_ON_ERROR:"
print
print "all:"
print

allFiles = []

for r, sf, fls in os.walk(fDir):
    # print >>sys.stderr, r, sf, fls
    rPref = r[:len(fDir)]    
    if rPref != fDir:
        x10
    rStuff = r[len(fDir):]
    tr = tDir + rStuff
    logtr = "log/" + tDir + rStuff
    # print >>sys.stderr, r, tr

    try:
        os.makedirs(tr)
    except:
        pass

    try:
        os.makedirs(logtr)
    except:
        pass

    for f in fls:
        ffn = os.path.join(r,f) 
        tfn = os.path.join(tr,f) 
        tfnLog = os.path.join(logtr,f) 

        print >>sys.stderr, r, tr, rStuff, f

        op = "copy"
        if ffn.endswith('.txt'):
            if rStuff not in dnvStudiesToCopy and isDenovoCalls(ffn):
                op = 'annotate dnv'
        elif ffn.endswith('.bgz'):
            if ignoreBgz:
                op = 'ignore'
            else:
                if rStuff in tmStudiesToAnnotate and "TOOMANY" not in f:
                    op = 'annotate trm'
                else:
                    op = 'copy bgz'
        elif ffn.endswith('.tbi'):
            op = 'ignore'
     
        print >>sys.stderr, "%15s: %s" % (op, ffn)

        if op=='ignore':
           continue
 
        allFiles.append(tfn)

        if op=="copy":
            cmd =  "cp $^ $@"
        elif op=="copy bgz":
            cmd = "cp $^ $@ && tabix -s 1 -b 2 -e 2 $@ 2> %s-tabix.txt" % (tfnLog)
        elif op=="annotate trm":
            cmd = "annotateFreqTransm.py $^ iterative %s | bgzip -c > $@ && tabix -s 1 -b 2 -e 2 $@" % (freqAttF)
        elif op=="annotate dnv":
            cmd = "annotateFreqTransm.py $^ direct %s > $@" % (freqAttF)
        else:
            x10

        print '%s: %s\n\t(time %s) 2> %s-time.txt\n' % (tfn, ffn, cmd, tfnLog)

 
        # print "\t", f, op
         
print "all:", " ".join(allFiles)


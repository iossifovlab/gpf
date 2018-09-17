#!/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
import os
import sys 
import gzip
import checkSortCols

fDir = sys.argv[1] 
tDir = sys.argv[2]

ignoreBgz = False 
# ignoreBgz = True

def isSorted(fn,fmt,zipped=False):
    if zipped:
        f = gzip.open(fn)
    else:
        f = open(fn)

    r = checkSortCols.isSorted(f,fmt)
    f.close()
   
    return r 


print("SHELL=/bin/bash -o pipefail")
print(".DELETE_ON_ERROR:")
print()
print("all:")
print()

allFiles = []

for r, sf, fls in os.walk(fDir):
    # print r, sf, fls
    rPref = r[:len(fDir)]    
    if rPref != fDir:
        x10
    rSuff = r[len(fDir):]
    tr = tDir + rSuff
    logtr = "log/" + tDir + rSuff
    # print r, tr

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

        # print >>sys.stderr, ffn,

        op = "copy"
        isf = -1 
        if ffn.endswith('.txt'):
            isf = isSorted(ffn,"dnv")
            if isf == 1:
                op = 'sort dnv'
        elif ffn.endswith('.bgz'):
            if ignoreBgz:
                op = 'ignore'
            else:
                isf =  isSorted(ffn,"trm",zipped=True)
                if isf == 1:
                    op = 'sort trm'
                else:
                    op = 'copy bgz'
        elif ffn.endswith('.tbi'):
            op = 'ignore'
     
        print("%10s (%d): %s" % (op, isf, ffn), file=sys.stderr)

        if op=='ignore':
           continue
 
        allFiles.append(tfn)

        if op=="copy":
            cmd =  "cp $^ $@"
        elif op=="sort trm":
            # cmd = "annotate_variants.py $^ 2> %s-out.txt | re_annotate_variants.py > $@" % (tfnLog)
            cmd = "zcat $^ | addSortCols.py trm | sort -k1,1n -k2,2n -k3,3 | rmSortCols.py | bgzip -c > $@ && tabix -s 1 -b 2 -e 2 $@"  
        elif op=="sort dnv":
            # cmd = "zcat $^ | annotate_variants.py -c chr -p position - 2> %s-out.txt | bgzip -c > $@ && tabix -s 1 -b 2 -e 2 $@ 2> %s-tabix.txt" % (tfnLog, tfnLog)
            cmd = "cat $^ | addSortCols.py dnv | sort -k1,1n -k2,2n -k3,3 | rmSortCols.py > $@" 
        elif op=="copy bgz":
            cmd = "cp $^ $@ && tabix -s 1 -b 2 -e 2 $@ 2> %s-tabix.txt" % (tfnLog)

        print('%s: %s\n\t(time %s) 2> %s-time.txt\n' % (tfn, ffn, cmd, tfnLog))

 
        # print "\t", f, op
         
print("all:", " ".join(allFiles))


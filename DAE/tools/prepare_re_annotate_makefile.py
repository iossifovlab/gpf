#!/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
import os
import sys 
import gzip

fDir = sys.argv[1] 
tDir = sys.argv[2]

ignoreBgz = False 
# ignoreBgz = True

def isAnnotated(fn,zipped=False):
    cols = "effectType effectGene effectDetails".split(' ')
    if zipped:
        f = gzip.open(fn)
    else:
        f = open(fn)

    hdr = f.readline().strip().split("\t")
    f.close()
   
    return all([cl in hdr for cl in cols])


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
        op = "copy" 
        if ffn.endswith('.txt') and isAnnotated(ffn):
            op = 'reannotate text'
        elif ffn.endswith('.bgz'):
            if ignoreBgz:
                op = 'ignore'
            elif isAnnotated(ffn,zipped=True):
                op = 'reannotate bgz'
            else:
                op = 'copy bgz'
        elif ffn.endswith('.tbi'):
            op = 'ignore'
      
        if op=='ignore':
           continue
 
        allFiles.append(tfn)

        if op=="copy":
            cmd =  "cp $^ $@"
        elif op=="reannotate text":
            cmd = "annotate_variants.py $^ 2> %s-out.txt | re_annotate_variants.py > $@" % (tfnLog)
        elif op=="reannotate bgz":
            cmd = "zcat $^ | annotate_variants.py -c chr -p position - 2> %s-out.txt | bgzip -c > $@ && tabix -s 1 -b 2 -e 2 $@ 2> %s-tabix.txt" % (tfnLog, tfnLog)
        elif op=="copy bgz":
            cmd = "cp $^ $@ && tabix -s 1 -b 2 -e 2 $@ 2> %s-tabix.txt" % (tfnLog)

        print('%s: %s\n\t(time %s) 2> %s-time.txt\n' % (tfn, ffn, cmd, tfnLog))

 
        # print "\t", f, op
         
print("all:", " ".join(allFiles))


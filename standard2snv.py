#!/data/software/local/bin/python

import csv
import sys

lol = list(csv.reader(open(sys.argv[1], 'rb'), delimiter='\t'))

#print sys.argv[1]
#print lol[0]
#['familyId', 'location', 'variant', 'bestState', 'who', 'why', 'val.counts', 'val.bestState', 'val.autoStatus', 'val.status', 'val.note', 'val.parent']
#quadId  Location        refBase altBase allBaseCnts     bestState 
print "\t".join(['quadId', 'Location', 'refBase', 'altBase', 'allBaseCnts', 'bestState'])
for n in range(1,len(lol)-1):
    #ind = lol[n][1].index(':')
    #chr = lol[n][1][:ind]
    #pos = lol[n][1][ind+1:]
    altR = lol[n][2][4]
    altA = lol[n][2][7]
    quadId = 'auSSC'+str(lol[n][0])+'-wholeblood'
    print "\t".join([quadId,lol[n][1],altR,altA, lol[n][6], lol[n][7] ])
    #print altR,"\t",altA
    #print chr,"\t",pos
    #print lol[n]


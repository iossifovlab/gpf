#!/data/software/local/bin/python

import csv

lol = list(csv.reader(open('validationWithDuplicates20131018.txt', 'rb'), delimiter='\t'))
#lol[0] = ['familyId', 'location', 'variant', 'val.batchId', 'val.status', 'val.resultNote', 'val.parent', 'val.counts']
lol1 = sorted(lol[1:],key=lambda x:str(x[1:2]))

#for n in range(len(lol1)-1):
#    print "\t".join(lol1[n])
#    #print "\t".join(lol1[n])
#exit()

lout=[]
lout.append(lol[0])
n = 0
while n < (len(lol1)-1):
    if lol1[n+1][0] == lol1[n][0] and lol1[n+1][1] == lol1[n][1] and lol1[n+1][2] == lol1[n][2] :
        if lol1[n+1][4] == 'valid' or lol1[n][4] == 'valid':
            if lol1[n+1][4] == 'valid':
                lout.append(lol1[n+1])
            else:
                lout.append(lol1[n])
        elif lol1[n+1][4] == 'invalid' or lol1[n][4] == 'invalid':
            if lol1[n+1][4] == 'invalid':
                lout.append(lol1[n+1])
            else:
                lout.append(lol1[n])
        elif lol1[n+1][4] == 'failed' or lol1[n][4] == 'failed':
            if lol1[n+1][4] == 'failed':
                lout.append(lol1[n+1])
            else:
                lout.append(lol1[n])
        else:
            if lol1[n+1][3] > lol1[n][3]:
                lout.append(lol1[n+1])
            else:
                lout.append(lol1[n])
        n+=2
    else:
        lout.append(lol1[n])
        n+=1
lout.append(lol1[n])
lout.append(lol1[len(lol1) -1])

for n in range(len(lout)-1):
    print "\t".join(lout[n])
    #print "\t".join(lol1[n])
            
        


    



        

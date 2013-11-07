#!/bin/env python

# July 12th 2013
# written by Ewa

import networkx as nx
from collections import namedtuple
from collections import defaultdict


class regIvan:
    def __init__(self,chr,start,stop):
        self.chr = chr
        self.start = start
        self.stop = stop

def connected_component(*r):

    G = nx.Graph()
    R = [el for list in r for el in list]
    
    sorted(R, key=lambda x: int(x[0]))
    
    G.add_nodes_from(R)
        
    for k in xrange(1, len(R)):
        for j in xrange(k-1,-1,-1):
            if R[k].chr == R[j].chr and R[k].start <= R[j].stop:
                G.add_edge(R[k], R[j])
        

        

    CC = nx.connected_components(G)
    return(CC)


def collapse(r, is_sorted=False): 

    reg = namedtuple('reg', 'start stop chr')
    
    if is_sorted == False:
        r.sort(key=lambda x: int(x[0]))

    C=defaultdict(list)

    C[r[0].chr].append(r[0])
    
    for i in r[1:]:
        try:
            j = C[i.chr][-1]
        except:
            C[i.chr].append(i)
            continue

        if i.start <= j.stop:
            if i.stop > j.stop:
                del C[i.chr][-1]
                C[i.chr].append(reg(chr=i.chr, start=j.start, stop=i.stop))
            continue

        C[i.chr].append(i)


    L = []
    for v in C.values():
        L.extend(v)
        

    return L



def collapse_noChr(r, is_sorted=False):

    if r == []:
        return r

    reg = namedtuple('reg', 'start stop')
    
    if is_sorted == False:
        r.sort(key=lambda x: int(x[0]))

    C = [r[0]]
    for i in r[1:]:
        j = C[-1]
        if i.start <= j.stop:
            if i.stop > j.stop:
                del C[-1]
                C.append(reg(start=j.start, stop=i.stop))
                # C[-1].stop = i.stop
            continue
                
        C.append(i)
          
    return C
            
    

def intersection(s1, s2):

    I = []

    sorted(s1, key=lambda x: int(x[1]))
    sorted(s2, key=lambda x: int(x[0]))
   
           
    reg = namedtuple('reg', 'start stop chr')

    k = 0
    for i in s2:
        while k < len(s1):
           if i.chr != s1[k].chr:
               k+=1
               continue
           if i.start > s1[k].stop:
               k+=1
               continue
           if i.stop < s1[k].start:
               break
           if i.start <= s1[k].start:
               if i.stop >= s1[k].start:
                   I.append(reg(chr=i.chr, start=s1[k].start, stop=i.stop))
               break
               
           if i.start > s1[k].start:
               if i.stop > s1[k].stop:
                   I.append(reg(chr=i.chr, start=i.start, stop=s1[k].stop))
                   k+=1
                   break
               else:
                   I.append(i)
                   break
        if k >= len(s1):
               break

               
    #print I
    return(collapse(I, is_sorted=True))


def union(*r):
    
     r_sum = [el for list in r for el in list]
     return(collapse(r_sum))


def difference(s1, s2):
    
    reg = namedtuple('reg', 'start stop chr')
    D = []
    I = intersection(s1, s2)
    print I

    k = 0
    sorted(s1, key=lambda x: int(x[0]))

    for i in s1:
        
        if I[k].start > i.stop:
            D.append(i)
            continue
        
        while k < len(I) and I[k].start <= i.stop:
            if I[k].chr != i.chr:
                k+=1
                continue
            if I[k].start == i.start:
                if I[k].stop == i.stop:
                    k+=1
                    break
                if k+1 < len(I) and I[k+1].start  <= i.stop:
                    D.append(reg(chr=i.chr, start = I[k].stop+1, stop = I[k+1].start-1))
                    k+=1
                    continue
                                 
                                 
            else:
                if I[k].stop <= i.stop:
                    if len(D) == 0:
                        D.append(reg(chr=i.chr, start = i.start, stop=I[k].start-1))
                    else:
                        if D[-1] != reg(chr=i.chr, start = max(i.start, I[k-1].stop+1), stop=I[k].start-1):
                            D.append(reg(chr=i.chr, start = max(i.start, I[k-1].stop+1), stop=I[k].start-1))
                    k+=1
                    continue
        if I[k-1].stop < i.stop:
            D.append(reg(chr=i.chr, start = I[k-1].stop+1, stop = i.stop))

        

        if k >= len(I):
            break
                    

    return(D)

        
#reg = namedtuple('reg', 'start stop chr')#print intersection([reg(chr=2,start=9,stop=11),reg(chr=1,start=1,stop=5), reg(chr=1, start=4, stop=7)],[reg(chr=1,start=4,stop=10)],)
#print difference([reg(chr=2,start=1,stop=10), reg(chr=1,start=20,stop=30), reg(chr=1,start=40,stop=50), reg(chr=1,start=60,stop=70)],[reg(chr=1,start=4,stop=6), reg(chr=1,start=15,stop=22), reg(chr=1,start=25,stop=28), reg(chr=1,start=65,stop=70)])

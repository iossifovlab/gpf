#!/bin/env python

# Nov 7th 2013
# written by Ewa

import networkx as nx
from collections import namedtuple
from collections import defaultdict


class Region:

    def __init__(self, chr, start, stop):
        self.chr = chr
        self.start = start
        self.stop = stop

    def __str__(self):
        return(self.chr + " " + str(self.start) + " " + str(self.stop))

def all_regions_from_chr(R, chr):
    A = [r for r in R if r.chr == chr]
    return(A)
        

def unique_regions(R):
    D = defaultdict(list)
    
    for r in R:
        D[r.chr].append(r)

    for chr in D.keys():
        D[chr].sort(key=lambda x: x.start)
   
    for chr,nds in D.items():
        cp_nds = list(nds)
        k = 1
        removed = 0
        for i in cp_nds[1:]:
            for j in xrange(k-1,-1,-1):
                if i.start != cp_nds[j].start:
                    break
                if i.stop == cp_nds[j].stop:
                    print D[chr][k-removed]
                    del D[chr][k-removed] #?
                    removed += 1
                    break
            k += 1
        
      
    U = [x for y in D.values() for x in y]
    
    return(U)
        

def connected_component(R):

    Un_R = unique_regions(R)

    G = nx.Graph()

    G.add_nodes_from(R)

    D = defaultdict(list)
    for r in R:
        D[r.chr].append(r) 


    for chr,nds in D.items():
        nds.sort(key=lambda x: x.stop)
        for k in xrange(1, len(nds)):
            for j in xrange(k-1,-1,-1):
                if nds[k].start <= nds[j].stop:
                    G.add_edge(nds[k], nds[j])
                else:
                    break
        
    CC = nx.connected_components(G)
    return(CC)


def collapse(r, is_sorted=False): 

    
    if is_sorted == False:
        r.sort(key=lambda x: x.start)

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
                C[i.chr][-1].stop = i.stop
            continue

        C[i.chr].append(i)


    L = []
    for v in C.values():
        L.extend(v)
        

    return L



def collapse_noChr(r, is_sorted=False):

    if r == []:
        return r

    
    if is_sorted == False:
        r.sort(key=lambda x: x.start)


    C = [r[0]]
    for i in r[1:]:
        j = C[-1]
        if i.start <= j.stop:
            if i.stop > j.stop:
                C[-1].stop = i.stop
            continue
                
        C.append(i)
          
    return C
            
#------------------------------------------------
#TO BE CHECKED AND SPEED UP

def intersection(s1, s2):

    I = []

    s1.sort(key=lambda x: int(x[1]))
    s2.sort(key=lambda x: int(x[0]))
   
           
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

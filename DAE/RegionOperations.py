#!/bin/env python

# Nov 7th 2013
# written by Ewa

import networkx as nx
from collections import namedtuple
from collections import defaultdict
import copy

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

    r_copy = copy.deepcopy(r)

    if is_sorted == False:
        r_copy.sort(key=lambda x: x.start)

    C=defaultdict(list)

    C[r_copy[0].chr].append(r_copy[0])
    
    for i in r_copy[1:]:
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
    r_copy = copy.copy(r)
    
    if is_sorted == False:
        r_copy.sort(key=lambda x: x.start)

    C = [r_copy[0]]
    for i in r_copy[1:]:
        j = C[-1]
        if i.start <= j.stop:
            if i.stop > j.stop:
                C[-1].stop = i.stop
            continue
                
        C.append(i)
          
    return C
            

def intersection(s1,s2):
    s1_c = collapse(s1)
    s2_c = collapse(s2)
    s1_c.sort(key=lambda x : (x.chr, x.start))
    s2_c.sort(key=lambda x : (x.chr, x.start))
    
    I = []

    k = 0

    for i in s2_c:
        while k < len(s1_c):
            if i.chr != s1_c[k].chr:
                if i.chr > s1_c[k].chr:
                    k += 1
                    continue
                break
            if i.stop < s1_c[k].start:
                break
            if i.start > s1_c[k].stop:
                k += 1
                continue
            if i.start <= s1_c[k].start:
                if i.stop >= s1_c[k].stop:
                    I.append(s1_c[k])
                    k += 1
                    continue
                new_i = copy.copy(i)
                new_i.start = s1_c[k].start              
                I.append(new_i)
                break
            if i.start > s1_c[k].start:
                if i.stop <= s1_c[k].stop:
                    I.append(i)
                    break
                new_i = copy.copy(i)
                new_i.stop = s1_c[k].stop
                I.append(new_i)
                k += 1
                continue
    
    return(I)


def union(*r):
    
     r_sum = [el for list in r for el in list]
     return(collapse(r_sum))



def difference(s1, s2):
    # union - intersection
    D = []
    U = union(s1, s2)
    U.sort(key=lambda x: (x.chr, x.start))
    I = intersection(s1, s2)

    k = 0

    for u in U:
        if k >= len(I):
            D.append(u)
            continue 
        if u.chr < I[k].chr:
            D.append(u)
            continue
        if u.stop < I[k].start:
            D.append(u)
            continue
        prev = u.start
        while k < len(I) and I[k].stop <= u.stop:
            if prev < I[k].start:
                new_u = Region(u.chr, prev, I[k].start - 1)
                D.append(new_u)
            prev = I[k].stop + 1
            k+=1
        if prev <= u.stop:
           D.append(Region(u.chr, prev, u.stop))
        
    return(D)
        
            


    
  
        

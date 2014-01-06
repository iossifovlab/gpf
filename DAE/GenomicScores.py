#!/bin/env python

# Nov 27th 2013
# by Ewa

import tarfile
import numpy as np
import os, sys
import gzip
import pickle
from collections import defaultdict
from operator import itemgetter
import re
from RegionOperations import *
import h5py


class GenomicScore:
    location = None
    name = None
    Scores = None
    _Keys = None
    _score_names = None
    chr_format = None

    def _create_index_gerp(self):
        self._Indexing =  defaultdict(dict)
        self._Keys = {}
        for k, v in self.Scores['gerp'].items():
            self._Indexing[k][(1, len(v))] = (0, len(v)-1)

            self._Keys[k] = sorted(self._Indexing[k].keys(), key=lambda x: int(x[0])) 
            

    def _create_array_gerp(self, file):

        self.location = file
        self.Scores = {}
        self.Scores['gerp'] = {}
        self._score_names = ['gerp']
        
        
        tar = tarfile.open(file, 'r')
        for member in tar.getnames():
            L = []
            sys.stderr.write(member + "\n")
            chr = member[:member.index(".")]
            if chr.startswith("chr"):
                self.chr_format = "hg19"
            else:
                self.chr_format = "GATK"
            file = tar.extractfile(member)
            for line in file:
                L.append(float(line.split()[1]))
            self.Scores['gerp'][chr] =  np.array(L, dtype='<f4')
          
        tar.close()

        self._create_index_gerp()


    def _create_index_p(self, dir):
        self._Indexing =  defaultdict(dict) 
        self._Keys = {}
        sys.stderr.write("Creating the index..............\n")
        listing = [ f for f in os.listdir(dir) if f.endswith(".gz") ]
        for file in listing:
                sys.stderr.write("index for: " + file + "\n")
                chr = file[:file.index('.')]
                f = gzip.open(dir + "/" +  file,'rb')
                K = 0
                k = 0
                start = None
                for line in f:
                    if line[0] == "f":
                        if start:
                            self._Indexing[chr][(start, start+k-1)] = (K, K+k-1)
                        K += k
                        line = line.split()
                        start = int(line[2][6:])
                        k = 0 
                    else:
                        k += 1

                if start == None:
                    sys.stderr.write("Incorrect file format: " + dir + "/" +  file + " ....skipping\n")
                    continue
                self._Indexing[chr][(start, start+k-1)] = (K, K+k-1)        
                K += k
                self._Keys[chr] = sorted(self._Indexing[chr].keys(), key=lambda x: int(x[0]))
        f.close()
        

    def _create_array_p(self, dir):
        self.location = dir
        self.Scores = defaultdict(dict)

        for subdir in ['Primates', 'Placental', 'Vertebrates']:
            new_dir = dir + "/" + subdir + "/"
            if subdir == 'Primates':
                self._create_index_p(new_dir)
                sys.stderr.write("\nCreating arrays with the conservation scores....\n")
            sys.stderr.write(subdir + "..............\n")

            listing = [ f for f in os.listdir(new_dir) if f.endswith(".gz") ]
            for file in listing:
                sys.stderr.write(file + "\n")
                chr = file[:file.index('.')]
                if chr.startswith("chr"):
                    self.chr_format = "hg19"
                else:
                    self.chr_format = "GATK"
                f = gzip.open(new_dir + "/" +  file,'rb')
                
                L=[] # list with all phastCons scores
                
                for line in f:
                    if line[0] != "f":
                        L.append(float(line[:-1]))
                
                self.Scores[subdir][chr] = np.array(L, dtype='<f4')
            f.close()
            
        self._score_names = ['Primates', 'Placental', 'Vertebrates']

    def _create_index_only_target_file(self, target_file, is_sorted = True):
        self._Indexing =  defaultdict(dict) 
        self._Keys = defaultdict(list) 
        sys.stderr.write("Creating the index..............\n")

        file = open(target_file)
        for line in file:
            line = line.split()
            self._Keys[line[0]].append((int(line[1]), int(line[2])))
        file.close()

        if is_sorted == False:
            for v in self._Keys.values():
                v.sort()

        for chr, vls in self._Keys.items():
            k = 0
            for v in vls:
                k2 = v[1] - v[0]
                self._Indexing[chr][v] = (k, k2)
                k = k2 + 1

        if self._Indexing.keys()[0].startswith("chr"):
            self.chr_format = "hg19"
        else:
            self.chr_format = "GATK"

        self.name = "target_index"
        
    def __join_intervals(self, D):

        for chr in D.keys():
            prev = (-2,-2)
            for key in sorted(D[chr].keys(), key=lambda tup: tup[0]):
                if key[0] == prev[1] + 1:
                    D[chr][(prev[0], key[1])] = (D[chr][prev][0], D[chr][key][1])
                    del D[chr][prev]
                    del D[chr][key]
                    prev = (prev[0], key[1])
                else:
                    prev = key
 

    def __create_index_binary(self, Ar, D, k):
    
        posb = Ar[0][1]
        chrb = Ar[0][0]
        pose = Ar[-1][1]
        chre = Ar[-1][0]
        length = len(Ar)
        if chrb == chre and pose - length + 1 == posb:
            D[chrb][(posb, pose)] = (k, k+length-1)
        
        else:
            self.__create_index_binary(Ar[:length/2], D, k)
            self.__create_index_binary(Ar[length/2:], D, k+length/2)

                
    def _create_mut_prob_array_index(self, Ar):
        Inds = defaultdict(dict)
        self.__create_index_binary(Ar, Inds, 0)
        self.__join_intervals(Inds)
        return(Inds)
        

 
    def save_hdf5(self, file):
        sys.stderr.write("..saving..\n")

        if file.endswith(".hdf5") == False:
            file = file + ".hdf5"
        
        h5py_file = h5py.File(file, 'w')
        for subscore in self.Scores.keys():
            grp = h5py_file.create_group(subscore)
            for k, v in self.Scores[subscore].items():
                grp.create_dataset(k, data=v)
        
        grp = h5py_file.create_group("Index")
        for key in self._Indexing.keys():
            L = []
            for k, v in self._Indexing[key].items():
                L.append((k[0], k[1], v[0], v[1]))
            grp.create_dataset(key, data=np.array(L))
        
            
        h5py_file.close()

   
        
    def _load_hdf5(self, file, format=None):
        self.Scores = defaultdict(dict)
        self._Indexing = defaultdict(dict)
        self._Keys = {}
        self.name = format
        self.location = file

       
        #for chr in self._Indexing.keys():
        #    self._Keys[chr] = sorted(self._Indexing[chr].keys(), key=lambda x: int(x[0]))
        
        
        
        f = h5py.File(file, 'r')
        
        
        if f['Index'].keys()[0].startswith("chr"):
            self.chr_format = "hg19"
        else:
            self.chr_format = "GATK"
            
        for chrom, vals in f['Index'].items():
            for i in vals:
                self._Indexing[str(chrom)][(i[0], i[1])] = (i[2], i[3])
            self._Keys[str(chrom)] = sorted(self._Indexing[str(chrom)].keys(), key=lambda x: int(x[0]))
        
            
        alignments = [str(align) for align in f.keys() if align != "Index"]
        if len(alignments) == 3 and all(i in alignments for i in ['Placental', 'Primates', 'Vertebrates']):
            self._score_names = ['Primates', 'Placental','Vertebrates']
        else:
            self._score_names = alignments
            
        for i in alignments:
            for k, v in f[i].items():
                try:
                    self.Scores[i][str(k)] = np.array(v)
                except:
                    self.Scores[i][str(k)] = np.empty(shape=0)

  
    def save_exome_scores(self, file):
        
        sys.stderr.write("..saving..\n")
        
        if file.endswith(".npz") == False:
            file = file + ".npz"
            

        args = []
        kwds = []
        for subscore in self.Scores.keys():
            for k,v in self.Scores[subscore].items():
                args.append(v)
                kwds.append(subscore + ":" + k)


        for key in self._Indexing.keys():
            L = []
            for k, v in self._Indexing[key].items():
                L.append((k[0], k[1], v[0], v[1]))
            kwds.append("Index:" + key)
            args.append(np.array(L))
            
        np.savez(file, arrays=args, subscores = kwds)
            
        #for subscore in self.Scores.keys():
        #    if os.path.isdir(dir + "/" + subscore + "/") == False:
        #        os.makedirs(dir + "/" + subscore + "/")
           
            #np.savez(dir + "/" + subscore + "/all_chr", self.Scores[subscore].values())
         #   for k,v in self.Scores[subscore].items():
         #       np.save(dir + "/" + subscore + "/" + k, v)
        #seq_pickle = dir + "/Index.dump"
        #pickle.dump(self._Indexing, open(seq_pickle, 'wb'))
    
    def _load_exome_scores(self, file, name = None):
        self.Scores = defaultdict(dict)
        self._Indexing = defaultdict(dict)
        self._Keys = {}
        self.location = file
        self.name = name
        
        f = np.load(file)

        score_names = []

        for subscore,ar in zip(f['subscores'], f['arrays']):
            s1, s2 = subscore.split(":")
            s1 = str(s1)
            s2 = str(s2)
            if self.chr_format == None:
                if s2.startswith("chr"):
                    self.chr_format = "hg19"
                else:
                    self.chr_format = "GATK"
            if s1 == "Index":
                for i in ar:
                   self._Indexing[s2][(i[0], i[1])] = (i[2], i[3])
            else:
                score_names.append(s1)
                self.Scores[s1][s2] = ar

        for chr in self._Indexing.keys():
            self._Keys[chr] = sorted(self._Indexing[chr].keys(), key=lambda x: int(x[0]))

        self._score_names = list(set(score_names))
        if all(i in self._score_names for i in ['Placental', 'Primates', 'Vertebrates']):
            self._score_names = ['Primates', 'Placental','Vertebrates']
        elif self.name == "gc":
            self._score_names.sort(key = lambda x: int(x.split("_")[1]))

    def __reindex(self):
        for chr in self._Indexing.keys():
            diff = self._Indexing[chr][self._Keys[chr][0]][0]
            new_Ind = {}
            for k, v in sorted(self._Indexing[chr].items()):
                new_Ind[k] = (v[0]-diff, v[1]-diff)
        
            self._Indexing[chr] = new_Ind  
                
        

    def _create_mut_prob_array_features(self, file, feature):

        available_features = ['nt', 'GC', 'cov', 'pos']
        if feature not in available_features:
            raise Exception("No " + feature + " in the input array!")

        self.Scores = defaultdict(dict)
        self._Keys = {}
        self.location = file
        self.name = feature
        
        A = np.load(file)
        
        columns = [x for x in A.dtype.names if feature in x]

        self._score_names = columns
        
        self._Indexing = self._create_mut_prob_array_index(A)
        
        for chr in self._Indexing.keys():
            if self.chr_format == None:
                if chr.startswith("chr"):
                    self.chr_format = 'hg19'
                else:
                    self.chr_format = 'GATK'
            self._Keys[chr] = sorted(self._Indexing[chr].keys(), key=lambda x: int(x[0]))
        
        
        for k in self._Indexing.keys():
            minIndex = self._Indexing[k][self._Keys[k][0]][0]
            maxIndex = self._Indexing[k][self._Keys[k][-1]][1]
            for col in columns:
                self.Scores[col][k] = A[minIndex:maxIndex+1][col]

        self.__reindex()
            
            
        
    

    def cut_target(self, target_file="/mnt/wigclust5/data/safe/egrabows/2013/MutationProbability/NMWE50_20.1.target.bed", target_file_format = "GATK"):
        if self.chr_format == "hg19" and target_file_format == "GATK":
            new_gs = self.relabel_chromosomes_2()
        else:
            new_gs = self
                    
        file = open(target_file)
        Locs = []
        for line in file:
            line = line.split()
            loc = (line[0] + ":" + line[1] + "-" + line[2])
            Locs.append(loc)
        TS = new_gs.get_multi_score(Locs, if_sorted=True, region = True)#, fill_with_NA = True)
        file.close()
        
        
        gs = GenomicScore()
        gs.name = self.name
        gs._score_names = self._score_names
        gs.location = self.location
        gs.chr_format = target_file_format

        cols = len(gs._score_names)
        
        gs.Scores = defaultdict(dict)
        gs._Keys = {}
        gs._Indexing = defaultdict(dict)
        
        number_of_alignments = len(gs._score_names)

        TS_dict = defaultdict(list)
        for ts in TS:
            if ts[cols]:
                TS_dict[ts[cols][0].chr].append(ts)

       
        #for chrom in new_gs._Keys.keys(): ###?
        #    one_chr = [x for x in TS if x[cols] and x[cols][0].chr == chrom]
        for chr, vls in TS_dict.items():
    
            for sp in xrange(0, number_of_alignments):
                try:
                    gs.Scores[gs._score_names[sp]][chr] = np.concatenate([y[sp] for y in vls])
                except:
                    pass
            ind_k = 0
            for v in vls:
                for m in v[cols]:
                    gs._Indexing[chr][(m.start, m.stop)] = (ind_k, ind_k + m.stop - m.start)
                    ind_k += m.stop - m.start + 1
            gs._Keys[chr] = sorted(gs._Indexing[chr].keys(), key=lambda x: int(x[0]))
        
        return gs
    
    def _load_array(self, dir): 
        self.Scores = defaultdict(dict)
        self._Indexing = defaultdict(dict)
        self._Keys = {}
        
        all_dir = [d for d in os.listdir(dir) if os.path.isdir(dir + "/" + d)]
        if len(all_dir) == 3 and all(i in all_dir for i in ['Placental', 'Primates', 'Vertebrates']):
            self._score_names = ['Primates', 'Placental','Vertebrates']
        else:
            self._score_names = all_dir
        for subdir in all_dir:
            new_dir = dir + "/" + subdir + "/"
            listing = [ f for f in os.listdir(new_dir) if f.endswith(".npy") ]
            if listing[0][:listing[0].index('.')].startswith("chr"):
                self.chr_format = "hg19"
            else:
                self.chr_format = "GATK"
        
            for file in listing:
                chr = file[:file.index('.')]
                self.Scores[subdir][chr] = np.load(new_dir + file)
                
        pkl_file = open(dir + "/Index.dump", 'rb')
        self._Indexing = pickle.load(pkl_file)
        pkl_file.close()
        
        for chr in self._Indexing.keys():
            self._Keys[chr] = sorted(self._Indexing[chr].keys(), key=lambda x: int(x[0]))
  
    
    def get_lengths(self):

        if self.Scores:
            
            Lengths = {}
            for key in self.Scores.keys():
                for k, v in self.Scores[key].items():
                    Lengths[k] = len(v)
                break

        else:
            Lengths = defaultdict(int)
            for key, vls in self._Keys.items():
                for v in vls:
                   Lengths[key] += v[1] - v[0] + 1 
        return(Lengths)

    def _ucsc2gatk(self, chr):
        chr = chr[3:]
        if len(chr) < 3:
            return(chr)
        try:
            chr = chr[chr.index("_")+1:]
        except ValueError:
            sys.stderr.write("chr" + " - not the hg19 format!\n")
            return(None)
        chr = chr.upper()
        if "_" in chr:
            chr = chr[:chr.index("_")]
        return(chr + ".1")
        

    def relabel_chromosomes_2(self):
        gs = GenomicScore()
        gs.name = self.name
        gs.Scores = defaultdict(dict)
        gs._Keys = {}
        gs._Indexing = {}
        gs._score_names = self._score_names 

        for key in self.Scores:
            sys.stderr.write("Relabeling for: " + key + "\n")
            for k, v in self.Scores[key].items():
                gs.Scores[key][self._ucsc2gatk(k)] = v

        for k,v in self._Indexing.items():
            gs._Indexing[self._ucsc2gatk(k)] = v

        for k, v in self._Keys.items():
            gs._Keys[self._ucsc2gatk(k)] = v

        gs.chr_format = "GATK"
        return(gs)
        
                   
    def relabel_chromosomes(self, file="/data/unsafe/autism/genomes/hg19/ucsc2gatk.txt"):
    
        f = open(file)
        Relabel = dict([(line.split()[0], line.split()[1]) for line in f])
        f.close()

        for key in self.Scores:
            sys.stderr.write("Relabeling for: " + key + "\n")
            for k, v in self.Scores[key].items():
                try:
                    self.Scores[key][Relabel[k]] = v
                    del self.Scores[key][k]
                except:
                    sys.stderr.write("Unknown chromosome: " + k + " -  has not been changed\n")
                
        for k,v in self._Indexing.items():
            try:
                self._Indexing[Relabel[k]] = v
                del self._Indexing[k]
            except:
                pass

        for k, v in self._Keys.items():
            try:
                self._Keys[Relabel[k]] = v
                del self._Keys[k]
            except:
                pass

        self.chr_format = "GATK"
            
            
    def _bin_search1(self, chr, p):       
        b = 0
        e = len(self._Keys[chr])

        while True:
            x = b + (e-b)/2 
            if self._Keys[chr][x][1] >= p >= self._Keys[chr][x][0]:
                return((True, x, self._Indexing[chr][self._Keys[chr][x]][0] + p - self._Keys[chr][x][0]))
            if p < self._Keys[chr][x][0]:
                e = x-1
            else:
                b = x+1
            if b > e:
                return((False,b))

    def _get_scores_for_region(self, loc, scores=None):


        if scores == None:
            scores = self._score_names
        else:
            for i in scores:
                if i not in self._score_names:
                    sys.stderr.write("Unknown scores parameter: " + s + "\n")
                    sys.exit(-454)

        chr, pos = loc.split(":")
        posB, posE = map(int, pos.split("-"))
        ind = self._bin_search1(chr, int(posB))
        
        K = []
        k = ind[1]
        length = len(self._Keys[chr])
        while k < length and posB > self._Keys[chr][k][1]:
            k+=1
        while  k < length and posE >= self._Keys[chr][k][0]:
            K.append(self._Keys[chr][k])
            k+=1
        if K == []:
            return(K)
        
        x = K[0]
        y = K[-1]
        
        if posB <= x[0]:
            left_ind = self._Indexing[chr][x][0]
        else:
            left_ind = self._Indexing[chr][x][0] + posB-x[0]
            K[0] = (posB,x[1])
        
        if posE >= y[1]:
            right_ind = self._Indexing[chr][y][1]
        else:
            right_ind = self._Indexing[chr][y][0] + posE-y[0]
            K[-1] = (K[-1][0], posE)
        
        
        scrs = [self.Scores[i][chr][left_ind:right_ind+1] for i in scores]
        Rgns = [Region(chr, x[0], x[1]) for x in K]
        scrs.append(Rgns)
        return(scrs)

    def __mapping(self, L):
        return([L[0], int(L[1]), int(L[2])])

    def _get_multi_scores_for_region(self, locs, scores, if_sorted):#, fill_with_NA = False):
  
        K2 = []
        
        locs2 = [self.__mapping(re.split(":|-", x)) for x in locs]
        
        if if_sorted == False:
            order, locs2 = zip(*sorted([(i,v) for i,v in enumerate(locs2)], key=itemgetter(1)))
            
        k_prev = 0
        chr = None
        for i in locs2:
            if i[0] not in self._Keys.keys():
                #if fill_with_NA == True:
                #    scrs = [["NA"]*(i[2]-i[1]+1) for s in scores]
                #    scrs.append([Region(i[0], i[1], i[2])])
                #else:
                scrs = [[] for s in scores]
                scrs.append([])
                K2.append(scrs)
                continue
            if i[0] != chr:
                k = 0
                chr = i[0]
                length = len(self._Keys[chr])
            else:
                k = k_prev
            posB = i[1]
            posE = i[2]
            K=[]
            while  k < length and self._Keys[chr][k][1] < posB:
                k += 1
            k_prev = k       
            while  k < length and posE >= self._Keys[chr][k][0]:
                K.append(self._Keys[chr][k])
                k+=1
            if K == []:
                #if fill_with_NA == True:
                #    scrs = [["NA"]*(posE-posB+1) for s in scores]
                #    scrs.append([Region(chr, posB, posE)])
                #else:
                scrs = [[] for s in scores]
                scrs.append([])
                K2.append(scrs)
                continue
            x = K[0]
            y = K[-1]
            if posB <= x[0]:
                left_ind = self._Indexing[chr][x][0]
            else:
                left_ind = self._Indexing[chr][x][0] + posB-x[0]
                K[0] = (posB,x[1])
            if posE >= y[1]:
                right_ind = self._Indexing[chr][y][1]
            else:
                right_ind = self._Indexing[chr][y][0] + posE-y[0]
                K[-1] = (K[-1][0], posE)

            scrs = [self.Scores[s][chr][left_ind:right_ind+1] for s in scores]
            Rgns = [Region(chr, x[0], x[1]) for x in K]
            """
            if fill_with_NA == True:
                if Rgns[0].start > posB:
                    for p in xrange(0, len(scrs)-1):
                        scrs[p].insert(0, ['NA']*(Rgns[0].start-posB))
                r_ind = 0
                for r in xrange(0, len(Rgns)-1):
                    r_ind += Rgns[r].stop - Rgns[r].start + 1
                    for p in xrange(0, len(scrs)-1):
                        scrs[p].insert(r_ind, ['NA']* (Rgns[r+1].start - Rgns[r].stop - 1))

                if Rgns[-1].stop < posE:
                    for p in xrange(0, len(scrs)-1):
                        scrs[p].extend(['NA']*(posE - Rgns[-1].stop))

                Rgns = [Region(chr, posB, posE)] 
            """     
         
                    
                    
            scrs.append(Rgns) 
            K2.append(scrs)

        if if_sorted == True:
            return(K2)
        else:
            R2 = [0]*len(K2)
            r = 0
            for i in order:
                R2[i] = K2[r]
                r+=1
            return(R2)
            
            
            
    def get_score(self, loc, scores=None, region=False):
        
        if region == True:
            scrs = self._get_scores_for_region(loc, scores)
            return(scrs)

        
        chr, pos = loc.split(":")
        ind = self._bin_search1(chr, int(pos))
        
        if ind[0] == False:
            return([])
        if scores == None:
            scrs = [self.Scores[i][chr][ind[2]] for i in self._score_names]
            return(scrs)
        else:
            scrs = []
            for s in scores:
                if s not in self._score_names:
                    sys.stderr.write("Unknown scores parameter: " + s + "\n")
                    sys.exit(-452)
                scrs.append(self.Scores[s][chr][ind[2]])
            return(scrs)

    def get_index(self, loc):
        chr, pos = loc.split(":")
        ind = self._bin_search1(chr, int(pos))
        if ind[0] == False:
            return(None)
        return(ind[2])

    def get_score_names(self):
        return(self._score_names)

    def get_multi_score(self, locs, scores=None, region = False, if_sorted=False):#, fill_with_NA = False):

        if scores == None:
            scores = self._score_names
        else:
            for i in scores:
                if i not in self._score_names:
                    sys.stderr.write("Unknown scores parameter: " + s + "\n")
                    sys.exit(-453)

        if region == True:
            scrs = self._get_multi_scores_for_region(locs, scores, if_sorted)#, fill_with_NA)
            return(scrs)

        #locs2 = np.array([(x.split(":")[0], int(x.split(":")[1])) for x in locs], [('chr', '<S20'), ('pos', int)])
        locs2 = [(x.split(":")[0], int(x.split(":")[1])) for x in locs]
        if if_sorted == False:
            order, locs2 = zip(*sorted([(i,v) for i,v in enumerate(locs2)], key=itemgetter(1)))
            #order, locs2 = zip(*np.argsort([(i,v) for i,v in enumerate(locs2)], key=itemgetter(1)))
        
        R = []
        
        prev_chr = locs2[0][0]
        k=0
        length = len(self._Keys[prev_chr])
        for l in locs2:
            if l[0] not in self._Keys.keys():
                R.append([])
                continue
            if l[0] != prev_chr:
                prev_chr = l[0]
                length = len(self._Keys[l[0]])
                k=0
            while k < length and l[1] > self._Keys[l[0]][k][1]:
                k += 1
            if k >= length:
                R.append([])
                continue
            x = self._Keys[l[0]][k]
            if l[1] < x[0]:
                R.append([])
                continue
            if l[1] <= x[1]:
                ind = l[1] - x[0] + self._Indexing[l[0]][x][0]
                R.append([self.Scores[i][l[0]][ind] for i in scores])
                continue
            R.append([])

        if if_sorted == True:
            return(R)
        else:
            R2 = [0]*len(R)
            k = 0
            for i in order:
                R2[i] = R[k]
                k+=1
            return(R2)


    def get_regions(self):
        Region_list = []
        for chrom, rgns in self._Keys.items():
            for r in rgns:
                Region_list.append(Region(chrom, r[0], r[1]))
        return(Region_list)

    """
    def create_one_array(self):

        L = self.get_lengths()
        scores = self._score_names
        #length = sum(L.values())
        col_names='chr,pos,' + ",".join(scores)
        D = {}

        
        for chrom, vls in self._Keys.items():
            arr = []
            
            for v in vls:
                arr.append(np.arange(v[0], v[1]+1))
            chr = np.array([chrom]*L[chrom], dtype='<a6')
            pos = np.hstack(arr)
            one_chr = [chr, pos]
            for i in scores:
                one_chr.append(self.Scores[i][chrom])
            D[chrom] = np.core.records.fromarrays(one_chr, names=col_names)

        to_concat = []
        #m = 0
        #Indexing = defaultdict()
        #return(D)
        for chr,arr in sorted(D.items()):
            to_concat.append(arr)
            #for k, v in sorted(self._Indexing[chr].items()):
            #    Indexing[chr][k] = (v[0]+m, v[1]+m)
            #    m += v[1] - v[0] + 1

        D_concat = np.concatenate(to_concat)
        return(D_concat)
    """


class OneArray:
    array = None
    index = None
    """
    def __join_intervals(self, D):

        for chr in D.keys():
            prev = (-2,-2)
            for key in sorted(D[chr].keys(), key=lambda tup: tup[0]):
                if key[0] == prev[1] + 1:
                    D[chr][(prev[0], key[1])] = (D[chr][prev][0], D[chr][key][1])
                    del D[chr][prev]
                    del D[chr][key]
                    prev = (prev[0], key[1])
                else:
                    prev = key

    def __create_index_binary(self, Ar, D, k):
    
        posb = Ar[0]['pos']
        chrb = Ar[0]['chr']
        pose = Ar[-1]['pos']
        chre = Ar[-1]['chr']
        length = len(Ar)
        if chrb == chre and pose - length + 1 == posb:
            D[chrb][(posb, pose)] = (k, k+length-1)

        else:
            self.__create_index_binary(Ar[:length/2], D, k)
            self.__create_index_binary(Ar[length/2:], D, k+length/2)

    def create_index(self):

        Inds = defaultdict(dict)
        self.__create_index_binary(self.array, Inds, 0)
        self.__join_intervals(Inds)
        #Inds.pop('X')
        #Inds.pop('Y')
        self.index = Inds
        #return(Inds)
    """

def integrate(Ar, Index, GeneRgns, column='pp_1'):
    DD = defaultdict(lambda : defaultdict(int))


    p = 0
    I = sorted(Index['1'].keys())
    length = len(I)
    chr_prev = '1'
    for l in GeneRgns:
        chr = str(l[0])
        if chr != chr_prev:
            I = sorted(Index[chr].keys())
            chr_prev = chr
            length = len(I)
            p = 0

        ex_b = l[1]
        ex_e = l[2]
        pointer = p


        while pointer < length and I[pointer][1] < ex_b:
            pointer += 1
        p = pointer



        DD[l[3]]['length_total'] += ex_e - ex_b + 1

        while pointer < length and I[pointer][0] <= ex_e:

            indexes = Index[chr][I[pointer]]
            if ex_b <= I[pointer][0]:
                begin = indexes[0]
            else:
                begin = indexes[0] + ex_b - I[pointer][0]

            if ex_e >= I[pointer][1]:
                end = indexes[-1]
            else:
                end = indexes[-1] + ex_e - I[pointer][1] 



            DD[l[3]]['score'] += sum(Ar[begin:end+1][column])
            DD[l[3]]['length_cov'] += end - begin + 1


            pointer += 1
    return DD


       
 
def create_gerp(gerp_file):
    gs = GenomicScore()
    gs.name = "gerp"
    gs._create_array_gerp(gerp_file)
    return(gs)

def create_phyloP(phyloP_dir):
    gs = GenomicScore()
    gs.name = "phyloP"
    gs._create_array_p(phyloP_dir)
    return(gs)

def create_phastCons(phastCons_dir):
    gs = GenomicScore()
    gs.name = "phastCons"
    gs._create_array_p(phastCons_dir)
    return(gs)

def create_nt(array="/mnt/wigclust5/data/safe/egrabows/2013/MutationProbability/Arrays/chrAll.npy"):
    gs = GenomicScore()
    gs._create_mut_prob_array_features(array, 'nt')
    return(gs)

def create_GC(array="/mnt/wigclust5/data/safe/egrabows/2013/MutationProbability/Arrays/chrAll.npy"):
    gs = GenomicScore()
    gs._create_mut_prob_array_features(array, 'GC')
    return(gs)

def create_cov(array="/mnt/wigclust5/data/safe/egrabows/2013/MutationProbability/Arrays/chrAll.npy"):
    gs = GenomicScore()
    gs._create_mut_prob_array_features(array, 'cov')
    return(gs)

def create_pos(array="/mnt/wigclust5/data/safe/egrabows/2013/MutationProbability/Arrays/chrAll.npy"):
    gs = GenomicScore()
    gs._create_mut_prob_array_features(array, 'pos')
    return(gs)





def load_dir(dir, format=None):

    if not format:
        if "gerp" in dir.lower():
            format = "gerp"
        elif "phylop" in dir.lower():
            format = "phylop"
        elif "phastcons" in dir.lower():
            format = "phastcons"
            
    if  format.lower() not in ['gerp','phylop', 'phastcons']:
        sys.stderr.write("Unrecognizable format! Choose between: gerp, phyloP and phastCons!\n")
        sys.exit(-444)
    gs = GenomicScore()
    gs.location = dir
    gs._load_array(dir)
    gs.name = format
    return(gs)


def load_target_indexing(target_file="/mnt/wigclust5/data/safe/egrabows/2013/MutationProbability/NMWE50_20.1.target.bed", is_sorted = True):
    t = GenomicScore()
    t._create_index_only_target_file(target_file, is_sorted)
    return(t)

def load_genomic_scores(file, format=None):
    if not format:
        if "gerp" in file.lower():
            format = "gerp"
        elif "phylop" in file.lower():
            format = "phylop"
        elif "phastcons" in file.lower():
            format = "phastcons"
        elif 'gc' in file.lower():
            format = "gc"
        elif 'cov' in file.lower():
            format = "cov"
        elif 'nt' in file.lower():
            format = "nt"
        
    if  format.lower() not in ['gerp','phylop', 'phastcons', 'nt', 'gc', 'cov']:
        raise Exception("Unrecognizable format! Available formats: gerp, phylop, phastcons, nt, gc, cov")


    es = GenomicScore()
    if file.endswith(".npz"):
        es._load_exome_scores(file, format)
        return es
    if file.endswith(".hdf5"):
        es._load_hdf5(file, format)
        return es
    
    raise Exception("Unrecognizable format! The program needs a .npz format or .hdf5 format!")    
        
    
        



def create_one_array(*gs):
        
    L = gs[0].get_lengths()
    Index = defaultdict(dict)
    D={}
    score_n = [i._score_names for i in gs]
    col_names = 'chr,pos,' + ",".join([x for x in score_n for x in x])

    k = 0
    for chrom, vls in sorted(gs[0]._Keys.items()):
        arr = []
        for v in vls:
            arr.append(np.arange(v[0], v[1]+1))
            Index[chrom][v] = (k, v[1] - v[0] +k)
            k += v[1] - v[0] + 1
        chr = np.array([chrom]*L[chrom], dtype='<a6')
        pos = np.hstack(arr)
        one_chr = [chr, pos]
        for i in gs:
            scores = i._score_names
            for s in scores:
                one_chr.append(i.Scores[s][chrom])
        D[chrom] = np.core.records.fromarrays(one_chr, names=col_names)

    to_concat = []
    for chr,arr in sorted(D.items()):
        to_concat.append(arr)

    A = OneArray()
    A.array = np.concatenate(to_concat)
    #A.create_index()
    A.index = Index
    return(A)

#!/bin/env python

# June 6th 2013
# by Ewa

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from builtins import next
from past.utils import old_div
from builtins import object
import sys, os

class GenomicSequence_Dan(object):
    
    _seq_dic = None
    genomicFile = None
    allChromosomes = None

    def createSeqDic(self, outputDir = "./", genome_location = None):
        # slightly modified Dan's script

        import numpy as np
        import os
        import pickle
        import gzip

        if genome_location == None:
            genome_location = "/data/unsafe/autism/genomes/hg19/per_chr_from_ucsc_20100831/"

        SeqDic = {}
        if os.path.isfile(genome_location) == True:
            # separate chromosomes!
            if genome_location.endswith(".fa.gz"):
                infile = gzip.open(genome_location, 'rb')
            elif genome_location.endswith(".fa"):
                infile = open(genome_location)
            else:
                print("Unrecognizible file format: " +  genome_location)
                sys.exit(-2)

            key = None
            while True:
                line = infile.readline().strip()
                if not line:
                    SeqDic[key] = full
                    print(key + " ..done!")
                    break
                if line[0] == ">":
                    if key != None:
                        SeqDic[key] = full
                        print(key + " ..done!")
                    key = line[1:]
                    full = ''
                else:
                    full += line.upper()
            infile.close()
                    
            
        elif os.path.isdir(genome_location) == True:
            for chromName in os.listdir(genome_location):
                if chromName.endswith(".fa.gz"):
                    key = chromName.split(".fa.gz")[0]
                    chromFile = os.path.join(genome_location, chromName)
                    infile = gzip.open(chromFile, 'rb')
                elif chromName.endswith(".fa"):
                    key = chromName.split(".fa")[0]
                    chromFile = os.path.join(genome_location, chromName)
                    infile = open(chromFile, 'r')
                else:
                    continue

                full = ""
                next(infile)
                for line in infile:
                    full += line.strip().upper()
                print(key + " ..done!")
                SeqDic[key] = full

                infile.close()

        else:
            print("the genome dir/file is incorrect or does not exist: " + genome_location)
            print("...exiting.......")
            sys.exit(-53)

        
        for key in SeqDic:
            print(key, len(SeqDic[key]))


        seq_pickle = outputDir + "seqDic_upper.dump"
        pickle.dump(SeqDic, open(seq_pickle, 'wb'), protocol=2)

    def __loadPickleSeq(self, file="/data/unsafe/autism/genomes/hg19/seqDic_upper.dump"):
        import pickle
        pkl_file = open(file, 'rb')
        self._seq_dic = pickle.load(pkl_file)
        pkl_file.close()
        
    def close(self):

        pass

    def _load_genome(self, file):
        
        self.genomicFile = file
        self.__loadPickleSeq(file)
        self.allChromosomes = list(self._seq_dic.keys())
        return(self)

    def get_chr_length(self, chrom):
        try:
            return(len(self._seq_dic[chrom]))
        except KeyError:
            print("Unknown chromosome!")

    def get_all_chr_lengths(self):
        R = []
        for chr in self._seq_dic:
            R.append((chr, len(self._seq_dic[chr])))
        return(R)
    
    def getSequence(self, chr, start, stop):

        return self._seq_dic[chr][start-1:stop]

        

class GenomicSequence_Ivan(object):

    genomicFile = None
    genomicIndexFile = None
    allChromosomes = None

    
    def __createIndexFile(self, file):

        from pysam import faidx

        faidx(file)


    def __chromNames(self):

        file = open(self.genomicIndexFile)

        Chr = []

        while True:
            line = file.readline()
            if not line:
                break
            line = line.split()
            Chr.append(line[0])

        file.close()

        self.allChromosomes = Chr

    def __initiate(self):
        self._Indexing = {}
        f = open(self.genomicIndexFile, 'r')
        while True:
            line = f.readline()
            if not line:
                break
            line = line.split()
            self._Indexing[line[0]] = {'length': int(line[1]), 'startBit': int(line[2]), 'seqLineLength': int(line[3]), 'lineLength': int(line[4])}
        f.close()

        self.__f = open(self.genomicFile, 'r')

    def close(self):

        self.__f.close()

    def _load_genome(self, file):

        if os.path.exists(file + ".fai") == False:
            self.__createIndexFile(file)

        self.genomicIndexFile = file + ".fai"
        self.genomicFile = file
        self.__chromNames()
        self.__initiate()

        return(self)

    def get_chr_length(self, chrom):

        try:
            return(self._Indexing[chrom]['length'])
        except KeyError:
            print("Unknown chromosome!")

    def get_all_chr_lengths(self):
        R = []
        for chr in self.allChromosomes:
            R.append((chr, self._Indexing[chr]['length']))
        return(R)
      
    def getSequence(self, chr, start, stop):
        
        if chr not in self.allChromosomes:
            print("Unknown chromosome!")
            return(-1)

        self.__f.seek(
            self._Indexing[chr]['startBit']+start-1+old_div((start-1),
            self._Indexing[chr]['seqLineLength']))

        l = stop-start+1
        x = 1 + old_div(l, self._Indexing[chr]['seqLineLength'])

        w = self.__f.read(l+x)
        w = w.replace("\n", "")[:l]

        return w.upper()


def openRef(file="/data/unsafe/autism/genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa"):

    if os.path.exists(file) == False:
        print("The input file: " + file + " does NOT exist!")
        sys.exit(-100)

    if file.endswith('.fa'):
        # ivan's method
        g_a = GenomicSequence_Ivan()
        return(g_a._load_genome(file))
        
    elif file.endswith('.dump'):
        # dan's method
        g_a = GenomicSequence_Dan()
        return(g_a._load_genome(file))

    else:
        print("Unrecognizable format of the file: " + file)
        sys.exit(-8)



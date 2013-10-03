#!/bin/env python

# June 6th 2013
# by Ewa

import sys

class GenomicSequence_Dan:
    
    seq_dic = None
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
                infile.next()
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
            print key, len(SeqDic[key])


        seq_pickle = outputDir + "seqDic_upper.dump"
        pickle.dump(SeqDic, open(seq_pickle, 'wb'))

    def loadPickleSeq(self, file="/data/unsafe/autism/genomes/hg19/seqDic_upper.dump"):
        import pickle
        pkl_file = open(file, 'rb')
        self.seq_dic = pickle.load(pkl_file)
        pkl_file.close()
        
    def close(self):

        pass
    
    def getSequence(self, chr, start, stop):

        return self.seq_dic[chr][start-1:stop]

        

class GenomicSequence_Ivan:

    genomicSeq = "/mnt/wigclust8/data/unsafe/autism/genomes/hg19/chrAll.fa"
    genomicIndexFile = "/mnt/wigclust8/data/unsafe/autism/genomes/hg19/chrAll.fa.fai"
    allChromosomes = None

    
    def createIndexFile(self, file=None):

        from pysam import faidx
        
        if file == None:
            file = self.genomicSeq

        faidx(file)


    def chromNames(self):

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

    def initiate(self):
        self.Indexing = {}
        f = open(self.genomicIndexFile, 'r')
        while True:
            line = f.readline()
            if not line:
                break
            line = line.split()
            self.Indexing[line[0]] = {'length': int(line[1]), 'startBit': int(line[2]), 'seqLineLength': int(line[3]), 'lineLength': int(line[4])}
        f.close()

        self.f = open(self.genomicSeq, 'r')

    def close(self):

        self.f.close()
        
        
 
    def getSequence(self, chr, start, stop):
        
        
        if chr not in self.allChromosomes:
            print("Unknown chromosome!")
            return(-1)

        self.f.seek(self.Indexing[chr]['startBit']+start-1+(start-1)/self.Indexing[chr]['seqLineLength'])
        
        l = stop-start+1
        x = 1 + l/self.Indexing[chr]['seqLineLength']
        
        w = self.f.read(l+x)
        w = w.replace("\n", "")[:l]
        
       
        return w.upper() 
        
    



def openRef(file="/mnt/wigclust8/data/unsafe/autism/genomes/hg19/chrAll.fa"):

    import os

    if os.path.exists(file) == False:
        print("The input file: " + file + " does NOT exist!")
        sys.exit(-100)
        

    if file.endswith('.fa'):
        # ivan's method
        g_a = GenomicSequence_Ivan()
        g_a.file_name = file
        g_a.genomicSeq = file

        if os.path.exists(file + ".fai") == False:
            g_a.createIndexFile()

        g_a.genomicIndexFile =  file + ".fai"
        g_a.chromNames()
        g_a.initiate()
        return(g_a)
        
    elif file.endswith('.dump'):
        # dan's method
        g_a = GenomicSequence_Dan()
        g_a.file_name = file
        g_a.loadPickleSeq(file)
        g_a.allChromosomes = g_a.seq_dic.keys()
        return(g_a)


    else:
        print("Unrecognizable format of the file: " + file)
        sys.exit(-8)



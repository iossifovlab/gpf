#!/bin/env python

# July 12th 2013
# written by Ewa

import gzip, pickle, os.path, os, sys, re
from subprocess import call
import shutil
from collections import namedtuple

                             
class AbstractClassDoNotInstantiate:
    # class with default parameters for RefSeq gene model - make these parameters default
    name = "refseq"
    location = "/data/unsafe/autism/genomes/hg19/geneModels/refGene.txt.gz"
    shift = 1
    DictNames = None
    dictFile = "/data/unsafe/autism/genomes/hg19/CodingSeq/RefSeq/"
    
class TranscriptModel:
   
    gene = None
    trID = None
    chr = None
    cds = []
    strand = None
    exons = []
    tx = []
    

    def is_coding(self):

       if self.cds[0] >= self.cds[1]:
            return False

       return True
            

    def CDS_regions(self, ss=0):

       
        if self.cds[0] >= self.cds[1]:
            return([])
        
        CDS_reg=namedtuple('CDS_reg', 'start stop chr')
        CDS_regions = []
        k=0
        while self.exons[k].stop < self.cds[0]:
            k+=1
            
        if self.cds[1] <=  self.exons[k].stop:
            CDS_regions.append(CDS_reg(chr=self.chr, start=self.cds[0], stop=self.cds[1]))
            return CDS_regions

        CDS_regions.append(CDS_reg(chr=self.chr, start=self.cds[0], stop=self.exons[k].stop + ss)) 
        k += 1
        while k < len(self.exons) and self.exons[k].stop <= self.cds[1]:
            if self.exons[k].stop < self.cds[1]:
                CDS_regions.append(CDS_reg(chr=self.chr, start=self.exons[k].start - ss, stop=self.exons[k].stop + ss))
                k += 1
            else:
                CDS_regions.append(CDS_reg(chr=self.chr, start=self.exons[k].start - ss, stop=self.exons[k].stop))
                return CDS_regions
            
        
        if k < len(self.exons) and self.exons[k].start <= self.cds[1]: 
            CDS_regions.append(CDS_reg(chr=self.chr, start=self.exons[k].start - ss, stop=self.cds[1]))

        
        return CDS_regions


    def UTR5_regions(self):

        

        if self.cds[0] >= self.cds[1]:
            return([])

        UTR5_reg=namedtuple('UTR5_reg', 'start stop chr')
        UTR5_regions = []
        k = 0
        if self.strand == "+":
            while self.exons[k].stop < self.cds[0]:
                UTR5_regions.append(UTR5_reg(chr=self.chr, start=self.exons[k].start, stop=self.exons[k].stop))
                k += 1
            if  self.exons[k].start < self.cds[0]:  
                UTR5_regions.append(UTR5_reg(chr=self.chr, start=self.exons[k].start, stop=self.cds[0]-1))

        else:
            while self.exons[k].stop < self.cds[1]:
                k += 1
            if self.exons[k].stop == self.cds[1]:
                k += 1
            else:
               UTR5_regions.append(UTR5_reg(chr=self.chr, start=self.cds[1]+1, stop=self.exons[k].stop))
               k += 1

            for e in self.exons[k:]:
                UTR5_regions.append(UTR5_reg(chr=self.chr, start=e.start, stop=e.stop))

        return UTR5_regions


    def UTR3_regions(self):

        if self.cds[0] >= self.cds[1]:
            return([])

        UTR3_reg = namedtuple('UTR3_reg', 'start stop chr')
        UTR3_regions = []
        k = 0
        if self.strand == "-":
            while self.exons[k].stop < self.cds[0]:
                UTR3_regions.append(UTR3_reg(chr=self.chr, start=self.exons[k].start, stop=self.exons[k].stop))
                k += 1
            if  self.exons[k].start < self.cds[0]:  
                UTR3_regions.append(UTR3_reg(chr=self.chr, start=self.exons[k].start, stop=self.cds[0]-1))

        else:
            while self.exons[k].stop < self.cds[1]:
                k += 1
            if self.exons[k].stop == self.cds[1]:
                k += 1
            else:
               UTR3_regions.append(UTR3_reg(chr=self.chr, start=self.cds[1]+1, stop=self.exons[k].stop))
               k += 1

            for e in self.exons[k:]:
                UTR3_regions.append(UTR3_reg(chr=self.chr, start=e.start, stop=e.stop))

        return UTR3_regions


    def all_regions(self, ss=0, prom=0):

        all_regions = []
        all_reg = namedtuple('all_reg', 'start stop chr')
        
        if ss == 0:
            for e in self.exons:
                all_regions.append(all_reg(chr=self.chr, start=e.start, stop=e.stop))
           

        else:
            for e in self.exons:
                if e.stop <= self.cds[0]:
                    all_regions.append(all_reg(chr=self.chr, start=e.start, stop=e.stop))
                elif e.start <= self.cds[0]:
                    if e.stop >= self.cds[1]:
                        all_regions.append(all_reg(chr=self.chr, start=e.start, stop=e.stop))
                    else:
                        all_regions.append(all_reg(chr=self.chr, start=e.start, stop=e.stop + ss))
                elif e.start > self.cds[1]:
                    all_regions.append(all_reg(chr=self.chr, start=e.start, stop=e.stop))
                else:
                    if e.stop >= self.cds[1]:
                        all_regions.append(all_reg(chr=self.chr, start=e.start-ss, stop=e.stop))
                    else:
                        all_regions.append(all_reg(chr=self.chr, start=e.start-ss, stop=e.stop+ss))


        if prom != 0:
            if self.strand == "+":
                all_regions[0] = all_reg(chr=all_regions[0].chr, start = all_regions[0].start - prom, stop = all_regions[0].stop)
            else:
                all_regions[-1] = all_reg(chr=all_regions[-1].chr, start = all_regions[-1].start, stop = all_regions[-1].stop + prom)

        return all_regions
           
        

    def total_len(self):

        length = 0
        for e in self.exons:
            length += e.stop - e.start + 1
        return length
    

    def CDS_len(self):

        cds_region = self.CDS_regions()
        
        length = 0
        for c in cds_region:
            length += c[1] - c[0] + 1
        return(length)


    def UTR3_len(self):

        utr3 = self.UTR3_regions()

        l = 0

        for i in utr3:
            l += i[1] - i[0] + 1

        return l


    def UTR5_len(self):

       utr5 = self.UTR5_regions()

       l = 0

       for i in utr5:
           l += i[1] - i[0] + 1
           
       return l



    def __check_if_exon(self, pos_start, pos_stop):

        for e in self.exons:
          
            if e.start > pos_stop:
                return(False)
            if (e.start <= pos_start <= e.stop) or (pos_start < e.start and pos_stop >= e.start):
                return True
        return False
       

    def what_region(self, chr, pos_start, pos_stop, prom = 0):

        
        if pos_stop < self.exons[0].start:
            if prom == 0:
                return("no_hit")
            if self.strand == "+" and pos_stop >= self.exons[0].start - prom:
                return("promoter")
            return("no_hit")

        if pos_start > self.exons[-1].stop:
            if prom == 0:
                return("no_hit")
            if self.strand == "-" and pos_start <= self.exons[-1].stop + prom:
                return("promoter")
            return("no_hit")

        if pos_stop < self.cds[0]:
            if self.__check_if_exon(pos_start, pos_stop) == True:
                if self.strand == "+":
                    return("5'utr")
                return("3'utr")
            
            if self.strand == "+":
                return("5'UTR-intron")
            return("3'UTR-intron")

        if pos_start > self.cds[1]:
            if self.__check_if_exon(pos_start, pos_stop) == True:
                if self.strand == "+":
                    return("3'utr")
                return("5'utr")
          
            if self.strand == "+":
                return("3'UTR-intron")
            return("5'UTR-intron")
        
        if pos_start <= self.exons[0].start and pos_stop >= self.exons[-1].stop :
            return("all")
        
        if self.__check_if_exon(pos_start, pos_stop) == True:
            return("CDS")

        if self.chr != chr:
            return("no_hit")

        
        return("intronic")

       


    
    
class Exon:
   
    start = None
    stop = None
    frame = None
   

class GeneModels(AbstractClassDoNotInstantiate):
    # uses RefSeq parameters
    # provides methods for RefSeq, KnownGene, Ccds classes

    utrModels = {}
    transcriptModels = {}
    geneModels = {}

   

    def __addToDict(self, line):

        
        chrom = line[1 + self.shift]

    
        if self.name != "knowngene":
            if self.name == "refseq":
                gene = line[12]
                trName = line[1] + "_1"
               
            else:
                try:
                    gene = self.DictNames[line[1]]
                except:
                    gene = line[1]
                trName = line[1]  + "_1"
               
                    
            Frame = map(int, line[-1].split(',')[:-1])
                
           
        else:
            try:
                gene = self.DictNames[line[0]]
            except:
                gene = line[0]
            trName = line[0] + "_1"
           

        k = 1
        while True:
            try:
                self.transcriptModels[trName]
                k += 1
                trName = line[1] + "_" + str(k)
            except:
                break
        
            
        strand = line[2 + self.shift]
        transcription_start = int(line[3 + self.shift])
        transcription_end = line[4 + self.shift]
        cds_start = line[5 + self.shift]
        cds_end = line[6 + self.shift]
        exon_starts = line[8 + self.shift].split(',')[:-1]
        exon_ends = line[9 + self.shift].split(',')[:-1]

        l = len(exon_starts)        
                
        exons = []
            
        if self.name != "knowngene":
               
            for i in xrange(0, l):
                ex = Exon()
                ex.start = int(exon_starts[i])+1
                ex.stop = int(exon_ends[i])
                ex.frame = int(Frame[i])
                ex.seq = None
                exons.append(ex)

        else:
           
            
            Frame = []
            if int(cds_start) >= int(cds_end):
                for e in xrange(0, l):
                    Frame.append(-1)
            
            elif strand == "+":
                k = 0
                while int(exon_ends[k]) < int(cds_start):
                    Frame.append(-1)
                    k+=1
                Frame.append(0)
                if int(cds_end) > int(exon_ends[k]):
                    Frame.append((int(exon_ends[k]) - int(cds_start))%3) ###
                if int(cds_end) <= int(exon_ends[k]):
                    for e in exon_ends[k+1:]:
                        Frame.append(-1)
                else:
                    k+=1
                    while k < l and int(exon_ends[k]) < int(cds_end):
                        Frame.append((Frame[k] + int(exon_ends[k]) - int(exon_starts[k]))%3)
                        k += 1
                    k += 1
                    for e in exon_ends[k:]:
                        Frame.append(-1)

            else:
                k = len(exon_ends)-1
                while int(exon_starts[k]) > int(cds_end):
                    Frame.append(-1)
                    k-=1
                Frame.append(0)
                if int(cds_start) < int(exon_starts[k]):
                    Frame.append((int(cds_end) - int(exon_starts[k]))%3)
                if  int(cds_start) >= int(exon_starts[k]):
                    for e in exon_ends[:k]:
                        Frame.append(-1)
                else:
                    k-=1
                    while k > -1 and int(exon_starts[k]) > int(cds_start):
                        Frame.append((Frame[-1] + int(exon_ends[k]) - int(exon_starts[k]))%3)
                        k -= 1
                    k-=1
                    for e in exon_ends[:k+1]:
                        Frame.append(-1)
                    Frame = Frame[::-1]

  
            for i in xrange(0, l):
                ex = Exon()
                ex.start = int(exon_starts[i])+1
                ex.stop = int(exon_ends[i])
                ex.frame = Frame[i]
                exons.append(ex)
            
                
                  

        tm = TranscriptModel() 
        tm.gene = gene
        tm.trID = trName
        tm.chr = chrom
        tm.strand = strand
        tm.tx = (transcription_start + 1, int(transcription_end))
        tm.cds = (int(cds_start)+1, int(cds_end))
        tm.exons= exons

       

        self.transcriptModels[tm.trID] = tm

        try:
            self.geneModels[gene].append(tm)
        except:
            self.geneModels[gene] = [tm]

        try:
            self.utrModels[chrom][(transcription_start + 1, int(transcription_end))].append(tm)
        except KeyError as e:
            if e.args[0] == chrom:
                self.utrModels[chrom] = {}
            self.utrModels[chrom][(transcription_start + 1, int(transcription_end))] = [tm]

        return(-1)
                

                        

    
    def create_gene_model_dict(self, location=None):

       

        if location == None:
            location = self.location


        geneModelFile = gzip.open(location, 'rb')
        
        while True:
        
            line = geneModelFile.readline()
            if not line:
                break
            if line[0] == "#":
                continue
            line = line.split()
            chrom = line[1 + self.shift]
            
            
            self.__addToDict(line)
            
        geneModelFile.close()
       


    def writeCdsToFile(self, fileDir="./"):

        if os.path.exists(fileDir) == False:
            os.makedirs(fileDir)

        for key in self.utrModels.keys():
            outFile = open(fileDir + "/cds_" + key + ".txt", 'w')
            self.__writeSmallDictToFile(self.utrModels[key], outFile)
            outFile.close()
            

    def loadDictFromFile(self, fileDir=None):

        if fileDir == None:
            fileDir = self.dictFile

        D = {}
        allFiles = os.listdir(fileDir)
        for file in allFiles:
            f = open(fileDir + file, 'r')
            line = f.readline()
            line = line.split()
            chr = line[1]
            vars()[chr] = {}
        
            while True:
                if not line:
                    break


                tm = TranscriptModel()
                Exons = []
                
                tm.chr = chr
                tm.gene = line[0][1:]
                tm.strand = line[2]
                
                utr_start = int(line[3])
                utr_end = int(line[4])
                tm.tx = (utr_start, utr_end)
                
                line = f.readline()
                line = line.split()
                linesWithData = []
                while line[0][0] != ">":
                    ex = Exon()
                    ex.start = int(line[0])
                    ex.stop = int(line[1])
                    ex.frame = line[2]
                    ex.seq = line[3]
                    Exons.append(ex)
                    line[0] = int(line[0])
                    line[1] = int(line[1])
                    linesWithData.append((line))
                    line = f.readline()
                    if not line:
                        break
                    line = line.split()

                
                tm.exons = Exons
                try:
                   vars()[chr][(utr_start, utr_end)].append(tm)
                except:
                   vars()[chr][(utr_start, utr_end)]=[tm]

            D[chr] = vars()[chr]
            f.close()
        
        return D

    def save_dicts(self, outputFile = "./geneModels.dump"):
        import pickle
    
        pickle.dump([self.utrModels, self.transcriptModels, self.geneModels], open(outputFile, 'wb'))

   
    def load_dicts(self, inputFile):
    
        import pickle
        pkl_file = open(inputFile, 'rb')
        Object = pickle.load(pkl_file)
        pkl_file.close()
        self.utrModels = Object[0]
        self.transcriptModels = Object[1]
        self.geneModels = Object[2]


    def gene_names(self):
        
        if self.geneModels == None:
            print("Gene Models haven't been created/uploaded yet! Use either loadGeneModels function or self.createGeneModelDict function")
            return(None)
        
        return self.geneModels.keys()


    def transcript_IDs(self):
        
        if self.transcriptModels == None:
            print("Gene Models haven't been created/uploaded yet! Use either loadGeneModels function or self.createGeneModelDict function")
            return(None)

        return(self.transcriptModels.keys()) 


    def gene_models_by_gene_name(self, name):

        try:
            return(self.geneModels[name])
        except:
            pass


    def gene_models_by_location(self, chr, pos1, pos2 = None):

        R = []

        chr = str(chr)
        if chr.startswith('chr') == False:
            chr = "chr" + chr

        if pos2 == None:
            for key in self.utrModels[chr]:
                if pos1 >= key[0] and pos1 <= key[1]:
                    R.extend(self.utrModels[chr][key])

        else:
            if pos2 < pos1:
                pos1, pos2 = pos2, pos1
                
            for key in self.utrModels[chr]:
                if (pos1 <= key[0] and pos2 >= key[0]) or (pos1 >= key[0] and pos1 <= key[1]):
                    R.extend(self.utrModels[chr][key])

        return(R)


    def relabel_chromosomes(self):
        
        if self.transcriptModels == None:
            print("Gene Models haven't been created/uploaded yet! Use either loadGeneModels function or self.createGeneModelDict function")
            return(None)

        Relabel={}
        for tm in self.utrModels.keys():
            if "gl" in tm:
                old_name = re.match('.*_(gl[0-9]*)', tm)
                new_name = old_name.group(1).upper() + ".1"
                Relabel[tm] = new_name
            else:
                new_name = tm[3:]
                Relabel[tm] = new_name
            

            self.utrModels[new_name] = self.utrModels[tm]

        
        for tm in self.transcriptModels:   
            self.transcriptModels[tm].chr = Relabel[self.transcriptModels[tm].chr]

  
   

class RefSeq(GeneModels):
    
    name = "refseq"
    location = "/data/unsafe/autism/genomes/hg19/geneModels/refGene.txt.gz"
    shift = 1
    DictNames = None
    dictFile = "/data/unsafe/autism/genomes/hg19/CodingSeq/RefSeq/"
    
    

class KnownGene(GeneModels):

    
    name="knowngene"
    location = "/data/unsafe/autism/genomes/hg19/geneModels/knownGene.txt.gz"
    shift = 0
    dictFile = "/data/unsafe/autism/genomes/hg19/CodingSeq/KnownGene/"
    
    DictNames={}
    dict_file = gzip.open("/data/unsafe/autism/genomes/hg19/geneModels/kgId2Sym.txt.gz")
    dict_file.readline()
    while True:
        line = dict_file.readline()
        if not line:
            break
        line = line.split()
        DictNames[line[0]] = line[1]
    dict_file.close()
        
        
        
class Ccds(GeneModels):

    name="ccds"
    location = "/data/unsafe/autism/genomes/hg19/geneModels/ccdsGene.txt.gz"
    shift = 1
    dictFile = "/data/unsafe/autism/genomes/hg19/CodingSeq/Ccds/"

   
    DictNames={}
    dict_file = gzip.open("/data/unsafe/autism/genomes/hg19/geneModels/ccdsId2Sym.txt.gz")
    dict_file.readline()
    while True:
        line = dict_file.readline()
        if not line:
            break
        line = line.split()
        DictNames[line[0]] = line[1]
    dict_file.close()
       


def create_region(chrom, b, e):
    reg = namedtuple('reg', 'start stop chr')
    
    return(reg(chr=chrom, start=b, stop=e))



def load_gene_models(file_name="/data/unsafe/autism/genomes/hg19/geneModels/refGene.txt.gz"):

    if file_name.endswith("refGene.txt.gz"):
        gm = RefSeq()
        
        gm.utrModels = {}
        gm.transcriptModels = {}
        gm.geneModels = {}
    
        gm.location = file_name
        gm.create_gene_model_dict()
        
    elif file_name.endswith("ccdsGene.txt.gz"):
        gm = Ccds()

        gm.utrModels = {}
        gm.transcriptModels = {}
        gm.geneModels = {}
        
        gm.location = file_name
        gm.create_gene_model_dict()
        
        

    elif file_name.endswith("knownGene.txt.gz"):
        gm = KnownGene()

        gm.utrModels = {}
        gm.transcriptModels = {}
        gm.geneModels = {}
        
        gm.location = file_name
        gm.create_gene_model_dict()
        

    elif file_name.endswith(".dump"):
        gm = GeneModels()
        gm.loadDicts(file_name)
        
    else:
        print("Unrecognizable file: " + file_name)
        print("File name must be one of: refGene.txt.gz, ccdsGene.txt.gz, knownGene.txt.gz or .dump file")
        sys.exit(-46)
        
    return gm


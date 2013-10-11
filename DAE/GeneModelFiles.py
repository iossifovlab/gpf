#!/bin/env python

# July 12th 2013
# written by Ewa

import gzip, pickle, os.path, os, sys, re
from subprocess import call
import shutil
from collections import namedtuple

                             
class AbstractClassDoNotInstantiate:
    
    name = None
    location = None
    _shift = None 
    Alternative_names = None
    
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
    
    utrModels = {}
    transcriptModels = {}
    geneModels = {}
    Alternative_names = None
   

    def __addToDict(self, line):
        
        chrom = line[1 + self._shift]
    
        if self.name != "knowngene":
            if self.name == "refseq":
                try:
                    gene = self.Alternative_names[line[12]]
                except:
                    gene = line[12]
                trName = line[1] + "_1"
               
            else:
                try:
                    gene = self.Alternative_names[line[1]]
                except:
                    gene = line[1]
                trName = line[1]  + "_1"
               
                    
            Frame = map(int, line[-1].split(',')[:-1])
                
           
        else:
            try:
                gene = self.Alternative_names[line[0]]
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
        
            
        strand = line[2 + self._shift]
        transcription_start = int(line[3 + self._shift])
        transcription_end = line[4 + self._shift]
        cds_start = line[5 + self._shift]
        cds_end = line[6 + self._shift]
        exon_starts = line[8 + self._shift].split(',')[:-1]
        exon_ends = line[9 + self._shift].split(',')[:-1]

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
                
    
    def _create_gene_model_dict(self, location=None, gene_mapping_file = None):

        self.Alternative_names={}
        if gene_mapping_file != None:
            if gene_mapping_file.endswith(".gz"):
                dict_file = gzip.open(gene_mapping_file)
            else:
                dict_file = open(gene_mapping_file)
            dict_file.readline()
            self.Alternative_names = dict([(line.split()[0],line.split()[1]) for line in dict_file])
            dict_file.close()
       
        if location == None:
            location = self.location

        geneModelFile = gzip.open(location, 'rb')
        
        
        for line in geneModelFile:
            if line[0] == "#":
                continue
            line = line.split()
            chrom = line[1 + self._shift]
           
            self.__addToDict(line)
            
        geneModelFile.close()



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


    def relabel_chromosomes(self, file="/data/unsafe/autism/genomes/hg19/ucsc2gatk.txt"):
        
        if self.transcriptModels == None:
            print("Gene Models haven't been created/uploaded yet! Use either loadGeneModels function or self.createGeneModelDict function")
            return(None)

        f = open(file)
        Relabel = dict([(line.split()[0], line.split()[1]) for line in f])
        
        for chrom in self.utrModels.keys():

            try:
                self.utrModels[Relabel[chrom]] = self.utrModels[chrom]
                self.utrModels.pop(chrom)
            except KeyError:
                pass

        
        for trID in self.transcriptModels:
            try:
                self.transcriptModels[trID].chr = Relabel[self.transcriptModels[trID].chr]
            except KeyError:
                pass
  
   

class RefSeq(GeneModels):
    
    name = "refseq"
    location = "/data/unsafe/autism/genomes/hg19/geneModels/refGene.txt.gz"
    _shift = 1
    Alternative_names = None    

class KnownGene(GeneModels):

    
    name="knowngene"
    location = "/data/unsafe/autism/genomes/hg19/geneModels/knownGene.txt.gz"
    _shift = 0
    Alternative_names = None       
        
class Ccds(GeneModels):

    name="ccds"
    location = "/data/unsafe/autism/genomes/hg19/geneModels/ccdsGene.txt.gz"
    _shift = 1
    Alternative_names = None

class MitoModel(GeneModels):

    name = "mitomap"
    location = "/data/unsafe/autism/genomes/hg19/geneModels/mitomap.txt"
    Alternative_names = None

    def _create_gene_model_dict(self, file_name):

        self.utrModels['chrM'] = {}
        if file_name == None:
            file = open(self.location)
        else:
            file = open(file_name)

        for line in file:
            line = line.split()
            if line[0] == "#":
                mode = line[1]
                continue
            if mode == "cds":
                mm = TranscriptModel()
                mm.gene = mm.trID = line[0]
                mm.strand = line[1]
                mm.cds = (int(line[2]), int(line[3]))
                mm.tx = (int(line[2]), int(line[3]))
                mm.chr = "chrM"
                e = Exon()
                e.start = int(line[2])
                e.stop = int(line[3])
                e.frame = 0
                mm.exons = [e]
                self.utrModels['chrM'][mm.tx] = [mm]
                self.transcriptModels[mm.trID] = mm
                self.geneModels[mm.gene] = [mm]

            elif mode == "rRNAs":
                mm = TranscriptModel()
                mm.gene = mm.trID = line[0]
                mm.strand = line[1]
                mm.cds = (int(line[2]), int(line[2]))
                mm.tx = (int(line[2]), int(line[3]))
                mm.chr = "chrM"
                e = Exon()
                e.start = int(line[2])
                e.stop = int(line[3])
                mm.exons = [e]
                self.utrModels['chrM'][mm.tx] = [mm]
                self.transcriptModels[mm.trID] = mm
                self.geneModels[mm.gene] = [mm]

            elif mode == "tRNAs":
                mm = TranscriptModel()
                mm.chr = "chrM"
                mm.gene = mm.trID = line[0]
                mm.strand = line[1]
                mm.cds = (int(line[2]), int(line[2]))
                mm.tx = (int(line[2]), int(line[3]))
                mm.anticodon = (int(line[4]), int(line[5]))
                e = Exon()
                e.start = int(line[2])
                e.stop = int(line[3])
                mm.exons = [e]
                self.utrModels['chrM'][mm.tx] = [mm]
                self.transcriptModels[mm.trID] = mm
                self.geneModels[mm.gene] = [mm]
                
            elif mode == "regulatory_elements":
                mm = TranscriptModel()
                mm.chr = "chrM"
                mm.gene = line[0]
                mm.cds = (int(line[2]), int(line[2]))
                mm.tx = (int(line[1]), int(line[2]))
                e = Exon()
                e.start = int(line[1])
                e.stop = int(line[2])
                mm.exons = [e]
                self.utrModels['chrM'][mm.tx] = [mm]

            else:
                continue
        file.close()


    
    

def save_dicts(gm, outputFile = "./geneModels.dump"):
    import pickle
    pickle.dump([gm.utrModels, gm.transcriptModels, gm.geneModels], open(outputFile, 'wb'))


def load_pickled_dicts(inputFile):
    
    import pickle
    gm = GeneModels()
    pkl_file = open(inputFile, 'rb')
    Object = pickle.load(pkl_file)
    pkl_file.close()

    gm.utrModels = Object[0]
    gm.transcriptModels = Object[1]
    gm.geneModels = Object[2]
    return(gm)

def create_region(chrom, b, e):
    reg = namedtuple('reg', 'start stop chr')
    
    return(reg(chr=chrom, start=b, stop=e))



def load_gene_models(file_name="/data/unsafe/autism/genomes/hg19/geneModels/refGene.txt.gz", gene_mapping_file="default", format=None):

    if format != None:


        if format.lower() == "refseq":
            gm = RefSeq()  
            gm.utrModels = {}
            gm.transcriptModels = {}
            gm.geneModels = {}
            if gene_mapping_file == "default":
                gene_mapping_file = None
            gm.location = file_name
            gm._create_gene_model_dict(file_name, gene_mapping_file)
        elif format.lower() == "ccds":
            gm = Ccds()
            gm.utrModels = {}
            gm.transcriptModels = {}
            gm.geneModels = {}
            if gene_mapping_file == "default":
                gene_mapping_file = os.path.dirname(file_name) + "/ccdsId2Sym.txt.gz"
            gm.location = file_name
            gm._create_gene_model_dict(file_name, gene_mapping_file)
        elif format.lower() == "knowngene":
            gm = KnownGene()
            gm.utrModels = {}
            gm.transcriptModels = {}
            gm.geneModels = {}
            if gene_mapping_file == "default":
                gene_mapping_file = os.path.dirname(file_name) + "/kgId2Sym.txt.gz"    
            gm.location = file_name
            gm._create_gene_model_dict(file_name, gene_mapping_file)
        else:
            print("Unrecognizable format! Choose between: 'refseq', 'ccds' and 'knowngene'")
            sys.exit(-1098)

        return gm



    if file_name.endswith("refGene.txt.gz"):
        gm = RefSeq()
        
        gm.utrModels = {}
        gm.transcriptModels = {}
        gm.geneModels = {}

        if gene_mapping_file == "default":
            gene_mapping_file = None

    
        gm.location = file_name
        gm._create_gene_model_dict(file_name, gene_mapping_file)
        
    elif file_name.endswith("ccdsGene.txt.gz"):
        gm = Ccds()

        gm.utrModels = {}
        gm.transcriptModels = {}
        gm.geneModels = {}
        if gene_mapping_file == "default":
            gene_mapping_file = os.path.dirname(file_name) + "/ccdsId2Sym.txt.gz"
        gm.location = file_name
        gm._create_gene_model_dict(file_name, gene_mapping_file)
        
        

    elif file_name.endswith("knownGene.txt.gz"):
        gm = KnownGene()
        gm.utrModels = {}
        gm.transcriptModels = {}
        gm.geneModels = {}

        if gene_mapping_file == "default":
            gene_mapping_file = os.path.dirname(file_name) + "/kgId2Sym.txt.gz"        
        gm.location = file_name
        gm._create_gene_model_dict(file_name, gene_mapping_file)
        

    elif file_name.endswith(".dump"):
        gm = GeneModels()
        
        if gene_mapping_file == "default":
             gene_mapping_file = None
             
        gm.loadDicts(file_name)

    elif file_name.endswith("mitomap.txt"):
        gm = MitoModel()
        gm._create_gene_model_dict(file_name)
        
        
    else:
        print("Unrecognizable file: " + file_name)
        print("File name must be one of: refGene.txt.gz, ccdsGene.txt.gz, knownGene.txt.gz or .dump file")
        sys.exit(-46)
        
    return gm


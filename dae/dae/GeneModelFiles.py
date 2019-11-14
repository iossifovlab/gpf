#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals

from builtins import zip
from builtins import map
from builtins import str
from builtins import range
from builtins import object
from RegionOperations import Region, \
    collapse_noChr
import gzip
import pickle
import sys
from collections import defaultdict, \
    namedtuple, OrderedDict

import os

NumOfLine2Read4Test = 100

#
# Exon
#
class Exon:
  def __init__( self, start=None, stop=None, frame=None, number=None, cds_start=None, cds_stop=None ):
    self.start     = start
    self.stop      = stop
    self.frame     = frame # related to cds

    # for GTF 
    self.number    = number # exon number
    self.cds_start = cds_start # 
    self.cds_stop  = cds_stop

class TranscriptModel:
    def __init__( self ):
        self.attr = {}
        self.gene = None
        self.trID = None
        self.chr = None
        self.cds = []
        self.strand = None
        self.exons = []
        self.tx = []

        #for GTF
        self.utrs = []
        self.start_codon = None
        self.stop_codon  = None

        self._is_coding = False #it can be derivable from cds' start and end

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

    def calc_frames(tm):
        l = len(tm.exons)
        fms = []

        if tm.cds[0] > tm.cds[1]:
            fms = [-1] * l
        elif tm.strand == "+":
            k = 0
            while tm.exons[k].stop < tm.cds[0]:
                fms.append(-1)
                k += 1
            fms.append(0)
            if tm.exons[k].stop < tm.cds[1]:
                fms.append((tm.exons[k].stop - tm.cds[0] + 1) % 3)
                k += 1
            while tm.exons[k].stop < tm.cds[1] and k < l:
                fms.append((fms[k] + tm.exons[k].stop - tm.exons[k].start + 1) % 3)
                k += 1
            fms += [-1] * (l - len(fms))
        else:
            k = l-1
            while tm.exons[k].start > tm.cds[1]:
                fms.append(-1)
                k -= 1
            fms.append(0)
            if tm.cds[0] < tm.exons[k].start:
                fms.append((tm.cds[1] - tm.exons[k].start + 1 ) % 3)
                k -= 1
            while tm.cds[0] < tm.exons[k].start and k > -1:
                fms.append((fms[-1] + tm.exons[k].stop - tm.exons[k].start + 1) % 3)
                k -= 1
            fms += [-1] * (l - len(fms))
            fms = fms[::-1]

        assert len(tm.exons) == len(fms)
        return fms

    def update_frames(tm):
        fms = tm.calc_frames()
        for e,f in zip(tm.exons,fms):
            e.frame = f
            
    def test_frames(tm,update=False):
        fms = tm.calc_frames()
        for e,f in zip(tm.exons,fms):
            if e.frame != f:
                return False
        return True

# column names that expected to have on certain formats
# in order
Columns4FileFormat = { \
    'commonGTF':'seqname,source,feature,start,end,score,strand,phase,attributes,comments'.split(','),
    'commonDefault':'chr,trID,gene,strand,tsBeg,txEnd,cdsStart,cdsEnd,exonStarts,exonEnds,exonFrames,atts'.split(','),
    'commonGenePredUCSC':'name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,exonStarts,exonEnds'.split(','),
    'ucscGenePred':'name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,exonCount,exonStarts,exonEnds'.split(','),
    'refSeq':'bin,name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,exonCount,exonStarts,exonEnds,score,name2,cdsStartStat,cdsEndStat,exonFrames'.split(','),
    'refFlat':'geneName,name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,exonCount,exonStarts,exonEnds'.split(','),
    'knownGene':'name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,exonCount,exonStarts,exonEnds,proteinID,alignID'.split(','),
    'ccds':'bin,name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,exonCount,exonStarts,exonEnds,score,name2,cdsStartStat,cdsEndStat,exonFrames'.split(',') }


#
# GeneModel's database
#
class GeneModelDB:
  def __init__( self ):
    self.name = None
    self.location = None
    self._shift = None
    self._Alternative_names = None

    self._utrModels = {}
    self.transcriptModels = {}
    self._geneModels = {}

  #from orgininal without editing
  def addModelToDict(self, tm):

      assert tm.trID not in self.transcriptModels

      self.transcriptModels[tm.trID] = tm

      try:
          self._geneModels[tm.gene].append(tm)
      except:
          self._geneModels[tm.gene] = [tm]

      try:
          self._utrModels[tm.chr][tm.tx].append(tm)
      except KeyError as e:
          if e.args[0] == tm.chr:
              self._utrModels[tm.chr] = {}
          self._utrModels[tm.chr][tm.tx] = [tm]

      return(-1)

  def _updateIndexes(self):
      self._geneModels = defaultdict(list)
      self._utrModels = defaultdict(lambda : defaultdict(list))
      for tm in self.transcriptModels.values():
          self._geneModels[tm.gene].append(tm)
          self._utrModels[tm.chr][tm.tx].append(tm) 

  def gene_names(self):
      if self._geneModels == None:
          print("Gene Models haven't been created/uploaded yet! Use either loadGeneModels function or self.createGeneModelDict function")
          return(None)
      
      return self._geneModels.keys()

  def gene_models_by_gene_name(self, name):
      try:
          return(self._geneModels[name])
      except:
          pass

  def gene_models_by_location(self, chr, pos1, pos2 = None):
      R = []

      
      if pos2 == None:
          for key in self._utrModels[chr]:
              if pos1 >= key[0] and pos1 <= key[1]:
                  R.extend(self._utrModels[chr][key])

      else:
          if pos2 < pos1:
              pos1, pos2 = pos2, pos1
              
          for key in self._utrModels[chr]:
              if (pos1 <= key[0] and pos2 >= key[0]) or (pos1 >= key[0] and pos1 <= key[1]):
                  R.extend(self._utrModels[chr][key])

      return(R)

  def relabel_chromosomes_chr(self,Relabel):
      
      if self.transcriptModels == None:
          print("Gene Models haven't been created/uploaded yet! Use either loadGeneModels function or self.createGeneModelDict function")
          return(None)

      
      for chrom in self._utrModels.keys():

          try:
              self._utrModels[Relabel[chrom]] = self._utrModels[chrom]
              self._utrModels.pop(chrom)
          except KeyError:
              pass

      
      for trID in self.transcriptModels:
          try:
              self.transcriptModels[trID].chr = Relabel[self.transcriptModels[trID].chr]
          except KeyError:
              pass

  def relabel_chromosomes(self, file="ucsc2gatk.txt"):
      
      if self.transcriptModels == None:
          print("Gene Models haven't been created/uploaded yet! Use either loadGeneModels function or self.createGeneModelDict function")
          return(None)

      f = open(file)
      Relabel = dict([(line.split()[0], line.split()[1]) for line in f])
      
      for chrom in self._utrModels.keys():

          try:
              self._utrModels[Relabel[chrom]] = self._utrModels[chrom]
              self._utrModels.pop(chrom)
          except KeyError:
              pass

      
      for trID in self.transcriptModels:
          try:
              self.transcriptModels[trID].chr = Relabel[self.transcriptModels[trID].chr]
          except KeyError:
              pass

  def save(self, outputFile, gzipped=True):
        if gzipped:
            f = gzip.open(outputFile + ".gz", 'wt')
        else:
            f = open(outputFile, 'wt')

        f.write("\t".join(
            "chr trID gene strand tsBeg txEnd cdsStart cdsEnd "
            "exonStarts exonEnds exonFrames atts".split())+"\n")

        for tmId, tm in sorted(self.transcriptModels.items()):
            eStarts = ",".join([str(e.start) for e in tm.exons])
            eEnds = ",".join([str(e.stop) for e in tm.exons])
            eFrames = ",".join([str(e.frame) for e in tm.exons])

            add_atts = ";".join(
                [k+":"+str(v) for k, v in list(tm.attr.items())])

            cs = [
                tm.chr,
                tm.trID,
                tm.gene,
                tm.strand,
                tm.tx[0],
                tm.tx[1],
                tm.cds[0],
                tm.cds[1],
                eStarts,
                eEnds,
                eFrames,
                add_atts,
            ]
            f.write("\t".join([
                str(x) if x is not None else "" for x in cs]) + "\n")
        f.close()

def openFile( fileName ):
    if fileName.endswith('.gz') or fileName.endswith('.bgz'):
        inF = gzip.open( fileName, 'rt' )
    else:
        inF = open( fileName )

    return inF
  
class GtfFileReader:
   colNames = 'seqname,source,feature,start,end,score,strand,phase,attributes,comments'.split(',')

   @staticmethod
   def gtfParseAttr( stx ):
    atx = {}
    for x in stx.split('; '):
        #print x, x.split(' ')
        n,d = x.split(' ')
        if d.startswith('"') and d.endswith('"'):
          d = d[1:-1]

        atx[n] = d
    #print atx
    return atx

   @staticmethod
   def gtfParseStr( line ):
        terms = line.strip('\n').split('\t')
        rx = { h:d for h,d in zip(GtfFileReader.colNames,terms) }

        rx['start'] = int(rx['start'])
        rx['end'] = int(rx['end'])
        rx['attributes'] = GtfFileReader.gtfParseAttr( rx['attributes'] )

        return rx

   def __init__( cls, fileName ):
        cls.colIndex = { cls.colNames[n]:n for n in range(len(cls.colNames)) }

        cls._file = None
        try:
           cls._file = openFile( fileName )
        except IOError as e:
                print( e )
                return

   def __iter__( cls ):
        return cls

   def __next__( cls ):
        line = cls._file.readline()
        while line and (line[0] == '#'):
           line = cls._file.readline()

        if line == '':
                raise StopIteration

        return GtfFileReader.gtfParseStr( line ) #rx

   #TODO: delete after migrate to python3
   #make code compatible to python2
   def next( cls ):
        line = cls._file.readline()
        while line and (line[0] == '#'):
           line = cls._file.readline()

        if line == '':
                raise StopIteration

        return GtfFileReader.gtfParseStr( line ) #rx

class defaultFileReader:
   dftHead = Columns4FileFormat['commonDefault']

   def __init__(self, line ):
     self.hDict = {h:n for n,h in enumerate(line.strip('\n').split('\t'))}
     try:
        self.index = [ self.hDict[h] for h in self.dftHead ]
     except KeyError as e:
        self.index = [n for n in range(len(self.dftHead))]

   def read( self, line ):
     terms = line.strip('\n').split('\t')
     return [terms[n] for n in self.index]

def defaultGeneModelParser(self, file_name, gene_mapping_file=None,testMode=False):  
      self.location = file_name

      f = openFile(file_name)

      l = f.readline()
      lineR = defaultFileReader(l)
      for nLR, l in enumerate(f):
          if testMode and nLR > NumOfLine2Read4Test:
                f.close()
                return True

          cs = lineR.read(l)  #l[:-1].split('\t')
          chr, trID, gene, strand, txB, txE, cdsB, cdsE, eStarts, eEnds, eFrames, add_attrs = cs
          
          exons = [] 
          for frm,sr,sp in zip(*map(lambda x: x.split(","), [eFrames, eStarts, eEnds])):
              e = Exon()
              e.frame = int(frm)
              e.start = int(sr)
              e.stop = int(sp)
              exons.append(e)

          if add_attrs: 
            attrs = dict([a.split(":") for a in add_attrs.split(";")])
          else:
            attrs = {}

          tm = TranscriptModel() 
          tm.gene = gene
          tm.trID = trID
          tm.chr = chr 
          tm.strand = strand
          tm.tx = (int(txB), int(txE))
          tm.cds = (int(cdsB), int(cdsE))
          tm.exons  = exons
          tm.attr = attrs

          self.transcriptModels[tm.trID] = tm

      f.close()
      self._updateIndexes()

      if testMode: return True

def pickledGeneModelParser( self, file_name, gene_mapping_file=None, testMode=False ):
    import pickle
 
    self.location = file_name
    pkl_file = open(file_name, 'rb')
    self._utrModels, self.transcriptModels, self._geneModels = pickle.load(pkl_file)
    pkl_file.close()

    if testMode: return True

def gtfGeneModelParser(self, file_name, gene_mapping_file=None, testMode=False):
        self.name = 'GTF'
        # print( 'GeneModel format: ', self.name, '\timporting: ', file_name, file=sys.stderr )
        self.location = file_name

        f = GtfFileReader( file_name )
        for nLR, rx in enumerate(f):
          if rx['feature'] in ['gene']:
                continue 

          if testMode and nLR > NumOfLine2Read4Test: return True

          trID = rx['attributes']['transcript_id']
          if rx['feature'] in ['transcript','Selenocysteine']:
            if rx['feature'] in ['Selenocysteine'] and trID in self.transcriptModels:
                continue

            if trID in self.transcriptModels:
                raise Exception("{} of {}: already existed on transcriptModels".format( trID, rx['feature'] ))

            tm = TranscriptModel()
            tm.gene = rx['attributes']['gene_name']
            tm.trID = trID
            tm.chr  = rx['seqname']
            tm.strand = rx['strand']
            tm.tx     = (rx['start'],rx['end'])
            tm.cds    = (rx['end'],rx['start'])
            tm.attr   = rx['attributes']

            self.addModelToDict(tm)
            #self.transcriptModels[tm.trID] = tm
            continue

          if rx['feature'] in ['CDS','exon']:
             if trID not in self.transcriptModels:
                raise Exception("{}: exon or CDS not existed on transcriptModels".format( trID ))
        
             ix = int(rx['attributes']['exon_number']) - 1 # 1-based to 0-based indexing
             #print trID, len(self.transcriptModels[trID].exons), ix, rx['attributes']['exon_number']
             if len(self.transcriptModels[trID].exons) <= ix:
                self.transcriptModels[trID].exons.append( Exon() )

             if rx['feature'] == 'exon':
                self.transcriptModels[trID].exons[ix].start = rx['start']
                self.transcriptModels[trID].exons[ix].stop  = rx['end']
                self.transcriptModels[trID].exons[ix].frame = -1
                self.transcriptModels[trID].exons[ix].number = ix + 1 #return to 1-base indexing

                continue

             if rx['feature'] == 'CDS':
                self.transcriptModels[trID].exons[ix].cds_start = rx['start']
                self.transcriptModels[trID].exons[ix].cds_stop  = rx['end']
                self.transcriptModels[trID].exons[ix].frame     = int(rx['phase'])

                self.transcriptModels[trID]._is_coding = True

                cx = self.transcriptModels[trID].cds
                self.transcriptModels[trID].cds = (min(cx[0],rx['start']), max(cx[1],rx['end']))

                continue

          if rx['feature'] in ['UTR','start_codon','stop_codon']:
                ix = int(rx['attributes']['exon_number']) # 1-based
                if rx['feature'] == 'UTR':
                        self.transcriptModels[trID].utrs.append( (rx['start'],rx['end'],ix) )
                if rx['feature'] == 'start_codon':
                        self.transcriptModels[trID].start_codon = (rx['start'],rx['end'],ix)
                if rx['feature'] == 'stop_codon':
                        self.transcriptModels[trID].stop_codon  = (rx['start'],rx['end'],ix)

                continue
          
          raise Exception("unknown {} found".format( rx['feature'] ))

        for k in self.transcriptModels.keys():
           self.transcriptModels[k].exons = sorted( self.transcriptModels[k].exons, key=lambda x: x.start )
           self.transcriptModels[k].utrs  = sorted( self.transcriptModels[k].utrs, key=lambda x: x[0] )

        #TODO: no need: done by self.addModelToDict(tm)
        #for k, gx in self.transcriptModels.items():
        #   gID = gx.gene
        #   if gID not in self._geneModels: self._geneModels[gID] = []
        #
        #   self._geneModels[gID].append( gx )
        if testMode: return True

#
#  MT chromosome
#
def mitoGeneModelParser(self, file_name, gene_mapping_file=None, testMode=False ):
        self.name = "mitomap"
        self._Alternative_names = None

        self._utrModels['chrM'] = {}
        file = openFile(file_name)

        for line in file:
            line = line.split()
            if line[0] == "#":
                mode = line[1]
                continue

            if mode not in ['cds','rRNAs','tRNAs']: continue

            mm = TranscriptModel()
            mm.gene = mm.trID = line[0]
            mm.chr = "chrM"
            mm.strand = line[1]
            mm.tx = (int(line[2]), int(line[3]))
            mm.attr = {}

            e = Exon()
            e.start = int(line[2])
            e.stop = int(line[3])

            if mode == "cds":
                mm.cds = (int(line[2]), int(line[3]))
                e.frame = 0

            elif mode == "rRNAs":
                mm.cds = (int(line[2]), int(line[2]))
                e.frame = -1

            elif mode == "tRNAs":
                mm.cds = (int(line[2]), int(line[2]))
                mm.attr['anticodonB'] = line[4]
                mm.attr['anticodonE'] = line[5]
                e.frame = -1
            #commented on original ewa version
            #elif mode == "regulatory_elements":
            #   mm.cds = (int(line[2]), int(line[2]))
            #   mm.tx = (int(line[1]), int(line[2]))    #note about original: line is different from others
            #   mm.exons = []

            else: #TODO: something wrong message
                continue # impossible to happen

            mm.exons = [e]

            self._utrModels['chrM'][mm.tx] = [mm]
            self.transcriptModels[mm.trID] = mm
            self._geneModels[mm.gene] = [mm]
              
        file.close()

        if testMode: return True

class parserLine4UCSC_genePred:
   commonCols = Columns4FileFormat['commonGenePredUCSC']

   def __init__( cls, header ):
     '''
        header: list of column names
           name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,exonStarts,exonEnds
        required
     '''
     cls.header = header
     cls.idxHD  = { n:i for i,n in enumerate(cls.header) }

   def parse(cls, line):
     '''
       reading tab-delimited line
       return:  1) transcriptModel without gene name
                2) parsed data in dict format
     '''
     terms = line.strip('\n').split('\t')

     assert len(terms) == len(cls.header)

     cs = {k:v for k,v in zip(cls.header,terms)}

     tm = TranscriptModel()

     #tm.gene   = # TODO implimented outside 
     tm.trID   = cs['name']
     tm.chr    = cs['chrom']
     tm.strand = cs['strand']
     tm.tx     = (int(cs['txStart'])+1,int(cs['txEnd']))
     tm.cds    = (int(cs['cdsStart'])+1,int(cs['cdsEnd']))
     tm.exons  = [Exon(b+1,e) for b,e in zip(map(int,cs['exonStarts'].strip(",").split(",")),
                                             map(int,cs['exonEnds'  ].strip(",").split(",")))]

     tm.attr = { k:v for k,v in cs.items() if k not in parserLine4UCSC_genePred.commonCols }
     tm.update_frames()

     #trIdC[tm.trID] += 1                       #TODO implimented outside
     #tm.trID += "_" + str(trIdC[tm.trID])      #TODO implimented outside

     #self.addModelToDict(tm)                   #TODO should be done outside
     return tm, cs

def geneMapping( fileName=None ):
   '''
      alternative names for genes
      assume that its first line has two column names
   '''
   if not fileName: return {}

   inF = openFile(fileName )

   inF.readline()

   altName = {}
   for line in inF:
        k,v = line.strip('\n').split('\t')
        altName[k] = v

   return altName

def refSeqParser( self, location=None, gene_mapping_file = None, testMode=False ):
    colNames = Columns4FileFormat['refSeq']
    lR = parserLine4UCSC_genePred(colNames)

    if not location: location = self.location

    GMF = openFile(location)

    trIdC = defaultdict(int)
    for nLR, line in enumerate(GMF):
       if line[0] == "#": continue

       if testMode and nLR > NumOfLine2Read4Test:
            GMF.close()
            return True

       tm, cs = lR.parse( line )
       tm.gene = cs['name2'] 

       trIdC[tm.trID] += 1
       tm.trID += "_" + str(trIdC[tm.trID])
       tm.update_frames()

       self.addModelToDict(tm)

    GMF.close()
    if testMode: return True
        

def refFlatParser( self, file_name, gene_mapping_file, testMode=False):
        assert gene_mapping_file == "default"

        #column names
        colNames = Columns4FileFormat['refFlat']
        lR = parserLine4UCSC_genePred(colNames)

        GMF = openFile(file_name)
       
        trIdC = defaultdict(int)
        for nLR,line in enumerate(GMF):
            if line[0] == "#":
                hcs = line[1:].strip("\n\r").split("\t")
                if hcs != Columns4FileFormat['refFlat']: 
                    raise Exception("The file " + file_name + " doesn't look like a refFlat file")

                continue

            if testMode and nLR > NumOfLine2Read4Test:
                GMF.close()
                return True

            tm, cs =  lR.parse( line ) 
            tm.gene = cs['geneName'] 

            trIdC[tm.trID] += 1
            tm.trID += "_" + str(trIdC[tm.trID])
            tm.update_frames()

            self.addModelToDict(tm)

        GMF.close()
        if testMode: return True

def knownGeneParser(self, file_name, gene_mapping_file='default',testMode=False):
    colNames = Columns4FileFormat['knownGene']
    lR = parserLine4UCSC_genePred(colNames)

    if gene_mapping_file == 'default':
        gene_mapping_file = os.path.dirname(file_name) + "/kgId2Sym.txt.gz"

    if not testMode: self._Alternative_names = geneMapping( gene_mapping_file)

    GMF = openFile(file_name)

    trIdC = defaultdict(int)
    for nLR,line in enumerate(GMF):
        if line[0] == "#": continue

        if testMode and nLR > NumOfLine2Read4Test:
            GMF.close()
            return True

        tm, cs =  lR.parse( line ) 
        try:
            if not testMode: tm.gene = self._Alternative_names[cs['name']]
        except KeyError as e:
            tm.gene = cs['name']

        trIdC[tm.trID] += 1
        tm.trID += "_" + str(trIdC[tm.trID])
        tm.update_frames()

        self.addModelToDict(tm)

    GMF.close()
    if testMode: return True

#  format = refseq
#  CCC = {"refseq":refseqParser, ....}
#  o = GeneModelDB()
#  CCC[format](o,file, geneMapFile)
#
    
# ccdsGene
def ccdsParser(self, file_name, gene_mapping_file='default', testMode=False ):
    colNames = Columns4FileFormat['ccds']
    lR = parserLine4UCSC_genePred(colNames)

    if gene_mapping_file == 'default':
        gene_mapping_file = os.path.dirname(file_name) + "/ccdsId2Sym.txt.gz"

    if not testMode: self._Alternative_names = geneMapping( gene_mapping_file)

    GMF = openFile(file_name)

    trIdC = defaultdict(int)
    for nLR,line in enumerate(GMF):
        if line[0] == "#": continue

        if testMode and nLR > NumOfLine2Read4Test:
            GMF.close()
            return True

        tm, cs =  lR.parse( line ) 
        try:
            if not testMode:
                tm.gene = self._Alternative_names[cs['name']]
        except KeyError as e:
            tm.gene = cs['name']

        trIdC[tm.trID] += 1
        tm.trID += "_" + str(trIdC[tm.trID])
        tm.update_frames()

        self.addModelToDict(tm)

    GMF.close()
    if testMode: return True

# 
# similar to refFlat except geneName (missing column)
#
def ucscGenePredParser(self, file_name, gene_mapping_file='default', testMode=False ):
    colNames = Columns4FileFormat['ucscGenePred']
    lR = parserLine4UCSC_genePred(colNames)

    if (not testMode) and (gene_mapping_file != 'default'):
        self._Alternative_names = geneMapping( gene_mapping_file)

    GMF = openFile(file_name)

    trIdC = defaultdict(int)
    for nLR,line in enumerate(GMF):
        if line[0] == "#": continue

        if testMode and nLR > NumOfLine2Read4Test:
            GMF.close()
            return True


        tm, cs =  lR.parse( line ) 
        try:
            tm.gene = self._Alternative_names[cs['name']]
        except (KeyError,TypeError) as e:
            tm.gene = cs['name']

        trIdC[tm.trID] += 1
        tm.trID += "_" + str(trIdC[tm.trID])
        tm.update_frames()

        self.addModelToDict(tm)

    GMF.close()
    if testMode: return True


FORMAT = namedtuple('format', 'name parser')

KNOWN_FORMAT = { \
  "refFlat.txt.gz":   FORMAT( *['refflat', refFlatParser  ] ), 'refflat':   FORMAT( *['refflat',  refFlatParser ] ), 
  "refGene.txt.gz":   FORMAT( *['refseq',  refSeqParser] ),    'refseq':    FORMAT( *['refseq',   refSeqParser  ] ),
  "ccdsGene.txt.gz":  FORMAT( *['ccds',    ccdsParser     ] ), 'ccds':      FORMAT( *['ccds',     ccdsParser    ] ),
  "knownGene.txt.gz": FORMAT( *['knowngene',knownGeneParser] ),'knowngene': FORMAT( *['knowngene', knownGeneParser] ),
  "gtf":              FORMAT( *['gtf',      gtfGeneModelParser      ] ),
  "pickled":          FORMAT( *['pickled',  pickledGeneModelParser] ),
  "mitomap.txt":      FORMAT( *['mito',     mitoGeneModelParser] ), 'mito': FORMAT( *['mito', mitoGeneModelParser] ),
  "default":          FORMAT( *['default',  defaultGeneModelParser]),
  "ucscgenepred":     FORMAT( *['ucscgenepred', ucscGenePredParser] )  }

KNOWN_FORMAT_NAME = 'refflat,refseq,ccds,knowngene,gtf,pickled,mito,default,ucscgenepred'.split(',')

def infer_format( file_name='refGene.txt.gz', file_format=None ):
    acceptedFormat = []

    known_format = KNOWN_FORMAT_NAME
    if file_format:
        known_format = [file_format]

    for fn in known_format:
        gm = GeneModelDB()
        fm = KNOWN_FORMAT[fn]
        try:
            flag = fm.parser( gm, file_name, gene_mapping_file="default", testMode=True )
        except Exception as e:
            #print( "\t\t", fn,e)
            continue

        acceptedFormat.append(fn)

    if len( acceptedFormat ) != 1:
        raise Exception( '[{}:"{}"] non-mataching/more than 1 match/match-not-found from known formats [{}]\nplease specify by --TrawFormat'.format( \
            file_name, ','.join(acceptedFormat), ','.join(known_format) ) )

    acceptedFormat = acceptedFormat[0]
    if (file_name.endswith( '.gtf' ) or file_name.endswith( '.gtf.gz' )) and (acceptedFormat != 'gtf'):
        raise Exception( '{} is not GTF format'.format( file_name ) )

    if file_name.endswith('.dump') and  (acceptedFormat != 'pickled'):
        raise Exception( '{} is not "pickled" format'.format( file_name ) )

    fn = file_name.split('/')[-1]
    if fn in KNOWN_FORMAT:
        fm = KNOWN_FORMAT[fn].name
        if fm != acceptedFormat:
            raise Exception( '"{}:{}": conflict with Database [{}:{}]'.format( fn,acceptedFormat, fn,fm ) )

    return acceptedFormat

def load_gene_models(file_name="/data/unsafe/autism/genomes/hg19/geneModels/refGene.txt.gz", \
         gene_mapping_file="default", format=None ):

    fm = KNOWN_FORMAT[ infer_format( file_name, file_format=format ) ]

    gm = GeneModelDB()
    gm.location = file_name
    fm.parser( gm, file_name, gene_mapping_file)

    return gm
    
def save_pickled_dicts(gm, outputFile = "./geneModels"):
    
    import pickle
    
    pickle.dump([gm._utrModels, gm.transcriptModels, gm._geneModels], open(outputFile + ".dump", 'wb'), 2)
    
def create_region(chrom, b, e):
    reg = namedtuple('reg', 'start stop chr')
    
    return(reg(chr=chrom, start=b, stop=e))

def join_gene_models(*gene_models):

    if len(gene_models) < 2:
        raise Exception("The function needs at least 2 arguments!")
    
    gm = GeneModels()
    gm._utrModels = {}
    gm._geneModels = {}
    
   
    gm.transcriptModels = gene_models[0].transcriptModels.copy()
    
    for i in gene_models[1:]:
        gm.transcriptModels.update(i.transcriptModels)

    gm._updateIndexes()

    return(gm)


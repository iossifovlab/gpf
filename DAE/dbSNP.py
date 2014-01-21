#!/bin/env python

# Jan 21th 2014
# by Ewa

import gzip
from collections import defaultdict
import sys
import numpy as np
import h5py
import bisect
import time, datetime
from VariantAnnotation import load_variant

def _dd():
        return(defaultdict(list))

def find_ge(A, x):
        # Find leftmost value greater or equal than x
	i = bisect.bisect_left(A, x)
	return(i)

def find_le(A, x):
	# Find rightmost value less than or equal to x
	i = bisect.bisect_right(A, x)
	return(i-1)

def find_gt(A, x):
	# Find leftmost value greater than x
	i = bisect.bisect_right(A, x)
	return(i)


class DbSNP:
	location = None
	Scores = None
	_S1 = None
	_S2 = None
	_only_variants = ['single', 'insertion', 'deletion']
    
	def _create_dict(self, file):
	# numpy array, line by line
		D = {}
	
		dt = np.dtype([('id', int),('chr', '|S12'),('posB', int), ('posE', int), ('name', '|S18'), ('score', int), ('strand', '|S2'), ('refNCBI', '|S20'), ('refUCSC', '|S20'), ('observed', '|S20'), ('molType', '|S12'), ('class', '|S12'), ('valid', '|S12'), ('av_het', float), ('av_het_se', float), ('func', '|S12'), ('locType', '|S12'), ('weight', int), ('exceptions', '|S12'), ('submitterCount', int), ('submitters', '|S12'), ('alleleFreqCount', int), ('alleles', '|S12'), ('alleleNs', '|S12'), ('alleleFreqs', '|S12'), ('bitfields', '|S12') ])
	
		self.location = file
		db_file = gzip.open(file, 'rb')
		k = 0
		chr = "chr1"
		L = []
		for line in db_file:
			line = line[:-1].split("\t")
			if line[1] != chr:
				D[chr] = np.core.records.fromrecords(L, dtype=dt)
				chr = line[1]
				L = []
			line[2] = int(line[2])+1
			line[3] = int(line[3])+1
			L.append(tuple(line))
			k += 1
			if k%1000000 == 0:
				sys.stderr.write(str(k) + " lines have been processed!\n")
		D[chr] = np.core.records.fromrecords(L, dtype=dt)
		self.Scores = D

	

	def save(self, file):
		sys.stderr.write("...saving...\n")

        
		if file.endswith(".hdf5") == False:
			file = file + ".hdf5"
        
		h5py_file = h5py.File(file, 'w')
	
		for chrom, arr in self.Scores.items():
			h5py_file[chrom] = arr
        
    
		h5py_file.close()


        
	def _load(self, file):
		sys.stderr.write("...loading " + file + " ...\n")
		self.location = file
		self.Scores = {}
		f = h5py.File(file, 'r')

		for k,v in f.items():
			self.Scores[str(k)] = v

		#self.__create_sub_dics()
	"""
	def find_variants_for_location(self, chr, pos1, pos2=None, d=100):
		if pos2 == None:
			pos2 = pos1
		I = find_gt(self.Scores[chr]['posB'], pos2) - 1
		
		if pos1 == pos2:
			V = [i for i in self.Scores[chr][I-d: I+1] if ((i['posB'] <= pos1 <= i['posE']) and i['class'] in self._only_variants)]
		else:
			V = [i for i in self.Scores[chr][I-d: I+1] if (i['posB'] <= pos1 <= i['posE'] or (pos1 < i['posB'] and pos2 >= i['posB'])) and i['class'] in self._only_variants]
		return(V)
	"""
	
	def _find_matching_variant(self, v):

		R = []
		
		I = find_gt(self.Scores[v.chr]['posB'], v.pos) - 1
		
		while self.Scores[v.chr][I]['posB'] == v.pos:
			#print I
			i = self.Scores[v.chr][I]
			
			if v.type == "substitution":
				if i['class'] != "single":
					I -= 1
					continue
				Obs = i['observed'].split("/")
				if v.ref in Obs and v.seq in Obs:
					R.append(i)
			
			elif v.type == "deletion":
				if i['class'] != "deletion":
					I -= 1
					continue
				if i['posE'] == v.pos_last + 1:
					R.append(i)

			elif v.type == "insertion":
				if i['class'] != "insertion":
					I -= 1
					continue
				obs_seq = i['observed'].split("/")[1]
				if obs_seq ==  v.seq:
					R.append(i)

			else:
				return([])
			I -= 1
		
		return(R)
		

		

	def find_variant(self, chr=None, position=None, loc=None, var=None, ref=None, alt=None, length=None, seq=None, typ=None):

		v = load_variant(chr, position, loc, var, ref, alt, length, seq, typ)
		V = self._find_matching_variant(v)
		return V
		

	
	def relabel_chromosomes(self, file="/data/unsafe/autism/genomes/hg19/ucsc2gatk.txt"):
	    
		f = open(file)
		Relabel = dict([(line.split()[0], line.split()[1]) for line in f])
		f.close()

		
		for k, v in self.Scores.items():
			sys.stderr.write("Relabeling chromosome: " + k + "\n")
			try:
				self.Scores[Relabel[k]] = v
			
			except:
				sys.stderr.write("Unknown chromosome: " + k + " -  deleting\n")
			del self.Scores[k]
			
		

		



def load_dbSNP(file = "/data/unsafe/autism/genomes/hg19/dbSNP/dbSNP_138.hdf5"):
	db = DbSNP()
	db._load(file)
	return(db)







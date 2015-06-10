'''
Created on Jun 8, 2015

@author: lubo
'''
import numpy as np
import cStringIO
import zlib 

from DAE import vDB
from collections import Counter




def _collect_affected_gene_sets(vs):
    return [set([ge['sym'] for ge in v.requestedGeneEffects])
            for v in vs]

def _collect_unique_gene_syms(affected_gene_sets):
    gene_set = set()
    for gs in affected_gene_sets:
        gene_set |= set(gs)
    return gene_set

def _count_gene_syms(affected_gene_sets):
    background = Counter()
    for gene_set in affected_gene_sets:
        for gene_sym in gene_set:
            background[gene_sym]+=1
    return background
    
def _build_synonymous_background(transmitted_study_name):
    transmitted_study = vDB.get_study(transmitted_study_name)
    vs = transmitted_study.get_transmitted_summary_variants(
                ultraRareOnly=True,
                effectTypes="synonymous")
    affected_gene_sets = _collect_affected_gene_sets(vs)
    bg_counts = _count_gene_syms(affected_gene_sets)
    
    bg_sorted = sorted(zip(bg_counts.keys(),
                           bg_counts.values(), 
                           np.zeros(len(bg_counts.keys()))))
    
    b = np.array(bg_sorted, 
                 dtype=[('sym','|S32'), ('raw','>i4'), ('weight', '>f8')])
    b['weight']=b['raw'] / (1.0 * np.sum(b['raw']))
    
    return b


class Background(object):
    def __init__(self):
        self.background = None

    @property
    def is_ready(self):
        return self.background
    
    def serialize(self):
        fout = cStringIO.StringIO()
        np.save(fout, self.background)
        return zlib.compress(fout.getvalue())
    
    def deserialize(self, data):
        fin = cStringIO.StringIO(zlib.decompress(data))
        self.background = np.load(fin)
        
    def prob(self, gen_set):
        vpred = np.vectorize(lambda sym: sym in gen_set)
        index = vpred(self.background['sym'])
        return np.sum(self.background['weight'][index])
    

class SynonymousBackground(Background):
    TRANSMITTED_STUDY_NAME = 'w1202s766e611'
    
    def __init__(self):
        super(SynonymousBackground, self).__init__()
        
    def precompute(self):
        self.background = _build_synonymous_background(self.TRANSMITTED_STUDY_NAME)
        return self.background
    
    
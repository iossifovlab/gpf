'''
Created on Jun 9, 2015

@author: lubo
'''
import itertools



def filter_denovo_one_event_per_family(vs):
    """
    For each variant returns list of affected gene syms.
    
    vs - generator for variants.
    
    This functions receives a generator for variants and transforms each variant
    into list of gene symbols, that are affected by the variant.
    
    The result is represented as list of lists.
    """
    seen = set()
    res = []
    for v in vs:
        syms = set([ge['sym'] for ge in v.requestedGeneEffects])
        not_seen = [gs for gs in syms if (v.familyId+gs) not in seen]
        if not not_seen:
            continue
        for gs in not_seen:
            seen.add(v.familyId + gs)
        res.append(not_seen)

    return res


def filter_denovo_one_gene_per_recurrent_events(vs):
    gn_sorted = sorted([[ge['sym'], v] for v in vs
                       for ge in v.requestedGeneEffects])
    sym_2_vars = {sym: [t[1] for t in tpi]
                  for sym, tpi in itertools.groupby(gn_sorted,
                                                    key=lambda x: x[0])}
    sym_2_fn = {sym: len(set([v.familyId for v in vs]))
                for sym, vs in sym_2_vars.items()}
    return [[gs] for gs, fn in sym_2_fn.items() if fn > 1]


def collect_denovo_variants(dsts, inchild, effect, **kwargs):
    """
    Selects denovo variants according given test spec.
    
    dsts - list of denovo studies;
    test_spec - enrichment test specification.
    
    Returns a generator of variants.
    """
    vsres = []
    
    for dst in dsts:
        vsres.append(dst.get_denovo_variants(inChild=inchild,
                                             effectTypes=effect))
    return itertools.chain.from_iterable(vsres)


def filter_denovo_studies_by_phenotype(dsts, phenotype):
    return [st for st in dsts if st.get_attr('study.phenotype') == phenotype]


def count_denovo_variant_events(affected_gene_syms, gene_syms):
    count = 0
    for variant_gene_syms in affected_gene_syms:
        touched_gene_set = False
        for sym in variant_gene_syms:
            if sym in gene_syms:
                touched_gene_set=True
        if touched_gene_set:
            count += 1

    return count


class DenovoCounter(object):
    '''
    Represents results for Denovo Variants counters classes
    '''
    def __init__(self, spec):
        self.spec = spec
        self.count = 0
        self.affected_gene_syms = []
        self.dsts = []

    @property
    def total(self):
        return len(self.affected_gene_syms)
    
class DenovoEventsCounter:
    
    def __init__(self, spec):
        self.spec = spec
        
    def count(self, dsts, gene_set):
        res = DenovoCounter(self.spec)
        res.dsts = dsts
        vs = collect_denovo_variants(dsts, **self.spec)
        res.affected_gene_syms = filter_denovo_one_event_per_family(vs)
        res.count = count_denovo_variant_events(res.affected_gene_syms, 
                                                gene_set)
        return res

class DenovoRecurrentGenesCounter:

    def __init__(self, spec):
        self.spec = spec

    def count(self, dsts, gene_set):
        res = DenovoCounter(self.spec)
        res.dsts = dsts
        vs = collect_denovo_variants(dsts, **self.spec)
        res.affected_gene_syms = filter_denovo_one_gene_per_recurrent_events(vs)
        res.count = count_denovo_variant_events(res.affected_gene_syms, 
                                                gene_set)
        return res
    

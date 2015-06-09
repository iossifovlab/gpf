'''
Created on Jun 9, 2015

@author: lubo
'''
import itertools



PRB_TESTS_SPECS = [
    # 0
    {'label': 'prb|Rec LGDs', 
     'inchild': 'prb',
     'effect': 'LGDs'},
    # 1
    {'label': 'prb|LGDs|prb|male,female|Nonsense,Frame-shift,Splice-site',
     'inchild': 'prb', 
     'effect': 'LGDs'},
    # 2
    {'label': 'prb|Male LGDs|prb|male|Nonsense,Frame-shift,Splice-site', 
     'inchild': 'prbM', 
     'effect': 'LGDs'},
    # 3
    {'label': 'prb|Female LGDs|prb|female|Nonsense,Frame-shift,Splice-site', 
     'inchild': 'prbF', 
     'effect': 'LGDs'},
    # 4
    {'label': 'prb|Rec Missense', 
     'inchild': 'prb',
     'effect': 'missense'},
    # 5
    {'label': 'prb|Missense|prb|male,female|Missense', 
     'inchild': 'prb',
     'effect': 'missense'},
    # 6
    {'label': 'prb|Male Missense|prb|male|Missense', 
     'inchild': 'prbM', 
     'effect': 'missense'},
    # 7
    {'label': 'prb|Female Missense|prb|female|Missense', 
     'inchild': 'prbF', 
     'effect': 'missense'},
    # 8
    {'label': 'prb|Rec Synonymous', 
     'inchild': 'prb', 
     'effect': 'synonymous'},
    # 9
    {'label': 'prb|Synonymous|prb|male,female|Synonymous', 
     'inchild': 'prb', 
     'effect': 'synonymous'},
    # 10
    {'label': 'prb|Male Synonymous|prb|male|Synonymous', 
     'inchild': 'prbM', 
     'effect': 'synonymous'},
    # 11
    {'label': 'prb|Female Synonymous|prb|female|Synonymous', 
     'inchild': 'prbF', 
     'effect': 'synonymous'},
]

SIB_TESTS_SPECS = [
    # 0
    {'label': 'sib|Rec LGDs', 
     'inchild': 'sib', 
     'effect': 'LGDs'},
    # 1
    {'label': 'sib|LGDs|sib|male,female|Nonsense,Frame-shift,Splice-site', 
     'inchild': 'sib', 
     'effect': 'LGDs'},
    # 2
    {'label': 'sib|Male LGDs|sib|male|Nonsense,Frame-shift,Splice-site', 
     'inchild': 'sibM', 
     'effect': 'LGDs'},
    # 3
    {'label': 'sib|Female LGDs|sib|female|Nonsense,Frame-shift,Splice-site', 
     'inchild': 'sibF', 
     'effect': 'LGDs'},
    # 4
    {'label': 'sib|Rec Missense', 
     'inchild': 'sib', 
     'effect': 'missense'},
    # 5
    {'label': 'sib|Missense|sib|male,female|Missense', 
     'inchild': 'sib', 
     'effect': 'missense'},
    # 6
    {'label': 'sib|Male Missense|sib|male|Missense', 
     'inchild': 'sibM', 
     'effect': 'missense'},
    # 7
    {'label': 'sib|Female Missense|sib|female|Missense', 
     'inchild': 'sibF', 
     'effect': 'missense'},
    # 8
    {'label': 'sib|Rec Synonymous', 
     'inchild': 'sib', 
     'effect': 'synonymous'},
    # 9
    {'label': 'sib|Synonymous|sib|male,female|Synonymous', 
     'inchild': 'sib', 
     'effect': 'synonymous'},
    # 10
    {'label': 'sib|Male Synonymous|sib|male|Synonymous', 
     'inchild': 'sibM', 
     'effect': 'synonymous'},
    # 11
    {'label': 'sib|Female Synonymous|sib|female|Synonymous', 
     'inchild': 'sibF', 
     'effect': 'synonymous'},
]

class DenovoCounter(object):
    '''
    Denovo Variants Counters
    '''


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

def collect_denovo_variants(dsts, inchild, effect, label):
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


def count_denovo_variant_events(affected_gene_syms, gene_set):
    count = 0
    for variant_gene_syms in affected_gene_syms:
        touched_gene_set = False
        for sym in variant_gene_syms:
            if sym in gene_set:
                touched_gene_set=True
        if touched_gene_set:
            count += 1

    return count
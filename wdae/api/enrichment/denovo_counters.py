'''
Created on Jun 9, 2015

@author: lubo
'''
import itertools



PRB_TESTS_VARS = [
    ('prb|Rec LGDs', 'prb', 'LGDs'),                                # 0
    ('prb|LGDs|prb|LGD', 'prb', 'LGDs'),                            # 1
    ('prb|Male LGDs|prbM|LGD', 'prbM', 'LGDs'),                     # 2
    ('prb|Female LGDs|prbF|LGD', 'prbF', 'LGDs'),                   # 3
    ('prb|Rec Missense', 'prb', 'missense'),                        # 4
    ('prb|Missense|prb|missense', 'prb', 'missense'),               # 5
    ('prb|Male Missense|prbM|missense', 'prbM', 'missense'),        # 6
    ('prb|Female Missense|prbF|missense', 'prbF', 'missense'),      # 7
    ('prb|Rec Synonymous', 'prb', 'synonymous'),                    # 8
    ('prb|Synonymous|prb|synonymous', 'prb', 'synonymous'),         # 9
    ('prb|Male Synonymous|prb|synonymous', 'prbM', 'synonymous'),   # 10
    ('prb|Female Synonymous|prb|synonymous', 'prbF', 'synonymous'), # 11
]

SIB_TESTS_VARS = [
    ('sib|Rec LGDs', 'sib', 'LGDs'),                                # 0
    ('sib|LGDs|sib|LGD', 'sib', 'LGDs'),                            # 1
    ('sib|Male LGDs|sibM|LGD', 'sibM', 'LGDs'),                     # 3
    ('sib|Female LGDs|sibF|LGD', 'sibF', 'LGDs'),                   # 3
    ('sib|Rec Missense', 'sib', 'missense'),                        # 4
    ('sib|Missense|sib|missense', 'sib', 'missense'),               # 5
    ('sib|Male Missense|sibM|missense', 'sibM', 'missense'),        # 6
    ('sib|Female Missense|sibF|missense', 'sibF', 'missense'),      # 7
    ('sib|Rec Synonymous', 'sib', 'synonymous'),                    # 8
    ('sib|Synonymous|sib|synonymous', 'sib', 'synonymous'),         # 9
    ('sib|Male Synonymous|sib|synonymous', 'sibM', 'synonymous'),   # 10
    ('sib|Female Synonymous|sib|synonymous', 'sibF', 'synonymous'), # 11
]

class DenovoCounter(object):
    '''
    Denovo Variants Counters
    '''


def filter_denovo_one_event_per_family(vs):
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

def collect_prb_denovo_variants(dsts, gene_syms, phenotype, test_spec):
    _label, in_child, effect_types = test_spec
    vgen = []
    
    for dst in dsts:
        if phenotype != dst.get_attr('study.phenotype'):
            continue
        vgen.append(dst.get_denovo_variants(inChild=in_child,
                                            effectTypes=effect_types,
                                            geneSyms=gene_syms))
    return itertools.chain.from_iterable(vgen)

def count_denovo_events(denovo_variants, ):
    pass
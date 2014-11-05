import itertools

from DAE import *
from query_variants import dae_query_variants

from query_prepare import prepare_denovo_studies, \
    combine_gene_syms, prepare_string_value

from collections import Counter

def filter_one_var_per_gene_per_child(vs):
    ret = []
    seen = set()
    for v in vs:
        vKs = {v.familyId + "." + ge['sym'] for ge in v.requestedGeneEffects}
        if seen & vKs:
            continue
        ret.append(v)
        seen |= vKs
    return ret


def pheno_query_variants(data):
    vsl = dae_query_variants(data)
    vs = itertools.chain(*vsl)
    return filter_one_var_per_gene_per_child(vs)


def prb_gender(fms):
    prb_inds = [ind for ind, prsn in enumerate(fms.memberInOrder) if prsn.role=='prb']
    if len(prb_inds)!=1:
        return '?'
    else:
        return fms.memberInOrder[prb_inds[0]].gender

def pheno_query(data):
    vs = pheno_query_variants(data)
    
    stds = prepare_denovo_studies(data)
    all_families = {fid:prb_gender(family) for st in stds
                    for fid, family in st.families.items()}
    families_with_hit = Counter([v.familyId for v in vs])

    return all_families, families_with_hit

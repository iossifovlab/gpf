import itertools

from DAE import *
from query_variants import dae_query_variants

from query_prepare import prepare_denovo_studies, \
    combine_gene_syms, prepare_string_value


def pheno_prepare(data):
    result = {'denovoStudies': prepare_denovo_studies(data),
              'geneSet': prepare_string_value(data, 'geneSet'),
              'geneTerm': prepare_string_value(data, 'geneTerm'),
              'geneStudy': prepare_string_value(data, 'geneStudy'),
              'geneSyms': combine_gene_syms(data)}

    if 'geneSet' not in result or result['geneSet'] is None or \
       'geneTerm' not in result or result['geneTerm'] is None:
        del result['geneSet']
        del result['geneTerm']
        del result['geneStudy']

    if 'geneSet' in result and result['geneSet'] != 'denovo':
        del result['geneStudy']

    if not all(result.values()):
        return None

    return result
    

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
    query = pheno_prepare(data)
    vsl = dae_query_variants(query)
    vs = itertools.chain(*vsl)
    return vs
'''
Created on Oct 21, 2015

@author: lubo
'''
from query_variants import do_query_variants
from api.dae_query import combine_denovo_gene_sets
from DAE import get_gene_sets_symNS
from query_prepare import prepare_gene_syms
from api.preloaded.register import get_register
from django.http import QueryDict


def prepare_query_dict(data):
    res = []
    if isinstance(data, QueryDict):
        items = data.iterlists()
    else:
        items = data.items()

    for (key, val) in items:
        key = str(key)
        if isinstance(val, list):
            value = ','.join([str(s).strip() for s in val])
        else:
            value = str(val)

        res.append((key, value))

    return dict(res)


def gene_set_loader2(gene_set_label, gene_set_phenotype=None):

    gene_term = None
    if gene_set_label != 'denovo':
        register = get_register()
        if register.has_key(gene_set_label):  # @IgnorePep8
            print('gene set {} found in preloaded'.format(gene_set_label))
            return register.get(gene_set_label)

        gene_term = get_gene_sets_symNS(gene_set_label)
    else:
        gene_term = combine_denovo_gene_sets(gene_set_phenotype)

    return gene_term


def prepare_gene_sets(data):
    if 'geneSet' not in data or not data['geneSet'] or \
            not data['geneSet'].strip():
        return None

    if 'geneTerm' not in data or not data['geneTerm'] or \
            not data['geneTerm'].strip():
        return None

    gene_set = data['geneSet']
    gene_term = data['geneTerm']

    gene_set_phenotype = data['gene_set_phenotype'] \
        if 'gene_set_phenotype' in data else None

    gt = gene_set_loader2(gene_set, gene_set_phenotype)

    if gt and gene_term in gt.t2G:
        return set(gt.t2G[gene_term].keys())

    return None


def get_data_key(key, data):
    if key not in data or not data[key] or \
            not data[key].strip():
        return None
    return data[key].strip()


def prepare_gene_weights(data):
    wname = get_data_key('geneWeight', data)
    wmax = get_data_key('geneWeightMax', data)
    wmin = get_data_key('geneWeightMin', data)

    if not wname:
        return None
    register = get_register()
    weights = register.get('gene_weights')
    if not weights.has_weight(wname):
        return None
    genes = weights.get_genes_by_weight(wname, wmin=wmin, wmax=wmax)
    return genes


def combine_gene_syms(data):
    gene_syms = prepare_gene_syms(data)
    gene_sets = prepare_gene_sets(data)
    gene_weights = prepare_gene_weights(data)

    gs = [gene_syms, gene_sets, gene_weights]
    gs = [g for g in gs if g is not None]

    if not gs:
        return None
    if len(gs) == 1:
        return list(gs[0])
    if len(gs) == 2:
        return list(gs[0].union(gs[1]))
    if len(gs) == 3:
        return list(gs[0].union(gs[1]).union(gs[2]))

#     if gene_syms is None:
#         return list(gene_sets) if gene_sets else None
#     else:
#         if gene_sets is None:
#             return list(gene_syms)
#         else:
#             return list(gene_sets.union(gene_syms))


def wdae_handle_gene_sets(data):
    data['geneSyms'] = combine_gene_syms(data)
    if 'geneSet' in data:
        del data['geneSet']
    if 'geneTerm' in data:
        del data['geneTerm']
    if 'gene_set_phenotype' in data:
        del data['gene_set_phenotype']
    if 'geneWeight' in data:
        del data['geneWeight']
    if 'geneWeightMin' in data:
        del data['geneWeightMin']
    if 'geneWeightMax' in data:
        del data['geneWeightMax']


def wdae_query_wrapper(data, atts=[]):
    wdae_handle_gene_sets(data)
    return do_query_variants(data, atts)

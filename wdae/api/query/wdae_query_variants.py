'''
Created on Oct 21, 2015

@author: lubo
'''
from query_variants import do_query_variants
from api.dae_query import combine_denovo_gene_sets
from DAE import get_gene_sets_symNS
from query_prepare import prepare_gene_syms, prepare_string_value
from api.preloaded.register import get_register


def prepare_query_dict(data):
    data = dict(data)
    return data


def gene_set_loader2(gene_set_label, gene_set_phenotype=None):

    gene_term = None
    if gene_set_label != 'denovo':
        register = get_register()
        if register.has_key(gene_set_label):  # @IgnorePep8
            return register.get(gene_set_label)

        gene_term = get_gene_sets_symNS(gene_set_label)
    else:
        gene_term = combine_denovo_gene_sets(gene_set_phenotype)

    return gene_term


def prepare_gene_sets(data):
    if 'geneSet' not in data or not data['geneSet']:
        return None

    if 'geneTerm' not in data or not data['geneTerm']:
        return None

    gene_set = data['geneSet']
    gene_term = data['geneTerm']

    gene_set_phenotype = data['gene_set_phenotype'] \
        if 'gene_set_phenotype' in data else None
    if isinstance(gene_set, list):
        gene_set = str(','.join(gene_set))
    if isinstance(gene_term, list):
        gene_term = str(','.join(gene_term))
    if isinstance(gene_set_phenotype, list):
        gene_set_phenotype = ','.join(gene_set_phenotype)
    gt = gene_set_loader2(gene_set, gene_set_phenotype)

    if gt and gene_term in gt.t2G:
        return set(gt.t2G[gene_term].keys())

    return None


def get_data_key(key, data):
    if key not in data or not data[key]:
        return None
    return prepare_string_value(data, key)


def prepare_gene_weights(data):
    wname = get_data_key('geneWeight', data)
    wmax = get_data_key('geneWeightMax', data)
    if wmax:
        wmax = float(wmax)
    wmin = get_data_key('geneWeightMin', data)
    if wmin:
        wmin = float(wmin)

    if not wname:
        return None
    register = get_register()
    weights = register.get('gene_weights')
    if not weights.has_weight(wname):
        return None
    genes = weights.get_genes_by_weight(wname, wmin=wmin, wmax=wmax)
    # print("wname: {}, wmin: {}, wmax: {}".format(wname, wmin, wmax))
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

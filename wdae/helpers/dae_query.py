from __future__ import unicode_literals
from builtins import str
import logging
import helpers.GeneTerm
from django.http.request import QueryDict

from datasets_api.studies_manager import get_studies_manager

LOGGER = logging.getLogger(__name__)


def columns_to_labels(columns, column_labels):
    return [column_labels[column] for column in columns]


def join_line(l, sep='\t'):
    tl = map(lambda v: '' if v is None or v == 'None' else v, l)
    return sep.join(tl) + '\n'


def prepare_query_dict(data):
    res = []
    if isinstance(data, QueryDict):
        items = data.iterlists()
    else:
        items = list(data.items())

    for (key, val) in items:
        key = str(key)
        if isinstance(val, list):
            value = ','.join([str(s).strip() for s in val])
        elif isinstance(val, str) or isinstance(val, str):
            value = str(val.replace(u'\xa0', u' ').encode('utf-8'))
            value = value.strip()
        else:
            value = str(val)
        if value == '' or value.lower() == 'none':
            continue
        res.append((key, value))

    return dict(res)


def gene_terms_union(gene_terms):
    if len(gene_terms) == 1:
        return helpers.GeneTerm.GeneTerm(gene_terms[0])

    result = helpers.GeneTerm.GeneTerm(gene_terms[0])

    for gt in gene_terms[1:]:
        result.union(gt)

    return result


def collect_denovo_gene_sets(gene_set_phenotype):
    gscs = get_studies_manager().get_gene_sets_collections()
    denovo_gene_sets = gscs.denovo_gene_sets
    if gene_set_phenotype is None:
        gene_set_phenotype = 'autism'
    phenotypes = gene_set_phenotype.split(',')
    gene_terms = [denovo_gene_sets[pheno] for pheno in phenotypes
                  if pheno in denovo_gene_sets]
    return gene_terms


def combine_denovo_gene_sets(gene_set_phenotype):
    gene_terms = collect_denovo_gene_sets(gene_set_phenotype)
    return gene_terms_union(gene_terms)

import logging
import api.GeneTerm
from api.precompute import register

LOGGER = logging.getLogger(__name__)

from DAE import get_gene_sets_symNS

# def load_gene_set(gene_set_label, study_name=None):
#     gene_term = gene_set_loader(gene_set_label, study_name)
#     gs = api.GeneTerm.GeneTerm(gene_term)
#     return gs


def gene_terms_union(gene_terms):
    if len(gene_terms) == 1:
        return api.GeneTerm.GeneTerm(gene_terms[0])

    result = api.GeneTerm.GeneTerm(gene_terms[0])

    for gt in gene_terms[1:]:
        result.union(gt)

    return result


def collect_denovo_gene_sets(gene_set_phenotype):
    precomputed = register.get('denovo_gene_sets')
    denovo_gene_sets = precomputed.denovo_gene_sets
    if gene_set_phenotype is None:
        gene_set_phenotype = 'autism'
    phenotypes = gene_set_phenotype.split(',')
    gene_terms = [denovo_gene_sets[pheno] for pheno in phenotypes
                  if pheno in denovo_gene_sets]
    return gene_terms


def combine_denovo_gene_sets(gene_set_phenotype):
    gene_terms = collect_denovo_gene_sets(gene_set_phenotype)
    return gene_terms_union(gene_terms)


def load_gene_set2(gene_set_label, gene_set_phenotype=None):
    gene_term = None
    if gene_set_label != 'denovo':
        gene_term = get_gene_sets_symNS(gene_set_label)
    else:
        gene_term = combine_denovo_gene_sets(gene_set_phenotype)

    if gene_term:
        gs = api.GeneTerm.GeneTerm(gene_term)
        return gs
    return None


# def prepare_pheno_pedigree(cols, rows):
#     genotype_index = cols.index['family genotype']
#     from_parent_index = cols.index['from parent']
#     in_child_index = cols.index['in child']
#     population_type_index = cols.index['population type']
#     children_description_index=cols.index['children description']

#     for row in rows:
#         pass


def prepare_summary(vs):
    rows = []
    cols = vs.next()
    count = 0
    for r in vs:
        count += 1
        if count <= 1000:
            rows.append(r)
        if count > 2000:
            break

    if count <= 2000:
        count = str(count)
    else:
        count = 'more than 2000'

    return {'count': count,
            'rows': rows,
            'cols': cols}

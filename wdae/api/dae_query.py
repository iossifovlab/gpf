import logging
import api.GeneTerm

logger = logging.getLogger(__name__)
from query_prepare import gene_set_loader

from DAE import get_gene_sets_symNS, vDB
from bg_loader import get_background

def load_gene_set(gene_set_label, study_name=None):
    gene_term = gene_set_loader(gene_set_label, study_name)
    gs = api.GeneTerm.GeneTerm(gene_term)
    return gs


def load_gene_set2(gene_set_label, gene_set_phenotype=None):
    gene_term = None
    if gene_set_label!= 'denovo':
        gene_term = get_background(gene_set_label)
        if not gene_term:
            gene_term = get_gene_sets_symNS(gene_set_label)
    else:
        denovo_gene_sets = get_background('Denovo')
        if gene_set_phenotype in denovo_gene_sets:
            gene_term = denovo_gene_sets[gene_set_phenotype]
    
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

import logging
import api.GeneTerm

logger = logging.getLogger(__name__)
from query_prepare import gene_set_loader


def load_gene_set(gene_set_label, study_name=None):
    gene_term = gene_set_loader(gene_set_label, study_name)
    gs = api.GeneTerm.GeneTerm(gene_term)
    return gs


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

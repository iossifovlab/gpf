import hashlib
import logging
from django.core.cache import get_cache

from DAE import vDB
from DAE import get_gene_sets_symNS
import api.GeneTerm

logger = logging.getLogger(__name__)


def load_gene_set(gene_set_label, study_name=None):
    # cache = get_cache('long')

    # cache_key = 'gene_set_' + gene_set_label
    # if 'denovo' == gene_set_label:
    #     cache_key += '_study_' + study_name

    # key = hashlib.sha1(cache_key).hexdigest()
    # gs = cache.get(key)
    # logger.info("looking in cache for %s, found(%s)?",
    #             cache_key, (gs is not None))
    # if not gs:
    if 'denovo' == gene_set_label:
        dsts = vDB.get_studies(study_name)
        gene_term = get_gene_sets_symNS(gene_set_label, dsts)
    else:
        gene_term = get_gene_sets_symNS(gene_set_label)
    gs = api.GeneTerm.GeneTerm(gene_term)
    return gs


# def __filter_gene_set(gene_set, data):
#     gs_id = gene_set['gs_id']
#     gs_term = gene_set['gs_term']

#     if 'denovo' == gs_id:
#         study = data['geneStudy']
#         if not study:
#             return None
#         gs = load_gene_set('denovo', study)
#     else:
#         gs = load_gene_set(gs_id)

#     if gs_term not in gs.tDesc:
#         return None

#     gl = gs.t2G[gs_term].keys()

#     if not gl:
#         return None

#     return set(gl)


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

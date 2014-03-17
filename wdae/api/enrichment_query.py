from DAE import vDB
from enrichment import enrichment_test, PRB_TESTS, SIB_TESTS

from dae_query import load_gene_set
import numpy as np
from query_prepare import prepare_denovo_studies, prepare_transmitted_studies, \
    combine_gene_syms
import logging

logger = logging.getLogger(__name__)


def __prepare_string_value(data, key):
    if key not in data or not data[key] \
       or not data[key].strip():
        return None
    res = data[key].strip()
    if res == 'null' or res == 'Null' or res == 'None' or res == 'none':
        return None
    return res


def enrichment_prepare(data):
    result = {'denovoStudies': prepare_denovo_studies(data),
              'transmittedStudies': prepare_transmitted_studies(data),
              'geneSet': __prepare_string_value(data, 'geneSet'),
              'geneTerm': __prepare_string_value(data, 'geneTerm'),
              'geneStudy': __prepare_string_value(data, 'geneStudy'),
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


def colormap_value(p_val, lessmore):
    scale = 0
    if p_val > 0:
        if p_val > 0.05:
            scale = 0
        else:
            scale = - np.log10(p_val)
            if scale > 5:
                scale = 5
            elif scale < 0:
                scale = 0

    intensity = int((5.0-scale) * 255.0/5.0)
    if lessmore == 'more':
        color = "rgba(%d,%d,%d,180)" % (255, intensity, intensity)
    elif lessmore == 'less':
        color = "rgba(%d,%d,%d,180)" % (intensity, intensity, 255)
    else:
        color = "rgb(255,255,255)"
    return color


def enrichment_results(denovoStudies=None,
                       denovoStudiesName=None,
                       transmittedStudies=None,
                       geneSet=None,
                       geneTerm=None,
                       geneStudy=None,
                       geneSyms=None):

    if geneSet is None or geneSet is None:
        gene_terms = None
    else:
        gene_terms = load_gene_set(geneSet, geneStudy)

    all_res, totals = enrichment_test(denovoStudies,
                                      geneSyms)
    bg_total = totals['BACKGROUND']
    bg_cnt = all_res['BACKGROUND'].cnt
    bg_prop = round(float(bg_cnt) / bg_total, 3)

    res = {}
    res['prb'] = PRB_TESTS
    res['sib'] = SIB_TESTS
    res['denovo_study'] = denovoStudiesName
    res['gs_id'] = geneSet

    if geneSet and geneTerm:
        res['gs_desc'] = gene_terms.tDesc[geneTerm]
    else:
        desc = ','.join(geneSyms)
        res['gs_desc'] = desc
        res['gs_id'] = desc

    res['gene_number'] = len(geneSyms)
    res['overlap'] = bg_cnt
    res['prop'] = bg_prop

    for test_name in all_res:
        tres = {}

        eres = all_res[test_name]

        tres['overlap'] = totals[test_name]
        tres['count'] = eres.cnt

        p_val = eres.p_val
        if eres.p_val >= 0.0001:
            p_val = round(eres.p_val, 4)
            tres['p_val'] = p_val
        else:
            tres['p_val'] = str('%.1E' % eres.p_val)

        expected = round(eres.expected, 4)
        tres['expected'] = str(expected)

        if eres.cnt > expected:
            lessmore = 'more'
        elif eres.cnt < expected:
            lessmore = 'less'
        else:
            lessmore = 'equal'
        tres['lessmore'] = lessmore
        # tres['prop'] =
        tres['bg'] = colormap_value(p_val, lessmore)

        res[test_name] = tres

    return res

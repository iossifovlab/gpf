from DAE import vDB
from enrichment import enrichment_test, PRB_TESTS, SIB_TESTS, \
    enrichment_test_by_phenotype

from dae_query import load_gene_set
import numpy as np
from query_prepare import prepare_denovo_studies, prepare_transmitted_studies, \
    combine_gene_syms, prepare_string_value
import logging

logger = logging.getLogger(__name__)



def enrichment_prepare(data):
    result = {'denovoStudies': prepare_denovo_studies(data),
              'transmittedStudies': prepare_transmitted_studies(data),
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

from itertools import chain


def enrichment_results(denovoStudies=None,
                       denovoStudiesName=None,
                       transmittedStudies=None,
                       geneSet=None,
                       geneTerm=None,
                       geneStudy=None,
                       geneSyms=None):

    if geneSet is None:
        gene_terms = None
    else:
        gene_terms = load_gene_set(geneSet, geneStudy)

    all_res, totals = enrichment_test(denovoStudies,
                                      geneSyms)
    bg_total = totals['BACKGROUND'][0]
    bg_cnt = all_res['BACKGROUND'].cnt
    bg_prop = round(float(bg_cnt) / bg_total, 3)

    res = {}
    res['prb'] = PRB_TESTS
    res['sib'] = SIB_TESTS
    res['denovo_study'] = denovoStudiesName
    res['gs_id'] = geneSet

    if geneSet and geneTerm:
        res['gs_desc'] = "%s: %s" % (geneTerm,
                                     gene_terms.tDesc[geneTerm])
    else:
        syms = list(geneSyms)
        desc = ','.join(sorted(syms))
        res['gs_desc'] = desc
        res['gs_id'] = desc

    res['gene_number'] = len(geneSyms)
    res['overlap'] = bg_cnt
    res['prop'] = bg_prop

    for test_name in all_res:
        tres = {}

        eres = all_res[test_name]

        tres['overlap'] = totals[test_name][0]
        tres['count'] = eres.cnt
        if test_name == 'prb|Rec LGDs':
            tres['syms'] = set(chain.from_iterable(totals[test_name][1]))
            tres['syms'] = tres['syms'].intersection(geneSyms)

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


def enrichment_test_helper(all_res, totals, genes_dict, gene_syms, tests):
    res = []
    for testname in tests:
        tres = {}
        eres = all_res[testname]
        tres['overlap'] = totals[testname]
        tres['label'] = testname.split('|')[1]
        tres['count'] = eres.cnt
        if testname == 'prb|Rec LGDs':
            tres['syms'] = set(chain.from_iterable(genes_dict[testname]))
            tres['syms'] = tres['syms'].intersection(gene_syms)
        else:
            tres['filter'] = testname.split('|')[2:]
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
        tres['bg'] = colormap_value(p_val, lessmore)

        res.append(tres)
        
    return res
    
def enrichment_results_by_phenotype(
        denovoStudies=None,
        transmittedStudies=None,
        geneSet=None,
        geneTerm=None,
        geneStudy=None,
        geneSyms=None):

    count_res_by_pheno, totals_by_pheno, genes_dict_by_pheno = \
        enrichment_test_by_phenotype(denovoStudies, geneSyms)
    
    res = {}
    res['gs_id'] = geneSet

    if geneSet is None:
        gene_terms = None
    else:
        gene_terms = load_gene_set(geneSet, geneStudy)
    
    if geneSet and geneTerm:
        res['gs_desc'] = "%s: %s" % (geneTerm,
                                     gene_terms.tDesc[geneTerm])
    else:
        syms = list(geneSyms)
        desc = ','.join(sorted(syms))
        res['gs_desc'] = desc
        res['gs_id'] = desc

    res['gene_number'] = len(geneSyms)

    res['phenotypes'] = sorted(count_res_by_pheno.keys())

    for phenotype in count_res_by_pheno.keys():
        logger.info("calculating enrichment for phenotype: %s", phenotype)
        
        all_res = count_res_by_pheno[phenotype]
        totals = totals_by_pheno[phenotype]
        genes_dict = genes_dict_by_pheno[phenotype]
        tests = PRB_TESTS
        if phenotype == 'unaffected':
            tests = SIB_TESTS
        res[phenotype] = enrichment_test_helper(all_res, totals, genes_dict, geneSyms, tests)

    return res
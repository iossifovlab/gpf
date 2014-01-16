from django.core.cache import get_cache

from DAE import vDB

import itertools
import logging


logger = logging.getLogger(__name__)


def one_variant_per_recurrent(vs):
    gn_sorted = sorted([[ge['sym'], v] for v in vs
                       for ge in v.requestedGeneEffects])
    sym_2_vars = {sym: [t[1] for t in tpi]
                  for sym, tpi in itertools.groupby(gn_sorted,
                                                    key=lambda x: x[0])}
    sym_2_fn = {sym: len(set([v.familyId for v in vs]))
                for sym, vs in sym_2_vars.items()}
    return [[gs] for gs, fn in sym_2_fn.items() if fn > 1]


def filter_denovo(vs):
    seen = set()
    res = []
    for v in vs:
        syms = set([ge['sym'] for ge in v.requestedGeneEffects])
        var_gss = [gs for gs in syms if (v.familyId+gs) not in seen]
        if not var_gss:
            continue
        for gs in var_gss:
            seen.add(v.familyId + gs)
        res.append(var_gss)

    return res


def filter_transmitted(vs):
    return [set([ge['sym'] for ge in v.requestedGeneEffects])
            for v in vs]


def __build_or_load_transmitted(tstd):
    cache = get_cache('long')
    background = cache.get('enrichment_background_model.'+tstd.name)
    if not background:
        background = filter_transmitted(
            tstd.get_transmitted_summary_variants(ultraRareOnly=True,
                                                  effectTypes="synonymous"))
        cache.set('enrichment_background_model.'+tstd.name, background)

    return ['BACKGROUND', background]

PRB_TESTS = ['prb|Rec LGDs',         # 0
             'prb|LGDs',             # 1
             'prb|Male LGDs',        # 2
             'prb|Female LGDs',      # 3
             'prb|Missense',         # 4
             'prb|Male Missense',    # 5
             'prb|Female Missense',  # 6
             'prb|Synonymous']       # 7

SIB_TESTS = ['sib|LGDs',             # 0
             'sib|Male LGDs',        # 1
             'sib|Female LGDs',      # 2
             'sib|Missense',         # 3
             'sib|Synonymous']       # 4


def __build_variants_genes_dict(denovo, transmitted, geneSyms=None):
    return [
        [PRB_TESTS[0],
         one_variant_per_recurrent(
             vDB.get_denovo_variants(denovo,
                                     inChild='prb',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        [PRB_TESTS[1],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prb',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        [PRB_TESTS[2],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prbM',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        [PRB_TESTS[3],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prbF',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        [PRB_TESTS[4],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prb',
                                     effectTypes="missense",
                                     geneSyms=geneSyms))],

        [PRB_TESTS[5],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prbM',
                                     effectTypes="missense",
                                     geneSyms=geneSyms))],
        [PRB_TESTS[6],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prbF',
                                     effectTypes="missense",
                                     geneSyms=geneSyms))],
        [PRB_TESTS[7],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prb',
                                     effectTypes="synonymous",
                                     geneSyms=geneSyms))],
        [SIB_TESTS[0],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='sib',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        [SIB_TESTS[1],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='sibM',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        [SIB_TESTS[2],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='sibF',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        [SIB_TESTS[3],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='sib',
                                     effectTypes="missense",
                                     geneSyms=geneSyms))],
        [SIB_TESTS[4],
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='sib',
                                     effectTypes="synonymous",
                                     geneSyms=geneSyms))],

        __build_or_load_transmitted(transmitted)
    ]


class EnrichmentTestRes:
    def __init__(self):
        self.cnt = 0
        self.p_val = 0.0
        self.q_val = 0.0
        self.expected = 0.0

    def __str__(self):
        return "ET(%d (%0.4f), p_val=%0.4f, q_val=%0.4f)" % \
            (self.cnt, self.expected, self.p_val, self.q_val)

    def __repr__(self):
        return self.__str__()

from scipy import stats


def __init_gene_set_enrichment(var_genes_dict, gene_terms):
    all_res = {}
    for set_name in gene_terms.t2G:
        all_res[set_name] = {}
    return all_res


def __count_gene_set_enrichment(all_res, var_genes_dict, gene_terms):
    for test_name, gene_syms in var_genes_dict:
        for set_name in gene_terms.t2G:
            all_res[set_name][test_name] = EnrichmentTestRes()
        for gene_sym_list in gene_syms:
            touched_gene_sets = set()
            for gene_sym in gene_sym_list:
                if gene_sym in gene_terms.g2T:
                    touched_gene_sets |= set(gene_terms.g2T[gene_sym])
            for gene_set in touched_gene_sets:
                all_res[gene_set][test_name].cnt += 1


import api.GeneTerm


def enrichment_test(dsts, tsts, gene_terms, gene_set_name):
    gtr = api.GeneTerm.GeneTerm(gene_terms, gene_set_name)
    var_genes_dict = __build_variants_genes_dict(dsts, tsts)

    all_res = __init_gene_set_enrichment(var_genes_dict, gtr)
    __count_gene_set_enrichment(all_res, var_genes_dict, gtr)

    totals = {test_name: len(gene_syms)
              for test_name, gene_syms in var_genes_dict}
    bg_total = totals['BACKGROUND']

    for gene_set in gtr.t2G:
        bg_gene_set = all_res[gene_set]['BACKGROUND'].cnt
        if bg_gene_set == 0:
            bg_gene_set = 0.5
        bg_prob = float(bg_gene_set) / bg_total

        for test_name, gene_syms in var_genes_dict:
            res = all_res[gene_set][test_name]
            total = totals[test_name]
            res.p_val = stats.binom_test(res.cnt, total, p=bg_prob)
            res.expected = round(bg_prob*total, 4)

    return all_res, totals


from dae_query import load_gene_set
import numpy as np


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


def enrichment_results(dst_name, tst_name, gt_name, gs_name, gt_study=None):
        dsts = vDB.get_studies(dst_name)
        tsts = vDB.get_study(tst_name)
        gene_terms = load_gene_set(gt_name, gt_study)

        all_res, totals = enrichment_test(dsts,
                                          tsts,
                                          gene_terms,
                                          gs_name)
        bg_total = totals['BACKGROUND']
        bg_cnt = all_res[gs_name]['BACKGROUND'].cnt
        bg_prop = round(float(bg_cnt) / bg_total, 3)

        res = {}
        res['prb'] = PRB_TESTS
        res['sib'] = SIB_TESTS
        res['denovo_study'] = dst_name
        res['gs_id'] = gs_name
        res['gs_desc'] = gene_terms.tDesc[gs_name]
        res['gene_number'] = len(gene_terms.t2G[gs_name])
        res['overlap'] = bg_cnt
        res['prop'] = bg_prop

        for test_name in all_res[gs_name]:
            tres = {}

            eres = all_res[gs_name][test_name]

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

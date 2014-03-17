
from DAE import vDB

import itertools
import logging
# import hashlib
# from api.wdae_cache import store, retrieve
from bg_loader import get_background

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


def build_transmitted_background(tstd):
    return filter_transmitted(
        tstd.get_transmitted_summary_variants(ultraRareOnly=True,
                                              effectTypes="synonymous"))


# def preload_background(tstd):
#     builder_func = build_transmitted, (tstd, ), 'background'
#     builders = [builder_func]
#     thread = BackgroundBuilderTask(builders)
#     thread.start()


PRB_TESTS = ['prb|Rec LGDs',                       # 0
             'prb|LGDs|prb|LGD',                   # 1
             'prb|Male LGDs|prbM|LGD',             # 2
             'prb|Female LGDs|prbF|LGD',           # 3
             'prb|Missense|prb|missense',          # 4
             'prb|Male Missense|prbM|missense',    # 5
             'prb|Female Missense|prbF|missense',  # 6
             'prb|Synonymous|prb|synonymous']      # 7

SIB_TESTS = ['sib|LGDs|sib|LGD',                   # 0
             'sib|Male LGDs|sibM|LGD',             # 1
             'sib|Female LGDs|sibF|LGD',           # 2
             'sib|Missense|sib|missense',          # 3
             'sib|Synonymous|sib|synonymous']      # 4


def __build_variants_genes_dict(denovo, geneSyms=None):
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


        ['BACKGROUND', get_background('enrichment_background')]

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


def __count_gene_set_enrichment(var_genes_dict, gene_syms_set):
    all_res = {}
    for test_name, gene_syms in var_genes_dict:
        all_res[test_name] = EnrichmentTestRes()
        for gene_sym_list in gene_syms:
            touched_gene_sets = False
            for gene_sym in gene_sym_list:
                if gene_sym in gene_syms_set:
                    touched_gene_sets = True
            if touched_gene_sets:
                all_res[test_name].cnt += 1
    return all_res


def enrichment_test(dsts, gene_syms_set):
    var_genes_dict = __build_variants_genes_dict(dsts)

    all_res = __count_gene_set_enrichment(var_genes_dict, gene_syms_set)
    totals = {test_name: len(gene_syms)
              for test_name, gene_syms in var_genes_dict}
    bg_total = totals['BACKGROUND']

    bg_gene_set = all_res['BACKGROUND'].cnt
    if bg_gene_set == 0:
        bg_gene_set = 0.5
    bg_prob = float(bg_gene_set) / bg_total

    for test_name, gene_syms in var_genes_dict:
        res = all_res[test_name]
        total = totals[test_name]
        res.p_val = stats.binom_test(res.cnt, total, p=bg_prob)
        res.expected = round(bg_prob*total, 4)

    return all_res, totals

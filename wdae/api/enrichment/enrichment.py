from collections import defaultdict
from DAE import vDB

import itertools
import logging
from scipy import stats

from api.deprecated.bg_loader import get_background

LOGGER = logging.getLogger(__name__)


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


PRB_TESTS = [
    'prb|Rec LGDs',                                                   # 0
    'prb|LGDs|prb|male,female|Nonsense,Frame-shift,Splice-site',      # 1
    'prb|Male LGDs|prb|male|Nonsense,Frame-shift,Splice-site',        # 2
    'prb|Female LGDs|prb|female|Nonsense,Frame-shift,Splice-site',    # 3
    'prb|Rec Missense',                                               # 4
    'prb|Missense|prb|male,female|Missense',                          # 5
    'prb|Male Missense|prb|male|Missense',                            # 6
    'prb|Female Missense|prb|female|Missense',                        # 7
    'prb|Rec Synonymous',                                             # 8
    'prb|Synonymous|prb|male,female|Synonymous',                      # 9
    'prb|Male Synonymous|prb|male|Synonymous',                        # 10
    'prb|Female Synonymous|prb|female|Synonymous',                    # 11
]

SIB_TESTS = [
    'sib|Rec LGDs',                                                   # 0
    'sib|LGDs|sib|male,female|Nonsense,Frame-shift,Splice-site',      # 1
    'sib|Male LGDs|sib|male|Nonsense,Frame-shift,Splice-site',        # 2
    'sib|Female LGDs|sib|female|Nonsense,Frame-shift,Splice-site',    # 3
    'sib|Rec Missense',                                               # 4
    'sib|Missense|sib|male,female|Missense',                          # 5
    'sib|Male Missense|sib|male|Missense',                            # 6
    'sib|Female Missense|sib|female|Missense',                        # 7
    'sib|Rec Synonymous',                                             # 8
    'sib|Synonymous|sib|male,female|Synonymous',                      # 9
    'sib|Male Synonymous|sib|male|Synonymous',                        # 10
    'sib|Female Synonymous|sib|female|Synonymous',                    # 11
    ]

PRB_TESTS_VARS = [
    ('prb|Rec LGDs', 'prb', 'LGDs'),                                # 0
    ('prb|LGDs|prb|LGD', 'prb', 'LGDs'),                            # 1
    ('prb|Male LGDs|prbM|LGD', 'prbM', 'LGDs'),                     # 2
    ('prb|Female LGDs|prbF|LGD', 'prbF', 'LGDs'),                   # 3
    ('prb|Rec Missense', 'prb', 'missense'),                        # 4
    ('prb|Missense|prb|missense', 'prb', 'missense'),               # 5
    ('prb|Male Missense|prbM|missense', 'prbM', 'missense'),        # 6
    ('prb|Female Missense|prbF|missense', 'prbF', 'missense'),      # 7
    ('prb|Rec Synonymous', 'prb', 'synonymous'),                    # 8
    ('prb|Synonymous|prb|synonymous', 'prb', 'synonymous'),         # 9
    ('prb|Male Synonymous|prb|synonymous', 'prbM', 'synonymous'),   # 10
    ('prb|Female Synonymous|prb|synonymous', 'prbF', 'synonymous'), # 11
]

SIB_TESTS_VARS = [
    ('sib|Rec LGDs', 'sib', 'LGDs'),                                # 0
    ('sib|LGDs|sib|LGD', 'sib', 'LGDs'),                            # 1
    ('sib|Male LGDs|sibM|LGD', 'sibM', 'LGDs'),                     # 3
    ('sib|Female LGDs|sibF|LGD', 'sibF', 'LGDs'),                   # 3
    ('sib|Rec Missense', 'sib', 'missense'),                        # 4
    ('sib|Missense|sib|missense', 'sib', 'missense'),               # 5
    ('sib|Male Missense|sibM|missense', 'sibM', 'missense'),        # 6
    ('sib|Female Missense|sibF|missense', 'sibF', 'missense'),      # 7
    ('sib|Rec Synonymous', 'sib', 'synonymous'),                    # 8
    ('sib|Synonymous|sib|synonymous', 'sib', 'synonymous'),         # 9
    ('sib|Male Synonymous|sib|synonymous', 'sibM', 'synonymous'),   # 10
    ('sib|Female Synonymous|sib|synonymous', 'sibF', 'synonymous'), # 11
]

def collect_prb_enrichment_variants_by_phenotype(dsts):
    collector = defaultdict(lambda: [[],[],[],[],[],[],[],[],[],[],[],[],])
    for dst in dsts:
        phenotype = dst.get_attr('study.phenotype')
        for n, (_label, in_child, effect_types) in enumerate(PRB_TESTS_VARS):
            collector[phenotype][n].append(
                dst.get_denovo_variants(inChild=in_child,
                                        effectTypes=effect_types))

    res = {}
    for key, evars in collector.items():
        res[key] = [itertools.chain.from_iterable(vgen) for vgen in evars]
    return res

def collect_sib_enrichment_variants_by_phenotype(dsts):
    collector = [[],[],[],[],[],[],[],[],[],[],[],[],]
    for dst in dsts:
        for n, (_label, in_child, effect_types) in enumerate(SIB_TESTS_VARS):
            collector[n].append(
                dst.get_denovo_variants(inChild=in_child,
                                        effectTypes=effect_types))

    res = [itertools.chain.from_iterable(vgen) for vgen in collector]
    return res

def filter_prb_enrichment_variants_by_phenotype(pheno_evars):
    res = {}
    for phenotype, evars in pheno_evars.items():
        gen = zip(PRB_TESTS, evars)
        pheno_res = []
        for test, vs in gen:
            if "Rec" in test:
                pheno_res.append(one_variant_per_recurrent(vs))
            else:
                pheno_res.append(filter_denovo(vs))
#         gen = iter(evars)
#         rec_vars = gen.next()
#         pheno_res = [one_variant_per_recurrent(rec_vars)]
#         for vs in gen:
#             pheno_res.append(filter_denovo(vs))
        res[phenotype] = zip(PRB_TESTS, pheno_res)
    return res

def filter_sib_enrichment_variants_by_phenotype(evars):

    gen = zip(SIB_TESTS, evars)
    res = []
    for test, vs in gen:
        if "Rec" in test:
            res.append(one_variant_per_recurrent(vs))
        else:
            res.append(filter_denovo(vs))

#     gen = iter(evars)
#
#     rec_vars = gen.next()
#     res = [one_variant_per_recurrent(rec_vars)]
#     for vs in gen:
#         res.append(filter_denovo(vs))
    return zip(SIB_TESTS, res)

def build_enrichment_variants_genes_dict_by_phenotype(dsts):
    genes_dict = filter_prb_enrichment_variants_by_phenotype(
        collect_prb_enrichment_variants_by_phenotype(dsts))
    genes_dict['unaffected'] = filter_sib_enrichment_variants_by_phenotype(
        collect_sib_enrichment_variants_by_phenotype(dsts))
    return genes_dict

def count_gene_set_enrichment_by_phenotype(genes_dict_by_pheno, gene_syms_set):
    all_res = defaultdict(dict)
    for phenotype, genes_dict in genes_dict_by_pheno.items():
        pheno_res = {}
        for test_name, gene_syms in genes_dict:
            pheno_res[test_name] = EnrichmentTestRes()

            for gene_sym_list in gene_syms:
                touched_gene_sets = False
                for gene_sym in gene_sym_list:
                    if gene_sym in gene_syms_set:
                        touched_gene_sets = True
                if touched_gene_sets:
                    pheno_res[test_name].cnt += 1
#                 else:
#                     raise Exception("this should not happend", 
#                                     gene_sym_list, gene_syms_set)
                    
        all_res[phenotype] = pheno_res
    return all_res


def count_background(gene_syms_set):
    gene_syms = get_background('enrichment_background')
    res = EnrichmentTestRes()

    for gene_sym_list in gene_syms:
        touched_gene_sets = False
        for gene_sym in gene_sym_list:
            if gene_sym in gene_syms_set:
                touched_gene_sets = True
        if touched_gene_sets:
            res.cnt += 1
    return res


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

def __count_gene_set_enrichment(var_genes_dict, gene_syms_set):
    all_res = {}
    for test_name, gene_syms in var_genes_dict:
        all_res[test_name] = EnrichmentTestRes()
        if test_name == 'BACKGROUND':
            gene_syms = get_background('enrichment_background')

        for gene_sym_list in gene_syms:
            touched_gene_sets = False
            for gene_sym in gene_sym_list:
                if gene_sym in gene_syms_set:
                    touched_gene_sets = True
            if touched_gene_sets:
                all_res[test_name].cnt += 1
#             elif test_name=='BACKGROUND':
#                 # in background we have all kinds of gene variants
#                 pass
#             else:
#                 raise Exception("this should not happend",
#                                 test_name, 
#                                 gene_sym_list, gene_syms_set)
    return all_res


def enrichment_test(dsts, gene_syms_set):

    var_genes_dict = __build_variants_genes_dict(dsts)

    all_res = __count_gene_set_enrichment(var_genes_dict, gene_syms_set)
    totals = {test_name: [len(gene_syms), gene_syms]
              for test_name, gene_syms in var_genes_dict}
    bg_total = totals['BACKGROUND'][0]

    bg_gene_set = all_res['BACKGROUND'].cnt
    if bg_gene_set == 0:
        bg_gene_set = 0.5
    bg_prob = float(bg_gene_set) / bg_total

    for test_name, gene_syms in var_genes_dict:
        res = all_res[test_name]
        total = totals[test_name][0]
        res.p_val = stats.binom_test(res.cnt, total, p=bg_prob)
        res.expected = round(bg_prob*total, 4)

    return all_res, totals

def enrichment_test_by_phenotype(dsts, gene_syms_set):
    genes_dict_by_pheno = build_enrichment_variants_genes_dict_by_phenotype(
            dsts)

    count_res_by_pheno = count_gene_set_enrichment_by_phenotype(
                            genes_dict_by_pheno, gene_syms_set)

    ###########
    count_bg = count_background(gene_syms_set)
    if count_bg.cnt == 0:
        count_bg.cnt = 0.5

    total_bg = len(get_background('enrichment_background'))
    prob_bg = float(count_bg.cnt) / total_bg
    ###########

    totals_by_pheno = {}
    for phenotype, genes_dict in genes_dict_by_pheno.items():
        totals = {testname: len(gene_syms) for testname, gene_syms in genes_dict}
        totals_by_pheno[phenotype] = totals

        all_res = count_res_by_pheno[phenotype]

        for testname, gene_syms in genes_dict:
            res = all_res[testname]
            total = totals[testname]

            res.p_val = stats.binom_test(res.cnt, total, p=prob_bg)
            res.expected = round(prob_bg * total, 4)

    return (count_res_by_pheno, totals_by_pheno,
            {phenotype: dict(genes_dict) 
             for phenotype, genes_dict in genes_dict_by_pheno.items()})



class Enrichment(object):
    pass
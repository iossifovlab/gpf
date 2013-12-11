from django.core.cache import get_cache

from DAE import vDB
import itertools


# def one_variant_per_recurrent(vs):
#     gn_sorted = sorted([[ge['sym'], v] for v in vs
#                         for ge in v.requestedGeneEffects])

#     sym_2_vars = {sym: [t[1] for t in tpi]
#                   for sym, tpi in itertools.groupby(gn_sorted,
#                                                     key=lambda x: x[0])}
#     sym_2_fn = {sym: len(set([v.familyId for v in vs]))
#                 for sym, vs in sym_2_vars.items()}

#     return [sym for sym, fn in sym_2_fn.items() if fn > 1]


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


def build_variants_genes_dict(denovo, transmitted, geneSyms=None):
    return [
        ['De novo recPrbLGDs',
         one_variant_per_recurrent(
             vDB.get_denovo_variants(denovo,
                                     inChild='prb',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        ['De novo prbLGDs',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prb',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        ['De novo prbMaleLGDs',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prbM',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        ['De novo prbFemaleLGDs',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prbF',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        ['De novo sibLGDs',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='sib',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        ['De novo sibMaleLGDs',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='sibM',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        ['De novo sibFemaleLGDs',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='sibF',
                                     effectTypes="LGDs",
                                     geneSyms=geneSyms))],
        ['De novo prbMissense',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prb',
                                     effectTypes="missense",
                                     geneSyms=geneSyms))],

        ['De novo prbMaleMissense',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prbM',
                                     effectTypes="missense",
                                     geneSyms=geneSyms))],
        ['De novo prbFemaleMissense',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prbF',
                                     effectTypes="missense",
                                     geneSyms=geneSyms))],
        ['De novo sibMissense',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='sib',
                                     effectTypes="missense",
                                     geneSyms=geneSyms))],
        ['De novo prbSynonymous',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='prb',
                                     effectTypes="synonymous",
                                     geneSyms=geneSyms))],
        ['De novo sibSynonymous',
         filter_denovo(
             vDB.get_denovo_variants(denovo,
                                     inChild='sib',
                                     effectTypes="synonymous",
                                     geneSyms=geneSyms))],
        # transmitted
        # ['UR LGDs in parents',
        #  filter_transmitted(
        #      transm.get_transmitted_summary_variants(ultraRareOnly=True,
        #                                              effectTypes="LGDs"))],
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


def init_gene_set_symbols(gene_terms, gene_set_name):
    if gene_set_name not in gene_terms.t2G:
        return (gene_set_name, set([]))
    return (gene_set_name, set(gene_terms.t2G[gene_set_name].keys()))


def init_gene_set_enrichment(var_genes_dict, gene_terms):
    all_res = {}
    for set_name in gene_terms.t2G:
        all_res[set_name] = {}
    return all_res


def count_gene_set_enrichment(all_res, var_genes_dict, gene_terms):
    for test_name, gene_syms in var_genes_dict:
        for set_name in gene_terms.t2G:
            all_res[set_name][test_name] = EnrichmentTestRes()
        for gene_sym_list in gene_syms:
            touched_gene_sets = set()
            for gene_sym in gene_sym_list:
                touched_gene_sets |= set(gene_terms.g2T[gene_sym])
            for gene_set in touched_gene_sets:
                all_res[gene_set][test_name].cnt += 1


# def __compute_q_val(pvals):
#     sorted_pvals = sorted([(set_name, p_val)
#                            for set_name, p_val in enumerate(pvals)],
#                           key=lambda x: x[1])
#     # print pvals, sorted_pvals
#     q_vals = [ip[1]*len(sorted_pvals)/(j+1)
#               for j, ip in enumerate(sorted_pvals)]
#     q_vals = [q if q<=1.0 else 1.0 for q in q_vals]
#     prev_q_val = q_vals[-1]
#     for i in xrange(len(sorted_pvals)-2, -1, -1):
#         if q_vals[i] > prev_q_val:
#             q_vals[i] = prev_q_val
#         else:
#             prev_q_val = q_vals[i]
#     return [q for d, q in sorted(zip(sorted_pvals, q_vals),
#                                  key=lambda x: x[0][0])]


def enrichment_test(var_genes_dict, gene_terms):
    all_res = init_gene_set_enrichment(var_genes_dict, gene_terms)
    count_gene_set_enrichment(all_res, var_genes_dict, gene_terms)

    totals = {test_name: len(gene_syms)
              for test_name, gene_syms in var_genes_dict}
    bg_total = totals['BACKGROUND']

    for gene_set in gene_terms.t2G:
        bg_gene_set = all_res[gene_set]['BACKGROUND'].cnt
        if bg_gene_set == 0:
            bg_gene_set = 0.5
        bg_prob = float(bg_gene_set) / bg_total

        for test_name, gene_syms in var_genes_dict:
            res = all_res[gene_set][test_name]
            total = totals[test_name]
            res.p_val = stats.binom_test(res.cnt, total, p=bg_prob)
            res.expected = round(bg_prob*total, 4)

    # for test_name, gene_syms in var_genes_dict:
    #     gset_pvals = [(gset, gset_res[test_name].p_val)
    #                   for gset, gset_res in all_res.items()]
    #     # print test_name, gset_pvals

    #     q_vals = __compute_q_val([p[1] for p in gset_pvals])
    #     for a, q in zip(gset_pvals, q_vals):
    #         all_res[a[0]][test_name].q_val = q

    return all_res, totals

from DAE import giDB


def main():
    dsts = vDB.get_studies('allWE')
    tsts = vDB.get_study('w873e374s322')
    var_genes_dict = build_variants_genes_dict(dsts, tsts)
    gene_terms = giDB.getGeneTerms('main')

    return (var_genes_dict, gene_terms)


def print_summary_table(var_genes_dict, geneTerms, allRes, totals):
    tests = [tn for tn, vs in var_genes_dict if tn != "BACKGROUND"]
    print "\t\t\tBACKGROUND (UR syn.)\t\t" + "\t\t\t\t\t".join(tests)
    bg_total = totals['BACKGROUND']
    hcols = []
    hcols.extend(("setId",
                  "setDesc",
                  "GeneNumber",
                  "Overlap (" + str(bcgTotal) + ")",
                  "proportion"))

    for test_name in tests:
        hcols.extend(("Overlap (" + str(totals[test_name]) + ")",
                      "Expected",
                      "pVal",
                      "lessOrMore"))
    print "\t".join(hcols)
    for s in geneTerms.t2G:
        cols = []
        bcgCnt = allRes[s]['BACKGROUND'].cnt
        bcgProp = str(round(float(bcgCnt) / bg_total, 3))
        cols.extend((s,
                     geneTerms.tDesc[s],
                     str(len(geneTerms.t2G[s])),
                     str(bcgCnt),
                     bcgProp))

        for test_name in tests:
            res = allRes[s][test_name]

            if res.pVal >= 0.0001:
                pVal = str(round(res.pVal, 4))
            else:
                pVal = str('%.1E' % (res.pVal))

            # if res.qVal >= 0.0001:
            #     qVal = str(round(res.qVal, 4))
            # else:
            #     qVal = str('%.1E' % (res.qVal))

            expected = str(round(res.expected, 4))

            if res.cnt > res.expected:
                lessmore = "more"
            elif res.cnt < res.expected:
                lessmore = "less"
            else:
                lessmore = "equal"
            cols.extend((str(res.cnt), expected, pVal, lessmore))
        print "\t".join(cols)
        break

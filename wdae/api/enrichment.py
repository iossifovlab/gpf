from DAE import vDB
import itertools


def one_variant_per_recurrent(vs):
    gn = [[ge['sym'], v] for v in vs for ge in v.requestedGeneEffects]
    gn_sorted = sorted(gn)

    sym_2_vars = {sym: [t[1] for t in tpi]
                  for sym, tpi in itertools.groupby(gn_sorted,
                                                    key=lambda x: x[0])}
    sym_2_fn = {sym: len(set([v.familyId for v in vs]))
                for sym, vs in sym_2_vars.items()}

    return [sym for sym, fn in sym_2_fn.items() if fn > 1]


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


def build_var_genes_dict(dnv, transm):
    return [
        ['De novo recPrbLGDs',
         one_variant_per_recurrent(
             vDB.get_denovo_variants(dnv,
                                     inChild='prb',
                                     effectTypes="LGDs"))],
        ['De novo prbLGDs',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='prb',
                                     effectTypes="LGDs"))],
        ['De novo prbMaleLGDs',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='prbM',
                                     effectTypes="LGDs"))],
        ['De novo prbFemaleLGDs',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='prbF',
                                     effectTypes="LGDs"))],
        ['De novo sibLGDs',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='sib',
                                     effectTypes="LGDs"))],
        ['De novo sibMaleLGDs',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='sibM',
                                     effectTypes="LGDs"))],
        ['De novo sibFemaleLGDs',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='sibF',
                                     effectTypes="LGDs"))],
        ['De novo prbMissense',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='prb',
                                     effectTypes="missense"))],

        ['De novo prbMaleMissense',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='prbM',
                                     effectTypes="missense"))],
        ['De novo prbFemaleMissense',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='prbF',
                                     effectTypes="missense"))],
        ['De novo sibMissense',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='sib',
                                     effectTypes="missense"))],
        ['De novo prbSynonymous',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='prb',
                                     effectTypes="synonymous"))],
        ['De novo sibSynonymous',
         filter_denovo(
             vDB.get_denovo_variants(dnv,
                                     inChild='sib',
                                     effectTypes="synonymous"))],
        # transmitted
        ['UR LGDs in parents',
         filter_transmitted(
             transm.get_transmitted_summary_variants(ultraRareOnly=True,
                                                     effectTypes="LGDs"))],
        ['BACKGROUND',
         filter_transmitted(
             transm.get_transmitted_summary_variants(ultraRareOnly=True,
                                                     effectTypes="synonymous"))]
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
            all_res[set_name][test_name].cnt = 0
        for gene_sym_list in gene_syms:
            touched_gene_sets = set()
            for gene_sym in gene_sym_list:
                touched_gene_sets |= set(gene_terms.g2T[gene_sym])
            for gene_set in touched_gene_sets:
                all_res[gene_set][test_name].cnt += 1


def __compute_q_val(pvals):
    sorted_pvals = sorted([(set_name, p_val)
                           for set_name, p_val in enumerate(pvals)],
                          key=lambda x: x[1])
    # print pvals, sorted_pvals
    q_vals = [ip[1]*len(sorted_pvals)/(j+1)
              for j, ip in enumerate(sorted_pvals)]
    q_vals = [q if q<=1.0 else 1.0 for q in q_vals]
    prev_q_val = q_vals[-1]
    for i in xrange(len(sorted_pvals)-2, -1, -1):
        if q_vals[i] > prev_q_val:
            q_vals[i] = prev_q_val
        else:
            prev_q_val = q_vals[i]
    return [q for d, q in sorted(zip(sorted_pvals, q_vals),
                                 key=lambda x: x[0][0])]


def enrichment_test(var_genes_dict, gene_terms):
    all_res = __init_gene_set_enrichment(var_genes_dict, gene_terms)
    __count_gene_set_enrichment(all_res, var_genes_dict, gene_terms)

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

    for test_name, gene_syms in var_genes_dict:
        gset_pvals = [(gset, gset_res[test_name].p_val)
                      for gset, gset_res in all_res.items()]
        # print test_name, gset_pvals

        q_vals = __compute_q_val([p[1] for p in gset_pvals])
        for a, q in zip(gset_pvals, q_vals):
            all_res[a[0]][test_name].q_val = q

    return all_res, totals

from DAE import giDB


def main():
    dsts = vDB.get_studies('allWE')
    tsts = vDB.get_study('wig781')
    var_genes_dict = build_var_genes_dict(dsts, tsts)
    gene_terms = giDB.getGeneTerms('main')

    return (var_genes_dict, gene_terms)

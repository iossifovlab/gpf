'''
Created on Nov 16, 2015

@author: lubo
'''
import itertools
from query_variants import dae_query_variants
from collections import Counter
from query_prepare import prepare_denovo_studies
from api.query.wdae_query_variants import wdae_handle_gene_sets


EFFECT_TYPE_GROUPS = [
    ('LGDs', 'rec'),
    ('missense', None),
    ('synonymous', None),
    ('CNV+,CNV-', None),
]


def _filter_one_var_per_gene_per_child(vs):
    ret = []
    seen = set()
    for v in vs:
        vKs = {v.familyId + "." + ge['sym'] for ge in v.requestedGeneEffects}
        if seen & vKs:
            continue
        ret.append(v)
        seen |= vKs
    return ret


def _filter_var_in_recurent_genes(vs):
    gnSorted = sorted([[ge['sym'], v]
                       for v in vs for ge in v.requestedGeneEffects])
    sym2Vars = {sym: [t[1] for t in tpi] for sym, tpi
                in itertools.groupby(gnSorted, key=lambda x: x[0])}
    sym2FN = {sym: len(set([v.familyId for v in vs]))
              for sym, vs in sym2Vars.items()}
    recGenes = {sym for sym, FN in sym2FN.items() if FN > 1}
    return [v for v in vs
            if {ge['sym'] for ge in v.requestedGeneEffects} & recGenes]


def _pheno_query_variants(data, effect_type):
    wdae_handle_gene_sets(data)
    data['effectTypes'] = effect_type

    vsl = dae_query_variants(data)
    vs = itertools.chain(*vsl)
    return _filter_one_var_per_gene_per_child(vs)


def family_pheno_query_variants(data):
    res = {}
    for (effect_type, recurrent) in EFFECT_TYPE_GROUPS:
        vs = _pheno_query_variants(data, effect_type)
        res[effect_type] = vs
        if recurrent:
            effect_type_rec = "{}.Rec".format(effect_type)
            res[effect_type_rec] = _filter_var_in_recurent_genes(vs)

    families = {}
    for (k, vs) in res.items():
        families[k] = Counter([v.familyId for v in vs])

    return families


def prepare_families_gender_data(data):
    stds = prepare_denovo_studies(data)
    prbs_gender = {fmid: pd.gender for st in stds
                   for fmid, fd in st.families.items()
                   for pd in fd.memberInOrder if pd.role == 'prb'}

    return prbs_gender

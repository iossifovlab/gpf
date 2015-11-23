'''
Created on Nov 16, 2015

@author: lubo
'''
import itertools
from query_variants import dae_query_variants
from collections import Counter
from api.query.wdae_query_variants import wdae_handle_gene_sets
import numpy as np
from scipy.stats import ttest_ind


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
    data['denovoStudies'] = 'ALL SSC'

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


def pheno_merge_data(variants, gender, nm):
    yield tuple(['family_id', 'gender', 'LGDs', 'recLGDs', 'missense',
                 'synonymous', 'CNV', nm.measure, 'age',
                 'non_verbal_iq', nm.formula])
    for fid, gender in gender.items():
        vals = nm.df[nm.df.family_id == int(fid)]
        if len(vals) == 1:
            m = vals[nm.measure].values[0]
            v = vals.normalized.values[0]
            a = vals['age'].values[0]
            nviq = vals['non_verbal_iq'].values[0]
        else:
            m = np.NaN
            v = np.NaN
            a = np.NaN
            nviq = np.NaN
        row = [
            fid,
            gender,
            variants['LGDs'].get(fid, 0),
            variants['LGDs.Rec'].get(fid, 0),
            variants['missense'].get(fid, 0),
            variants['synonymous'].get(fid, 0),
            variants['CNV+,CNV-'].get(fid, 0),
            a,
            nviq,
            m,
            v
        ]
        yield tuple(row)


def pheno_calc(ps):
    ps.next()  # skip column names
    rows = [tuple([e if e != 'NA' else np.NaN for e in p]) for p in ps]
    dtype = np.dtype([('fid', 'S10'),
                      ('gender', 'S1'),
                      ('LGDs', '<i4'),
                      ('recLGDs', '<i4'),
                      ('missense', '<i4'),
                      ('synonymous', '<i4'),
                      ('CNV', '<i4'),
                      ('age', 'f'),
                      ('non_verbal_iq', 'f'),
                      ('measure', 'f'),
                      ('value', 'f')])
    data = np.array(rows, dtype=dtype)
    data = data[~np.isnan(data['value'])]
    res = []

    for (effect_type, gender) in itertools.product(
            *[['LGDs', 'recLGDs', 'missense', 'synonymous', 'CNV'],
              ['M', 'F']]):

        positive = data[np.logical_and(data['gender'] == gender,
                                       data[effect_type] == 1)]['value']
        negative = data[np.logical_and(data['gender'] == gender,
                                       data[effect_type] == 0)]['value']
        p_count = len(positive)
        if p_count == 0:
            p_mean = 0
            p_std = 0
        else:
            p_mean = np.mean(positive, dtype=np.float64)
            p_std = 1.96 * \
                np.std(positive, dtype=np.float64) / np.sqrt(len(positive))

        n_count = len(negative)
        if n_count == 0:
            n_mean = 0
            n_std = 0
        else:
            n_mean = np.mean(negative, dtype=np.float64)
            n_std = 1.96 * \
                np.std(negative, dtype=np.float64) / np.sqrt(len(negative))
        if n_count == 0 or p_count == 0:
            pv = 'NA'
        else:
            pv = calc_pv(positive, negative)

        res.append((effect_type, gender, n_mean, n_std, p_mean, p_std, pv))
    return res


def calc_pv(positive, negative):
    pv = ttest_ind(positive, negative)[1]
    if pv >= 0.1:
        return "%.1f" % (pv)
    if pv >= 0.01:
        return "%.2f" % (pv)
    if pv >= 0.001:
        return "%.3f" % (pv)
    if pv >= 0.0001:
        return "%.4f" % (pv)
    return "%.5f" % (pv)

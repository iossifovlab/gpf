'''
Created on Nov 16, 2015

@author: lubo
'''
import itertools
from query_variants import dae_query_families_with_variants
from collections import Counter
from api.query.wdae_query_variants import wdae_handle_gene_sets
import numpy as np
from scipy.stats import ttest_ind


EFFECT_TYPE_GROUPS = [
    'LGDs',
    'missense',
    'synonymous',
    'CNV+,CNV-',
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


def _pheno_query_variants(data, effect_type):
    wdae_handle_gene_sets(data)
    data['effectTypes'] = effect_type
    data['inChild'] = 'prb'

    families = dae_query_families_with_variants(data)
    return families


def family_pheno_query_variants(data):
    data['denovoStudies'] = 'ALL SSC'
    data['transmittedStudies'] = 'w1202s766e611'
    if 'presentInParent' not in data or \
            data['presentInParent'] is None or \
            data['presentInParent'] == 'neither':

        del data['transmittedStudies']

    families = {}
    for effect_type in EFFECT_TYPE_GROUPS:
        fams = _pheno_query_variants(data, effect_type)
        families[effect_type] = Counter([fid for fid in fams])

    return families


def build_narray(ps):
    ps.next()  # skip column names
    rows = []
    for p in ps:
        rows.append(tuple([e if e != 'NA' else np.NaN for e in p]))

    dtype = np.dtype([('fid', 'S10'),
                      ('gender', 'S10'),
                      ('LGDs', 'f'),
                      ('missense', 'f'),
                      ('synonymous', 'f'),
                      ('CNV', 'f'),
                      ('measure', 'f'),
                      ('age', 'f'),
                      ('non_verbal_iq', 'f'),
                      ('value', 'f')])
    data = np.array(rows, dtype=dtype)
    data = data[~np.isnan(data['value'])]
    return data


def pheno_calc(ps):
    data = build_narray(ps)
    res = []

    for (effect_type, gender) in itertools.product(
            *[['LGDs', 'missense', 'synonymous', 'CNV'],
              ['M', 'F']]):

        gender_index = data['gender'] == gender
        positive_index = np.logical_and(data[effect_type] != 0,
                                        ~np.isnan(data[effect_type]))
        positive_gender_index = np.logical_and(positive_index, gender_index)

        negative_index = data[effect_type] == 0
        # negative_index = ~np.isnan(data[effect_type])
        negative_gender_index = np.logical_and(negative_index,
                                               gender_index)

        assert not np.any(np.logical_and(positive_gender_index,
                                         negative_gender_index))

        positive = data[positive_gender_index]['value']
        negative = data[negative_gender_index]['value']

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

        res.append((effect_type, gender,
                    n_mean, n_std, p_mean, p_std, pv,
                    p_count, n_count))
    return res


def calc_pv(positive, negative):
    if len(positive) < 2 or len(negative) < 2:
        return 'NA'
    tt = ttest_ind(positive, negative)
    pv = tt[1]
    if np.isnan(pv):
        return "NA"
    if pv >= 0.1:
        return "%.1f" % (pv)
    if pv >= 0.01:
        return "%.2f" % (pv)
    if pv >= 0.001:
        return "%.3f" % (pv)
    if pv >= 0.0001:
        return "%.4f" % (pv)
    return "%.5f" % (pv)

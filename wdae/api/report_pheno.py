import itertools
import logging

from DAE import phDB
from api.studies import get_denovo_studies_names
from query_variants import dae_query_variants

from query_prepare import prepare_denovo_studies, \
    combine_gene_syms, prepare_string_value

from collections import Counter
import numpy as np
from scipy.stats import ttest_ind, nanmean, nanstd

logger = logging.getLogger(__name__)
SUPPORTED_PHENO_STUDIES = {'combSSCWE', 'cshlSSCWE', 'yaleSSCWE', 'udapSSCWE'}

def get_supported_measures():
    return [('vIQ', 'verbal IQ'),
            ('NvIQ', 'non-verbal IQ')]

def get_supported_studies():
    stds = get_denovo_studies_names()
    return [(key, desc) for (key, desc) in stds if key in SUPPORTED_PHENO_STUDIES]

def filter_one_var_per_gene_per_child(vs):
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
    data['effectTypes'] = effect_type
    vsl = dae_query_variants(data)
    vs = itertools.chain(*vsl)
    return filter_one_var_per_gene_per_child(vs)
    
def pheno_query_variants(data):
    lgds = _pheno_query_variants(data, 'LGDs')
    missense = _pheno_query_variants(data, 'missense')
    synonymous = _pheno_query_variants(data, 'synonymous')

    families_with_lgds = Counter([v.familyId for v in lgds])
    families_with_missense = Counter([v.familyId for v in missense])
    families_with_synonymous = Counter([v.familyId for v in synonymous])

    return (families_with_lgds,
            families_with_missense,
            families_with_synonymous)


def pheno_prepare_families_data(data):
    stds = prepare_denovo_studies(data)
    all_families = {fid:prb_gender(family) for st in stds
                    for fid, family in st.families.items()}
    seq_prbs = {fmid:pd.gender for st in stds
                for fmid, fd in st.families.items()
                for pd in fd.memberInOrder if pd.role=='prb'}
    
    return seq_prbs, all_families
    
    
def prb_gender(fms):
    prb_inds = [ind for ind, prsn in enumerate(fms.memberInOrder) if prsn.role=='prb']
    if len(prb_inds)!=1:
        return '?'
    else:
        return fms.memberInOrder[prb_inds[0]].gender

def pheno_query(data):
    (families_with_lgds,
     families_with_missense,
     families_with_synonymous) = pheno_query_variants(data)
    seq_prbs, all_families = pheno_prepare_families_data(data)

    (measure_name, measure) = prepare_pheno_measure(data)

    yield ['family id', 'gender', 'LGDs', 'missense', 'synonymous', measure_name]
    for fid, gender in seq_prbs.items():
        row = (
            fid,
            gender,
            1 if fid in families_with_lgds else 0,
            1 if fid in families_with_missense else 0,
            1 if fid in families_with_synonymous else 0,
            measure[fid] if fid in measure else np.NaN)
        yield row

def prepare_pheno_measure(data):
    if 'measure' not in data:
        logger.error("no measure name in request. returning NvIQ")
        return ('NvIQ', get_non_verbal_iq())
    measure = data['measure']
    if measure =='NvIQ':
        return ('NvIQ', get_non_verbal_iq())
    elif measure == 'vIQ':
        return ('vIQ', get_verbal_iq())
    else:
        logger.error("strange measure name (%s) in request. returning NvIQ" % measure)
        return ('NvIQ', get_non_verbal_iq())

def get_pheno_measure(measure_name, conv_func=str):
    str_dict = dict(zip(phDB.families,phDB.get_variable(measure_name)))
    res_dict = {}
    for f,m in str_dict.items():
        try:
            res_dict[f] = conv_func(m)
        except:
            pass 
    return res_dict

def get_verbal_iq():
    return get_pheno_measure("pcdv.ssc_diagnosis_verbal_iq", float)

def get_non_verbal_iq():
    return get_pheno_measure("pcdv.ssc_diagnosis_nonverbal_iq", float)


def calc_pv(positive, negative):
    pv = ttest_ind(positive, negative)[1]
    if pv >= 0.1:
        return "%.1f" % (pv) 
    if pv >= 0.01:
        return "%.2f" % (pv) 
    if pv >= 0.001:
        return "%.3f" % (pv) 
    if pv >= 0.0001:
        return "%.3f" % (pv) 
    return "%.5f" % (pv) 

def pheno_calc(ps):
    ps.next() # skip column names
    rows = [p for p in ps]
    dtype = np.dtype([('fid', 'S10'),
                      ('gender', 'S1'),
                      ('LGDs', '<i4'),
                      ('missense', '<i4'),
                      ('synonymous', '<i4'),
                      ('m', 'f')])
    data = np.array(rows, dtype=dtype)
    data = data[~np.isnan(data['m'])]
    res = []
    
    for (effect_type, gender) in itertools.product(*[['LGDs', 'missense', 'synonymous'],
                                                     ['M', 'F']]):
        
        positive = data[np.logical_and(data['gender'] == gender,
                                       data[effect_type] == 1)]['m']
        negative = data[np.logical_and(data['gender'] == gender,
                                       data[effect_type] == 0)]['m']
        p_mean = np.mean(positive, dtype=np.float64)
        n_mean = np.mean(negative, dtype=np.float64)
        p_std = 1.96 * np.std(positive, dtype=np.float64)/np.sqrt(len(positive))
        n_std = 1.96 * np.std(negative, dtype=np.float64)/np.sqrt(len(negative))
        pv = calc_pv(positive, negative)

        res.append((effect_type, gender, n_mean, n_std, p_mean, p_std, pv))
    return res
        
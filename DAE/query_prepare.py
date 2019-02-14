import itertools
import logging
from DAE import vDB
import operator


from __builtin__ import str
from VariantsDB import Study

LOGGER = logging.getLogger(__name__)


def __load_text_column(colSpec):
    cn = 0
    sepC = "\t"
    header = 0
    cs = colSpec.split(',')
    fn = cs[0]
    if len(cs) > 1:
        cn = int(cs[1])
    if len(cs) > 2:
        sepC = cs[2]
    if len(cs) > 3:
        header = int(cs[3])
    f = open(fn)
    if header == 1:
        f.readline()

    r = []
    for l in f:
        cs = l.strip().split(sepC)
        r.append(cs[cn])
    f.close()
    return r


def prepare_string_value(data, key):
    if key not in data or not data[key]:
        return None
    result = data[key]
    if isinstance(result, list):
        result = ",".join(result)

    res = str(result).strip()
    if res == 'null' or res == 'Null' or res == 'None' or res == 'none':
        return None
    return res


def prepare_gene_syms(data):
    if 'geneSyms' not in data and 'geneSym' not in data:
        return None

    if 'geneSyms' in data and data['geneSyms'] is not None:
        gene_sym = data['geneSyms']
        if isinstance(gene_sym, list):
            gene_sym = ",".join(gene_sym)
    elif 'geneSym' in data and data['geneSym'] is not None:
        gene_sym = data['geneSym']
    elif 'geneSymFile' in data and data['geneSymFile']:
        gene_sym = __load_text_column(data['geneSymFile'])
    else:
        return None

    if isinstance(gene_sym, list):
        gl = gene_sym
        return set(gl)

    if isinstance(gene_sym, set):
        return gene_sym

    elif isinstance(gene_sym, str) or isinstance(gene_sym, unicode):
        gl = [s.strip()
              for s in str(gene_sym).replace(',', ' ').split()
              if len(s.strip()) > 0]
        if not gl:
            return None
        return set(gl)
    else:
        print('bad gene syms type: %s' % type(gene_sym))
        return None


def prepare_gene_ids(data):
    if 'geneId' not in data and 'geneIdFile' not in data:
        return None
    if 'geneId' in data and data['geneId']:
        return set([s.strip() for s in data['geneId'].split(',')
                    if len(s.strip()) > 0])
    elif 'geneIdFile' in data and data['geneIdFile']:
        return set(__load_text_column(data['geneIdFile']))
    else:
        return None


def prepare_denovo_phenotype_gender_filter1(data, st):
    study_pheno_type = st.get_attr('study.phenotype')
    study_type = st.get_attr('study.type')

    pheno_types = data['phenoType']
    if 'studyType' in data:
        study_types = data['studyType']
    else:
        study_types = set(['WE', 'TG', 'CNV'])

    pheno_filter = []
    if study_pheno_type in pheno_types and study_type in study_types:
        pheno_filter.append('affected only')
        pheno_filter.append('affected and unaffected')

    if 'unaffected' in pheno_types and study_type in study_types:
        pheno_filter.append('unaffected only')
        pheno_filter.append('autism and unaffected')
    pheno_filter = list(set(pheno_filter))

    if not pheno_filter:
        return None

    if len(pheno_filter) == 1:
        return pheno_filter[0]
    return pheno_filter


def prepare_denovo_study_type(data):
    if 'studyType' not in data:
        return

    study_type = data['studyType']
    if study_type is None or study_type.lower() == 'none':
        del data['studyType']
        return

    study_type = [st for st in data['studyType'].split(',')
                  if st in set(['WE', 'TG', 'CNV'])]
    if study_type:
        data['studyType'] = set(study_type)
    else:
        del data['studyType']


def prepare_denovo_phenotype(data):
    if 'phenoType' not in data:
        return

    phenoType = data['phenoType']

    if phenoType is None or not phenoType:
        del data['phenoType']
        return

    if isinstance(phenoType, list):
        phenoType = ','.join(phenoType)
    if isinstance(phenoType, str) or isinstance(phenoType, unicode):
        phenoType = set(str(phenoType).split(','))
    elif isinstance(phenoType, list):
        phenoType = set([str(pt) for pt in phenoType])
    data['phenoType'] = phenoType


def prepare_gender_filter(data):
    if 'gender' not in data:
        return None
    genderFilter = data['gender']

    if isinstance(genderFilter, str) or isinstance(genderFilter, unicode):
        genderFilter = str(data['gender']).split(',')
        res = []
        if 'female' in genderFilter:
            res.append('F')
        if 'male' in genderFilter:
            res.append('M')
        if len(res) == 1:
            data['gender'] = res
            return res
        else:
            del data['gender']
            return None
    else:
        if len(genderFilter) != 1:
            del data['gender']
            return None
        return genderFilter


def prepare_denovo_studies(data):
    if 'denovoStudies' not in data:
        return None

    dl = data['denovoStudies']
    if isinstance(dl, list):
        if all([isinstance(s, Study) for s in dl]):
            dst = [dl]
        else:
            dst = [vDB.get_studies(str(d)) for d in dl]
    else:
        dst = [vDB.get_studies(str(dl))]

    flatten = itertools.chain.from_iterable(dst)
    res = [st for st in flatten if st is not None]
    if not res:
        return None

    return res


def prepare_denovo_pheno_filter(data, dstudies):
    if 'phenoType' not in data:
        return [(st, None) for st in dstudies]

    res = []
    for st in dstudies:
        f = prepare_denovo_phenotype_gender_filter1(data, st)
        if not f:
            continue
        res.append((st, {'presentInChild': f}))

    return res


def prepare_transmitted_studies(data):
    if 'transmittedStudies' not in data and 'transmittedStudy' not in data:
        return None

    if 'transmittedStudies' in data:
        tl = data['transmittedStudies']
    else:
        tl = data['transmittedStudy']

    if isinstance(tl, list):
        if all([isinstance(s, Study) for s in tl]):
            tst = [tl]
        else:
            tst = [vDB.get_studies(str(d)) for d in tl]
    else:
        tst = [vDB.get_studies(str(tl))]

    flatten = itertools.chain.from_iterable(tst)
    res = [st for st in flatten if st is not None]
    if not res:
        return None

    return res


def prepare_ssc_filter(data):
    if 'presentInParent' not in data:
        data['presentInParent'] = 'neither'

    if 'presentInChild' not in data:
        data['presentInChild'] = 'neither'

    if data['presentInParent'] == 'neither':
        data['transmittedStudies'] = 'None'
    else:
        data['transmittedStudies'] = 'w1202s766e611'

    if data['presentInChild'] == 'neither':
        data['denovoStudies'] = 'None'
    else:
        data['denovoStudies'] = 'ALL SSC'

    if 'phenoType' in data:
        del data['phenoType']

    return data

EFFECT_TYPES = {
    "Nonsense": ["nonsense"],
    "Frame-shift": ["frame-shift"],
    "Splice-site": ["splice-site"],
    "Missense": ["missense"],
    "No-frame-shift": ["no-frame-shift"],
    "noStart": ["noStart"],
    "noEnd": ["noEnd"],
    "Synonymous": ["synonymous"],
    "Non coding": ["non-coding"],
    "Intron": ["intron"],
    "Intergenic": ["intergenic"],
    "3'-UTR": ["3'UTR", "3'UTR-intron"],
    "5'-UTR": ["5'UTR", "5'UTR-intron"],
    "CNV": ["CNV+", "CNV-"],

}


EFFECT_GROUPS = {
    "coding": [
        "Nonsense",
        "Frame-shift",
        "Splice-site",
        "Missense",
        "No-frame-shift",
        "noStart",
        "noEnd",
        "Synonymous",
    ],
    "noncoding": [
        "Non coding",
        "Intron",
        "Intergenic",
        "3'-UTR",
        "5'-UTR",
    ],
    "cnv": [
        "CNV+",
        "CNV-"
    ],
    "lgds": [
        "Nonsense",
        "Frame-shift",
        "Splice-site",
    ],
    "nonsynonymous": [
        "Nonsense",
        "Frame-shift",
        "Splice-site",
        "Missense",
        "No-frame-shift",
        "noStart",
        "noEnd",
    ],
    "utrs": [
        "3'-UTR",
        "5'-UTR",
    ]

}


def build_effect_types_list(effects):
    result_effects = reduce(
        operator.add,
        [EFFECT_TYPES[str(et)] if et in EFFECT_TYPES else [str(et)] for
         et in effects])
    return result_effects


def build_effect_types(effects):
    result_effects = build_effect_types_list(effects)
    return ','.join(result_effects)


def build_effect_type_filter(data):
    if "effectTypes" not in data:
        return
    effects_string = data['effectTypes']
    if effects_string is None:
        return
    if isinstance(effects_string, list):
        effects_string = ','.join(effects_string)
    if isinstance(effects_string, str) or isinstance(effects_string, unicode):
        effects = effects_string.split(',')
        result_effects = build_effect_types(effects)
    elif isinstance(effects_string, list):
        result_effects = build_effect_types([str(ef) for ef in effects_string])
    data["effectTypes"] = result_effects

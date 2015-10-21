import itertools
import logging
from DAE import get_gene_sets_symNS, vDB
from api.dae_query import combine_denovo_gene_sets

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
    if key not in data or not data[key] \
       or not data[key].strip():
        return None
    res = data[key].strip()
    if res == 'null' or res == 'Null' or res == 'None' or res == 'none':
        return None
    return res


def prepare_gene_syms(data):
    if 'geneSyms' not in data and 'geneSym' not in data:
        return None

    if 'geneSyms' in data and data['geneSyms']:
        gene_sym = data['geneSyms']
    elif 'geneSym' in data and data['geneSym']:
        gene_sym = data['geneSym']
    elif 'geneSymFile' in data and data['geneSymFile']:
        gene_sym = __load_text_column(data['geneSymFile'])
    else:
        return None

    if isinstance(gene_sym, list):
        gl = gene_sym
        if not gl:
            return None
        else:
            return set(gl)

    elif isinstance(gene_sym, str):
        gl = [s.strip()
              for s in gene_sym.replace(',', ' ').split()
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


def gene_set_loader2(gene_set_label, gene_set_phenotype=None):

    gene_term = None
    if gene_set_label != 'denovo':
        gene_term = get_gene_sets_symNS(gene_set_label)
    else:
        gene_term = combine_denovo_gene_sets(gene_set_phenotype)

    return gene_term


def prepare_gene_sets(data):
    if 'geneSet' not in data or not data['geneSet'] or \
            not data['geneSet'].strip():
        return None

    if 'geneTerm' not in data or not data['geneTerm'] or \
            not data['geneTerm'].strip():
        return None

    gene_set = data['geneSet']
    gene_term = data['geneTerm']

    gene_set_phenotype = data['gene_set_phenotype'] \
        if 'gene_set_phenotype' in data else None

    gt = gene_set_loader2(gene_set, gene_set_phenotype)

    if gt and gene_term in gt.t2G:
            return set(gt.t2G[gene_term].keys())

    return None


def prepare_denovo_phenotype_gender_filter1(data, st):
    study_pheno_type = st.get_attr('study.phenotype')
    study_type = st.get_attr('study.type')

    pheno_types = data['phenoType']
    if 'studyType' in data:
        study_types = data['studyType']
    else:
        study_types = set(['WE', 'TG', 'CNV'])

    gender = None
    if 'gender' in data:
        gender = data['gender']

    pheno_filter = []

    if study_pheno_type in pheno_types and study_type in study_types:
        pf = lambda inCh: len(inCh) > 0 and inCh[0] == 'p'
        if ['F'] == gender:
            pf = lambda inCh: 'prbF' in inCh
        elif ['M'] == gender:
            pf = lambda inCh: 'prbM' in inCh
        pheno_filter.append(pf)

    if 'unaffected' in pheno_types and study_type in study_types:
        pf = lambda inCh: ('sib' in inCh)
        if ['F'] == gender:
            pf = lambda inCh: 'sibF' in inCh
        elif ['M'] == gender:
            pf = lambda inCh: 'sibM' in inCh
        pheno_filter.append(pf)

    if not pheno_filter:
        return None

    if len(pheno_filter) == 1:
        return pheno_filter[0]
    return lambda inCh: any([f(inCh) for f in pheno_filter])


def prepare_denovo_study_type(data):
    if 'studyType' not in data:
        return

    study_type = data['studyType']
    if study_type is None or study_type.lower() == 'none':
        del data['studyType']

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

    if phenoType is None or phenoType.lower() == 'none':
        del data['phenoType']
        return

    phenoType = set(data['phenoType'].split(','))
    data['phenoType'] = phenoType


def prepare_gender_filter(data):
    if 'gender' in data:
        genderFilter = data['gender'].split(',')
        res = []
        if 'female' in genderFilter:
            res.append('F')
        if 'male' in genderFilter:
            res.append('M')
        if res:
            data['gender'] = res
        else:
            del data['gender']


def prepare_denovo_studies(data):
    if 'denovoStudies' not in data:
        return None

    dl = data['denovoStudies']
    if isinstance(dl, list):
        dst = [vDB.get_studies(str(d)) for d in dl]
    else:
        dst = [vDB.get_studies(str(dl))]

    flatten = itertools.chain.from_iterable(dst)
    res = [st for st in flatten if st is not None]
    if not res:
        return None

    return res


def prepare_denovo_pheno_filter(data, dstudies):
    if 'phenoType' not in data or 'gender' not in data:
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
        tst = [vDB.get_studies(str(t)) for t in tl]
    else:
        tst = [vDB.get_studies(str(tl))]

    flatten = itertools.chain.from_iterable(tst)
    res = [st for st in flatten if st is not None]
    if not res:
        return None

    return res


def combine_gene_syms(data):
    gene_syms = prepare_gene_syms(data)
    gene_sets = prepare_gene_sets(data)

    if gene_syms is None:
        return gene_sets
    else:
        if gene_sets is None:
            return gene_syms
        else:
            return gene_sets.union(gene_syms)


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

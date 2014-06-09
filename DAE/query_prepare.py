import itertools
import logging
from DAE import get_gene_sets_symNS, vDB
from bg_loader import get_background

logger = logging.getLogger(__name__)


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
        gl = [s.strip() for s in gene_sym.split(',') if len(s.strip()) > 0]
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


def gene_set_loader(gene_set_label, study_name=None):
    print("gene set label: %s" % gene_set_label)

    if 'denovo' == gene_set_label:
        dsts = vDB.get_studies(study_name)
        gene_term = get_gene_sets_symNS(gene_set_label, dsts)
    else:
        gene_term = get_background(gene_set_label)
        if not gene_term:
            gene_term = get_gene_sets_symNS(gene_set_label)

    return gene_term


def gene_set_bgloader(gene_set_label):
    print("gene set label: %s" % gene_set_label)

    if 'denovo' == gene_set_label:
        pass
    else:
        gene_term = get_gene_sets_symNS(gene_set_label)

    return gene_term


def __load_gene_set(gene_set, gene_term, gene_study,
                    gene_set_loader=gene_set_loader):

    if 'denovo' == gene_set:
        if not gene_study:
            return None
        gs = gene_set_loader('denovo', gene_study)
    else:
        gs = gene_set_loader(gene_set)

    if gene_term not in gs.tDesc:
        return None

    gl = gs.t2G[gene_term].keys()

    if not gl:
        return None

    return set(gl)


def __prepare_cli_gene_sets(data):
    gene_set = data['geneSet'].strip()
    if ":" in gene_set:
        ci = gene_set.index(":")
        collection = gene_set[0:ci]
        setId = gene_set[ci+1:]
    else:
        collection = "main"
        setId = gene_set
    if collection.lower() == 'denovo':
        study = data['denovoStudies']
    else:
        study = None
    return (collection, setId, study)


def __prepare_web_gene_sets(data):
    gene_set = data['geneSet']
    gene_term = data['geneTerm']
    gene_study = data['geneStudy'] if 'geneStudy' in data else None
    return (gene_set, gene_term, gene_study)


def prepare_gene_sets(data, gene_set_loader=gene_set_loader):
    if 'geneSet' not in data or not data['geneSet'] or not data['geneSet'].strip():
        return None

    if 'geneTerm' in data:
        # web interface
        (gene_set, gene_term, gene_study) = __prepare_web_gene_sets(data)
    else:
        # CLI
        (gene_set, gene_term, gene_study) = __prepare_cli_gene_sets(data)

    return __load_gene_set(gene_set, gene_term, gene_study,
                           gene_set_loader)


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


def combine_gene_syms(data, gene_set_loader=gene_set_loader):
    gene_syms = prepare_gene_syms(data)
    gene_sets = prepare_gene_sets(data, gene_set_loader)

    if gene_syms is None:
        return gene_sets
    else:
        if gene_sets is None:
            return gene_syms
        else:
            return gene_sets.union(gene_syms)

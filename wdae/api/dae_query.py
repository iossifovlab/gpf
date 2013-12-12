import itertools

#from django.conf import settings
from django.core.cache import get_cache

from DAE import vDB
from DAE import get_gene_sets_symNS
from GeneTerm import GeneTerm
from VariantAnnotation import get_effect_types
from VariantsDB import mat2Str
from GetVariantsInterface import augmentAVar


from api.family_query import apply_families_advanced_filter
from api.family_query import prepare_family_advanced_variants_filters


def get_child_types():
    # return ['prb', 'sib', 'prbM', 'sibF', 'sibM', 'prbF']
    return ['prb', 'sib', 'prbM', 'prbF', 'sibM', 'sibF']


def get_variant_types():
    return ['All', 'CNV+', 'CNV-', 'snv', 'ins', 'del']


def prepare_inchild(data):
    if 'inChild' not in data:
        return None

    inChild = data['inChild']
    if inChild == 'All' or inChild == 'none' or inChild == 'None':
        return None

    if inChild not in get_child_types():
        return None

    return inChild


def prepare_effect_types(data):
    if 'effectTypes' not in data:
        return None

    effect_type = data['effectTypes']
    if effect_type == 'none' or effect_type == 'None' or \
       effect_type is None or effect_type == 'All':
        return None

    if effect_type not in get_effect_types(types=True, groups=True):
        return None

    return effect_type


def prepare_variant_types(data):
    if 'variantTypes' not in data:
        return None

    variant_types = data['variantTypes']
    if variant_types == 'none' or variant_types == 'None' or \
       variant_types is None:
        return None

    if variant_types == 'All':
        return None

    if variant_types not in get_variant_types():
        return None

    return variant_types


def prepare_family_ids(data):
    if 'familyIds' not in data:
        return None

    families = data['familyIds']
    if isinstance(families, str):
        if families.lower() == 'none' or families.lower() == 'all':
            return None
        else:
            return [s.strip()
                    for s in families.split(',') if len(s.strip()) > 0]
    elif isinstance(families, list):
        return families
    else:
        return None


def prepare_gene_syms(data):
    if 'geneSyms' not in data:
        return None

    gene_sym = data['geneSyms']
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
        return None


def __load_gene_set(gene_set_label, study_name=None):
    cache = get_cache('long')
    cache_key = 'gene_set_' + gene_set_label
    if 'denovo' == gene_set_label:
        cache_key += '_study_' + study_name
    gs = cache.get(cache_key)
    if not gs:
        if 'denovo' == gene_set_label:
            gene_term = get_gene_sets_symNS(gene_set_label, study_name)
        else:
            gene_term = get_gene_sets_symNS(gene_set_label)
        gs = GeneTerm(gene_term)
        cache.set(cache_key, gs)

    return gs


def __filter_gene_set(gene_set, data):
    gs_id = gene_set['gs_id']
    gs_term = gene_set['gs_term']

    #gs = None
    #if gs_id.lower().strip() == 'main':
    #    gs = settings.GENE_SETS_MAIN
    #elif gs_id.lower().strip() == 'go':
    #    gs = settings.GENE_SETS_GO
    #elif gs_id.lower().strip() == 'disease':
    #    gs = settings.GENE_SETS_DISEASE
    #elif gs_id.lower().strip() == 'denovo':
    #    dl = prepare_denovo_studies(data)
    #    if not dl:
    #        return None
    #    gs = get_gene_sets_symNS('denovo', dl)
    #else:
    #    return None

    if 'denovo' == gs_id:
        study = data['denovoStudies']
        if not study:
            return None
        gs = __load_gene_set('denovo', study)
    else:
        gs = __load_gene_set(gs_id)

    if gs_term not in gs.tDesc:
        return None

    gl = gs.t2G[gs_term].keys()

    print gl

    if not gl:
        return None

    return set(gl)


def prepare_gene_sets(data):
    if 'geneSet' not in data:
        return None

    gene_set = data['geneSet']

    if isinstance(gene_set, dict):
        return __filter_gene_set(gene_set, data)
    elif isinstance(gene_set, str):
        gs_id = gene_set
        if 'geneTerm' not in data:
            return None
        gs_term = data['geneTerm']

        return __filter_gene_set({'gs_id': gs_id,
                                  'gs_term': gs_term.split('|')[0].strip()},
                                 data)
    else:
        return None


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
    if 'transmittedStudies' not in data:
        return None

    tl = data['transmittedStudies']
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

# "minParentsCalled=600,maxAltFreqPrcnt=5.0,minAltFreqPrcnt=-1"


def __prepare_min_alt_freq_prcnt(data):
    minAltFreqPrcnt = -1.0
    if 'minAltFreqPrcnt' in data:
        try:
            minAltFreqPrcnt = float(str(data['minAltFreqPrcnt']))
        except:
            minAltFreqPrcnt = -1.0
    return minAltFreqPrcnt


def __prepare_max_alt_freq_prcnt(data):
    maxAltFreqPrcnt = 100.0
    if 'maxAltFreqPrcnt' in data:
        try:
            maxAltFreqPrcnt = float(str(data['maxAltFreqPrcnt']))
        except:
            maxAltFreqPrcnt = 5.0
    return maxAltFreqPrcnt


def __prepare_min_parents_called(data):
    minParentsCalled = 600
    if 'minParentsCalled' in data:
        try:
            minParentsCalled = float(str(data['minParentsCalled']))
        except:
            minParentsCalled = 600
    return minParentsCalled


def __prepare_ultra_rare(data):
    ultraRareOnly = None
    if 'ultraRareOnly' in data:
        if ultraRareOnly == 'True' or ultraRareOnly == 'true':
            ultraRareOnly = True
    elif 'rarity' in data:
        if data['rarity'].strip() == 'ultraRare':
            return True
    return ultraRareOnly


def prepare_gene_region(data):
    if 'geneRegion' not in data:
        return None
    return data['geneRegion'].strip()


def prepare_transmitted_filters(data):
    filters = {'variantTypes': prepare_variant_types(data),
               'effectTypes': prepare_effect_types(data),
               'inChild': prepare_inchild(data),
               'familyIds': prepare_family_ids(data),
               'geneSyms': combine_gene_syms(data),
               'regionS': prepare_gene_region(data),
               'ultraRareOnly': __prepare_ultra_rare(data),
               'minParentsCalled': __prepare_min_parents_called(data),
               'minAltFreqPrcnt': __prepare_min_alt_freq_prcnt(data),
               'maxAltFreqPrcnt': __prepare_max_alt_freq_prcnt(data)
             }
    return filters


def prepare_denovo_filters(data):

    filters = {'inChild': prepare_inchild(data),
               'variantTypes': prepare_variant_types(data),
               'effectTypes': prepare_effect_types(data),
               'familyIds': prepare_family_ids(data),
               'geneSyms': combine_gene_syms(data),
               'regionS': prepare_gene_region(data)}
    return filters


def dae_query_variants(data):
    variants = []

    dstudies = prepare_denovo_studies(data)
    if dstudies is not None:
        filters = prepare_denovo_filters(data)
        apply_families_advanced_filter(filters, data, dstudies)
        dvs = vDB.get_denovo_variants(dstudies, **filters)
        variants.append(dvs)

    tstudies = prepare_transmitted_studies(data)
    if tstudies is not None:
        filters = prepare_transmitted_filters(data)
        apply_families_advanced_filter(filters, data, tstudies)
        for study in tstudies:
            tvs = study.get_transmitted_variants(**filters)
            variants.append(tvs)

    return variants


def combine_filters(filters):
    return lambda v: all([f(v) for f in filters])


def prepare_variant_filters(data):
    fl = []
    prepare_family_advanced_variants_filters(data, fl)
    return fl


def generate_response(vs, atts=[]):
    def ge2Str(gs):
        return "|".join(x['sym'] + ":" + x['eff'] for x in gs)

    mainAtts = ['familyId',
                'studyName',
                'location',
                'variant',
                'bestSt',
                'fromParentS',
                'inChS',
                'counts',
                'geneEffect',
                'requestedGeneEffects',
                'popType']

    specialStrF = {"bestSt": mat2Str,
                   "counts": mat2Str,
                   "geneEffect": ge2Str,
                   "requestedGeneEffects": ge2Str}

    yield (mainAtts + atts)

    for v in vs:
        mavs = []
        for att in mainAtts:
            try:
                if att in specialStrF:
                    mavs.append(specialStrF[att](getattr(v, att)))
                else:
                    mavs.append(str(getattr(v, att)))
            except:
                mavs.append("")

        yield (mavs + [str(v.atts[a]).replace(',', ';')
                       if a in v.atts else "" for a in atts])


def join_line(l):
    return ','.join(l) + '\n'


def save_vs(tf, vs, atts=[]):
    for line in itertools.imap(join_line, generate_response(vs, atts)):
        tf.write(line)


def do_query_variants(data):
    vsl = dae_query_variants(data)

    variant_filters = prepare_variant_filters(data)
    if len(variant_filters) == 0:
        res_variants = itertools.chain(*vsl)
    else:
        cf = combine_filters(variant_filters)
        res_variants = itertools.ifilter(cf, itertools.chain(*vsl))

    return generate_response(itertools.imap(augmentAVar, res_variants),
                             ['effectType',
                              'effectDetails',
                              'all.altFreq',
                              'all.nAltAlls',
                              'all.nParCalled',
                              '_par_races_',
                              '_ch_prof_'])


def prepare_summary(vs):
    rows = []
    cols = vs.next()
    count = 0
    for r in vs:
        count += 1
        if count <= 25:
            rows.append(r)
        if count > 2000:
            break

    if count <= 2000:
        count = str(count)
    else:
        count = 'more than 2000'

    return {'count': count,
            'rows': rows,
            'cols': cols}

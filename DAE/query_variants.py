import itertools
import re
import logging

from DAE import vDB, phDB
from DAE import get_gene_sets_symNS

from VariantAnnotation import get_effect_types
from VariantsDB import mat2Str


logger = logging.getLogger(__name__)


def get_child_types():
    # return ['prb', 'sib', 'prbM', 'sibF', 'sibM', 'prbF']
    return ['prb', 'sib', 'prbM', 'prbF', 'sibM', 'sibF']


def get_variant_types():
    return ['All', 'CNV+', 'CNV-', 'snv', 'ins', 'del']


def get_races():
    return {'african-amer',
            'asian',
            'more-than-one-race',
            'native-american',
            'native-hawaiian',
            'white'}


def __get_float_measure(var_name):
    str_map = dict(zip(phDB.families, phDB.get_variable(var_name)))
    flt_map = {}
    for key, val in str_map.items():
        try:
            flt_map[key] = float(val)
        except:
            pass
    return flt_map


def __get_string_measure(mName):
    return dict(zip(phDB.families, phDB.get_variable(mName)))


def get_verbal_iq():
    return __get_float_measure('pcdv.ssc_diagnosis_verbal_iq')


def get_non_verbal_iq():
    return __get_float_measure('pcdv.ssc_diagnosis_nonverbal_iq')


def get_pcdv_race():
    return __get_string_measure('pcdv.race')


def get_mocuv_race():
    return __get_string_measure('mocuv.race_parents')


def get_focuv_race():
    return __get_string_measure('focuv.race_parents')


def get_prb_gender():
    return __get_string_measure('Proband_Sex')


def get_sib_gender():
    return __get_string_measure('Sibling_Sex')


FATHER_RACE = get_focuv_race()
MOTHER_RACE = get_mocuv_race()
PARENTS_RACE = dict([(k, ';'.join([m, f])) for (k, m, f) in zip(phDB.families,
                                                                phDB.get_variable('mocuv.race_parents'),
                                                                phDB.get_variable('focuv.race_parents'))])
PARENTS_RACE_QUERY = dict([(k, f if f == m else 'more-than-one-race')
                           for (k, f, m) in zip(phDB.families,
                                                phDB.get_variable('mocuv.race_parents'),
                                                phDB.get_variable('focuv.race_parents'))])


def get_father_race():
    return FATHER_RACE


def get_mother_race():
    return MOTHER_RACE


def get_parents_race():
    return PARENTS_RACE


def __get_parents_race_filter():
    return PARENTS_RACE_QUERY


def family_filter_by_race(families, race):
    races = __get_parents_race_filter()
    res = dict([(key, val) for (key, val) in families.items()
                if key in races and races[key] == race])
    # logger.debug("family_filter_by_race: %s", str(res))
    return res


def __bind_family_filter_by_race(data, family_filters):
    if 'familyRace' in data and data['familyRace'].lower() != 'all':
        family_filters.append(
            lambda fs: family_filter_by_race(fs, data['familyRace'])
        )


def study_family_filter_by_verbal_iq(families, iq_lo=0.0, iq_hi=float('inf')):
    return dict([(key, families[key]) for key, val in get_verbal_iq().items()
                if key in families and val >= iq_lo and val <= iq_hi])


def __bind_family_filter_by_verbal_iq(data, family_filters):
    iq_hi = None
    iq_lo = None

    if 'familyVerbalIqHi' in data:
        try:
            iq_hi = float(data['familyVerbalIqHi'])
        except:
            iq_hi = None

    if 'familyVerbalIqLo' in data:
        try:
            iq_lo = float(data['familyVerbalIqLo'])
        except:
            iq_lo = None

    if iq_hi is None and iq_lo is None:
        return

    if iq_lo is None:
        iq_lo = 0.0
    if iq_hi is None:
        iq_hi = float('inf')

    family_filters.append(
        lambda fs: study_family_filter_by_verbal_iq(fs, iq_lo, iq_hi)
    )


def study_family_filter_by_prb_gender(families, gender):
    return dict([(key, val) for (key, val) in families.items()
                 if val.memberInOrder[2].gender == gender])


def __bind_family_filter_by_prb_gender(data, family_filters):
    if 'familyPrbGender' in data:
        if data['familyPrbGender'].lower() == 'male':
            family_filters.append(
                lambda fs: study_family_filter_by_prb_gender(fs, 'M')
            )
        elif data['familyPrbGender'].lower() == 'female':
            family_filters.append(
                lambda fs: study_family_filter_by_prb_gender(fs, 'F')
            )


def study_family_filter_by_sib_gender(families, gender):
    return dict([(key, val) for (key, val) in families.items()
                 if len(val.memberInOrder) > 3
                 and val.memberInOrder[3].gender == gender])


def __bind_family_filter_by_sib_gender(data, family_filters):
    if 'familySibGender' in data:
        if data['familySibGender'].lower() == 'male':
            family_filters.append(
                lambda fs: study_family_filter_by_sib_gender(fs, 'M')
            )
        elif data['familySibGender'].lower() == 'female':
            family_filters.append(
                lambda fs: study_family_filter_by_sib_gender(fs, 'F')
            )


def study_family_filter_by_trio_quad(families, trio_quad):
    """
    Filters dictionary of families by number of family members.
    Returns dictionary of families, for which number of members is equal
    to 'trio_quad' parameter of the function.
    """
    return dict([(key, val) for (key, val) in families.items()
                 if len(val.memberInOrder) == trio_quad])


def __bind_family_filter_by_trio_quad(data, family_filters):
    if 'familyQuadTrio' in data:
        if data['familyQuadTrio'].lower() == 'trio':
            logger.debug("filtering trio families...")
            family_filters.append(
                lambda fs: study_family_filter_by_trio_quad(fs, 3)
            )
        elif data['familyQuadTrio'].lower() == 'quad':
            logger.debug("filtering quad families...")
            family_filters.append(
                lambda fs: study_family_filter_by_trio_quad(fs, 4)
            )


def __apply_family_filters(study, family_filters):
    if family_filters is None or len(family_filters) == 0:
        return None
    families = study.families
    for ff in family_filters:
        families = ff(families)
    return families


def advanced_family_filter(data, filters):
    if 'familyIds' in filters and filters['familyIds'] is not None \
       and len(filters['familyIds']) > 0:
        return None

    family_filters = []
    __bind_family_filter_by_race(data, family_filters)
    __bind_family_filter_by_verbal_iq(data, family_filters)
    __bind_family_filter_by_trio_quad(data, family_filters)
    __bind_family_filter_by_prb_gender(data, family_filters)
    __bind_family_filter_by_sib_gender(data, family_filters)
    # logger.debug("family filters: %d", len(family_filters))

    if len(family_filters) == 0:
        return None
    else:
        return lambda study: __apply_family_filters(study, family_filters)


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


def __filter_gene_set(gene_set, data, gene_set_loader=get_gene_sets_symNS):
    gs_id = gene_set['gs_id']
    gs_term = gene_set['gs_term']

    if 'denovo' == gs_id:
        study = data['geneStudy']
        if not study:
            return None
        gs = gene_set_loader('denovo', study)
    else:
        gs = gene_set_loader(gs_id)

    if gs_term not in gs.tDesc:
        return None

    gl = gs.t2G[gs_term].keys()

    if not gl:
        return None

    return set(gl)


def prepare_gene_sets(data, gene_set_loader=get_gene_sets_symNS):
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
                                 data,
                                 gene_set_loader)
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


def combine_gene_syms(data, gene_set_loader=get_gene_sets_symNS):
    gene_syms = prepare_gene_syms(data)
    gene_sets = prepare_gene_sets(data, gene_set_loader)

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


REGION = re.compile(r"""(\d+|[Xx]):(\d+)-(\d+)""")


def validate_region(region):
    res = REGION.match(region)
    if not res:
        return None

    try:
        chromo = res.groups()[0]
        if chromo.lower() != 'x' and not (22 >= int(chromo) >= 1):
            return None
        start = int(res.groups()[1])
        end = int(res.groups()[2])
    except ValueError:
        return None
    if start >= end:
        return None
    return True


def prepare_gene_region(data):
    if 'geneRegion' not in data:
        return None
    region = data['geneRegion']
    if not validate_region(region):
        return None
    return data['geneRegion'].strip()


def prepare_transmitted_filters(data, gene_set_loader=get_gene_sets_symNS):
    filters = {'variantTypes': prepare_variant_types(data),
               'effectTypes': prepare_effect_types(data),
               'inChild': prepare_inchild(data),
               'familyIds': prepare_family_ids(data),
               'geneSyms': combine_gene_syms(data, gene_set_loader),
               'regionS': prepare_gene_region(data),
               'ultraRareOnly': __prepare_ultra_rare(data),
               'minParentsCalled': __prepare_min_parents_called(data),
               'minAltFreqPrcnt': __prepare_min_alt_freq_prcnt(data),
               'maxAltFreqPrcnt': __prepare_max_alt_freq_prcnt(data)}
    return filters


def prepare_denovo_filters(data, gene_set_loader=get_gene_sets_symNS):

    filters = {'inChild': prepare_inchild(data),
               'variantTypes': prepare_variant_types(data),
               'effectTypes': prepare_effect_types(data),
               'familyIds': prepare_family_ids(data),
               'geneSyms': combine_gene_syms(data, gene_set_loader),
               'regionS': prepare_gene_region(data)}
    return filters


def get_denovo_variants(studies, family_filters, **filters):
    if isinstance(studies, str):
        studies = vDB.get_studies(studies)
    seenVs = set()
    for study in studies:
        if family_filters is not None:
            families = family_filters(study).keys()
            filters['familyIds'] = families if len(families) > 0 else [None]
            #logger.debug("study: %s, families: %s", study.name, str(families))
        for v in study.get_denovo_variants(**filters):
            vKey = v.familyId + v.location + v.variant
            if vKey in seenVs:
                continue
            yield v
            seenVs.add(vKey)


def dae_query_variants(data, gene_set_loader=get_gene_sets_symNS):
    logger.info("query received: %s", str(data))

    variants = []

    dstudies = prepare_denovo_studies(data)
    if dstudies is not None:
        filters = prepare_denovo_filters(data, gene_set_loader)
        family_filters = advanced_family_filter(data, filters)
        dvs = get_denovo_variants(dstudies, family_filters, **filters)
        variants.append(dvs)

    tstudies = prepare_transmitted_studies(data)
    if tstudies is not None:
        filters = prepare_transmitted_filters(data, gene_set_loader)
        for study in tstudies:
            family_filters = advanced_family_filter(data, filters)
            if family_filters is not None:
                families = family_filters(study).keys()
                filters['familyIds'] = families if len(families) > 0 else [None]

            tvs = study.get_transmitted_variants(**filters)
            variants.append(tvs)

    return variants


def __augment_vars(v):
    fmId = v.familyId
    parRaces = get_parents_race()[fmId] \
        if fmId in get_parents_race() else "NA;NA"

    chProf = "".join((p.role + p.gender for p in v.memberInOrder[2:]))
    v.atts["_par_races_"] = parRaces
    v.atts["_ch_prof_"] = chProf
    return v


def do_query_variants(data, gene_set_loader=get_gene_sets_symNS):
    vsl = dae_query_variants(data, gene_set_loader)

    res_variants = itertools.chain(*vsl)
    return generate_response(itertools.imap(__augment_vars, res_variants),
                             ['effectType',
                              'effectDetails',
                              'all.altFreq',
                              'all.nAltAlls',
                              'all.nParCalled',
                              '_par_races_',
                              '_ch_prof_'])


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

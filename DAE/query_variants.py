import itertools
import re
import logging
from query_prepare import \
    prepare_denovo_studies, prepare_transmitted_studies, \
    prepare_denovo_phenotype, prepare_gender_filter, \
    prepare_denovo_pheno_filter, build_effect_type_filter


from VariantAnnotation import get_effect_types_set, get_effect_types
from VariantsDB import mat2Str
from DAE import phDB
from query_prepare import prepare_denovo_study_type, prepare_gene_syms

LOGGER = logging.getLogger(__name__)


def get_child_types():
    # return ['prb', 'sib', 'prbM', 'sibF', 'sibM', 'prbF']
    return ['prb', 'sib', 'prbM', 'prbF', 'sibM', 'sibF']


def get_variant_types():
    return ['All', 'CNV', 'sub', 'ins', 'del', 'ins,del']


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
PROBAND_VIQ = get_verbal_iq()
PROBAND_NVIQ = get_non_verbal_iq()

PARENTS_RACE = \
    dict([(k, ':'.join([m, f]))
          for (k, m, f) in zip(phDB.families,
                               phDB.get_variable('mocuv.race_parents'),
                               phDB.get_variable('focuv.race_parents'))])
PARENTS_RACE_QUERY = \
    dict([(k, f if f == m else 'more-than-one-race')
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
    # LOGGER.debug("family_filter_by_race: %s", str(res))
    return res


def __bind_family_filter_by_race(data, family_filters):
    if 'familyRace' in data and data['familyRace'] \
       and data['familyRace'].lower() != 'all':

        family_filters.append(
            lambda fs: family_filter_by_race(fs, data['familyRace'])
        )


def family_filter_by_verbal_iq(families, iq_lo=0.0, iq_hi=float('inf')):
    return dict([(key, families[key]) for key, val in get_verbal_iq().items()
                if key in families and val >= iq_lo and val <= iq_hi])


def __bind_family_filter_by_verbal_iq(data, family_filters):
    iq_hi = None
    iq_lo = None

    if 'familyVerbalIqHi' in data and data['familyVerbalIqHi']:
        try:
            iq_hi = float(data['familyVerbalIqHi'])
        except:
            iq_hi = None

    if 'familyVerbalIqLo' in data and data['familyVerbalIqLo']:
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
        lambda fs: family_filter_by_verbal_iq(fs, iq_lo, iq_hi)
    )


def family_filter_by_prb_gender(families, gender):
    return dict([(key, val) for (key, val) in families.items()
                 if val.memberInOrder[2].gender == gender])


def __bind_family_filter_by_prb_gender(data, family_filters):
    if 'familyPrbGender' in data and data['familyPrbGender']:
        if data['familyPrbGender'].lower() == 'male':
            family_filters.append(
                lambda fs: family_filter_by_prb_gender(fs, 'M')
            )
        elif data['familyPrbGender'].lower() == 'female':
            family_filters.append(
                lambda fs: family_filter_by_prb_gender(fs, 'F')
            )


def family_filter_by_sib_gender(families, gender):
    return dict([(key, val) for (key, val) in families.items()
                 if len(val.memberInOrder) > 3 and
                 val.memberInOrder[3].gender == gender])


def __bind_family_filter_by_sib_gender(data, family_filters):
    if 'familySibGender' in data and data['familySibGender']:
        if data['familySibGender'].lower() == 'male':
            family_filters.append(
                lambda fs: family_filter_by_sib_gender(fs, 'M')
            )
        elif data['familySibGender'].lower() == 'female':
            family_filters.append(
                lambda fs: family_filter_by_sib_gender(fs, 'F')
            )


def family_filter_by_trio_quad(families, trio_quad):
    """
    Filters dictionary of families by number of family members.
    Returns dictionary of families, for which number of members is equal
    to 'trio_quad' parameter of the function.
    """
    return dict([(key, val) for (key, val) in families.items()
                 if len(val.memberInOrder) == trio_quad])


def __bind_family_filter_by_trio_quad(data, family_filters):
    if 'familyQuadTrio' in data and data['familyQuadTrio']:
        if data['familyQuadTrio'].lower() == 'trio':
            LOGGER.debug("filtering trio families...")
            family_filters.append(
                lambda fs: family_filter_by_trio_quad(fs, 3)
            )
        elif data['familyQuadTrio'].lower() == 'quad':
            LOGGER.debug("filtering quad families...")
            family_filters.append(
                lambda fs: family_filter_by_trio_quad(fs, 4)
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
    # LOGGER.debug("family filters: %d", len(family_filters))

    if len(family_filters) == 0:
        return None
    else:
        return lambda study: __apply_family_filters(study, family_filters)


def prepare_inchild(data):
    if 'inChild' not in data:
        return None

    inChild = data['inChild']
    if not inChild:
        return None

    if inChild == 'All' or inChild == 'none' or inChild == 'None':
        return None
    if isinstance(inChild, str):
        inChild = inChild.split(',')

    res = [ic for ic in inChild if ic in get_child_types()]
    if not res:
        return None
    if len(res) != 1:
        LOGGER.error("inChild format wrong: %s, %s", inChild, res)
        return None
    return res[0]


PRESENT_IN_CHILD_TYPES = [
    "autism only",
    "unaffected only",
    "autism and unaffected",
    "proband only",
    "sibling only",
    "proband and sibling",
    "neither",
]


def prepare_present_in_child(data):
    if "presentInChild" in data:
        present_in_child = set(data['presentInChild'].split(','))
        assert any([pic in PRESENT_IN_CHILD_TYPES for pic in present_in_child])
        return list(present_in_child)

    return None

PRESENT_IN_PARENT_TYPES = [
    "mother only", "father only",
    "mother and father", "neither",
]


def prepare_present_in_parent(data):
    if "presentInParent" in data:
        present_in_parent = set(data['presentInParent'].split(','))
        assert all([pip in PRESENT_IN_PARENT_TYPES
                    for pip in present_in_parent])
        return list(present_in_parent)
    return None


def prepare_effect_types(data):
    if 'effectTypes' not in data:
        return None
    build_effect_type_filter(data)

    effect_type = data['effectTypes']
    if effect_type == 'none' or effect_type == 'None' or \
       effect_type is None or effect_type == 'All':
        return None

    effect_type_list = [et for et in effect_type.split(',')
                        if et in get_effect_types(types=True, groups=True)]

    if not effect_type_list:
        return None
    return list(get_effect_types_set(','.join(effect_type_list)))


def prepare_variant_types(data):
    if 'variantTypes' not in data:
        return None

    variant_types = data['variantTypes']
    if variant_types == 'none' or variant_types == 'None' or \
       variant_types is None:
        return None

    if variant_types == 'All':
        return None

    variant_types_set = set(get_variant_types())
    variant_types_list = variant_types.split(',')
    result = [vt for vt in variant_types_list if vt in variant_types_set]
    LOGGER.info("variant types: %s", result)
    if result:
        return result

    return None


def prepare_family_ids(data):
    if 'familyIds' not in data and 'familiesList' not in data \
       and 'familiesFile' not in data:
        return None

    if 'familyIds' in data and data['familyIds']:
        families = data['familyIds']
    elif 'familiesList' in data and data['familiesList']:
        families = data['familiesList']
    elif 'familiesFile' in data and data['familiesFile']:
        families = __load_text_column(data['familiesFile'])
    else:
        return None

    if isinstance(families, str):
        if families.lower() == 'none' or families.lower() == 'all':
            return None
        else:
            return [s.strip()
                    for s in families.replace(',', ' ').split()
                    if len(s.strip()) > 0]
    elif isinstance(families, list):
        return families
    else:
        return None


def prepare_min_alt_freq_prcnt(data):
    minAltFreqPrcnt = -1.0
    if 'popFrequencyMin' in data:
        try:
            minAltFreqPrcnt = float(str(data['popFrequencyMin']))
        except:
            minAltFreqPrcnt = -1.0
    return minAltFreqPrcnt


def prepare_max_alt_freq_prcnt(data):
    maxAltFreqPrcnt = 100.0
    if 'popFrequencyMax' in data:
        try:
            maxAltFreqPrcnt = float(str(data['popFrequencyMax']))
        except:
            maxAltFreqPrcnt = 5.0
    return maxAltFreqPrcnt


def prepare_pop_min_parents_called(data):
    minParentsCalled = 0
    if 'popMinParentsCalled' in data:
        try:
            minParentsCalled = float(str(data['popMinParentsCalled']))
        except:
            minParentsCalled = 0
    return minParentsCalled


def prepare_TMM_ALL(data):
    if 'TMM_ALL' in data and data['TMM_ALL']:
        return True
    return False


def prepare_ultra_rare(data):
    if 'rarity' in data:
        if data['rarity'].strip() == 'ultraRare':
            return True
    elif 'popFrequencyMax' in data and data['popFrequencyMax'] == 'ultraRare':
        return True
    return False


REGION = re.compile(r"""^(\d+|[Xx]):(\d+)-(\d+)$""")


def validate_region(region):
    res = REGION.match(region)
    if not res:
        return None

    try:
        chromo = res.groups()[0]
        if chromo.lower() != 'x' and not (22 >= int(chromo) >= 1):
            return None
        print(res.groups())
        start = int(res.groups()[1])
        end = int(res.groups()[2])
    except ValueError:
        return None
    if start >= end:
        return None
    return True


def prepare_gene_region(data):
    if 'geneRegion' not in data and 'regionS' not in data:
        return None
    if 'geneRegion' in data and data['geneRegion']:
        region = data['geneRegion']
    elif 'regionS' in data and data['regionS']:
        region = data['regionS']
    else:
        return None

    if isinstance(region, str):
        region = region.replace(',', ' ').split()
    region = [r for r in region if validate_region(r)]
    if region:
        return region
    else:
        return None


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


def prepare_transmitted_filters(data,
                                denovo_filters={}):

    filters = {'ultraRareOnly': prepare_ultra_rare(data),
               'minParentsCalled': prepare_pop_min_parents_called(data),
               'minAltFreqPrcnt': prepare_min_alt_freq_prcnt(data),
               'maxAltFreqPrcnt': prepare_max_alt_freq_prcnt(data),
               'TMM_ALL': prepare_TMM_ALL(data),
               'presentInParent': prepare_present_in_parent(data),
               }
    return dict(filters, **denovo_filters)


def prepare_denovo_filters(data):

    filters = {'inChild': prepare_inchild(data),
               'presentInChild': prepare_present_in_child(data),
               'gender': prepare_gender_filter(data),
               'variantTypes': prepare_variant_types(data),
               'effectTypes': prepare_effect_types(data),
               'familyIds': prepare_family_ids(data),
               'geneSyms': prepare_gene_syms(data),
               # 'geneIds': prepare_gene_ids(data),
               'regionS': prepare_gene_region(data)}

    return filters


def get_denovo_variants(studies, family_filters, **filters):
    seenVs = set()
    for (study, phenoFilter) in studies:
        if family_filters is not None:
            families = family_filters(study).keys()
            filters['familyIds'] = families if len(families) > 0 else [None]

        if phenoFilter:
            all_filters = dict(filters, **phenoFilter)
        else:
            all_filters = filters

        for v in study.get_denovo_variants(**all_filters):
            vKey = v.familyId + v.location + v.variant
            if vKey in seenVs:
                continue
            yield v
            seenVs.add(vKey)


def dae_query_variants(data):
    assert "geneSet" not in data

    prepare_denovo_phenotype(data)
    prepare_denovo_study_type(data)
    prepare_gender_filter(data)

    dstudies = prepare_denovo_studies(data)
    tstudies = prepare_transmitted_studies(data)
    if dstudies is None and tstudies is None:
        return []

    denovo_filters = prepare_denovo_filters(data)
    family_filters = advanced_family_filter(data, denovo_filters)

    variants = []
    if dstudies is not None:
        denovo_filtered_studies = prepare_denovo_pheno_filter(data, dstudies)
        dvs = get_denovo_variants(denovo_filtered_studies, family_filters,
                                  **denovo_filters)
        variants.append(dvs)

    if tstudies is not None:
        transmitted_filters = prepare_transmitted_filters(data, denovo_filters)
        for study in tstudies:
            if family_filters is not None:
                families = family_filters(study).keys()
                transmitted_filters['familyIds'] = families \
                    if len(families) > 0 else [None]

            tvs = study.get_transmitted_variants(**transmitted_filters)
            variants.append(tvs)

    return variants


def pedigree_data(v):
    return [v.study.get_attr('study.phenotype'), v.pedigree]


def augment_vars(v):
    fmId = v.familyId
    parRaces = get_parents_race()[fmId] \
        if fmId in get_parents_race() else "NA:NA"

    chProf = "".join((p.role + p.gender for p in v.memberInOrder[2:]))

    viq = str(PROBAND_VIQ[fmId]) \
        if fmId in PROBAND_VIQ else "NA"
    nviq = str(PROBAND_NVIQ[fmId]) \
        if fmId in PROBAND_NVIQ else "NA"

    v.atts["_par_races_"] = parRaces
    v.atts["_ch_prof_"] = chProf
    v.atts["_prb_viq_"] = viq
    v.atts["_prb_nviq_"] = nviq
    v.atts["_pedigree_"] = pedigree_data(v)
    # v.atts["phenoInChS"] = v.phenoInChS()

    return v


def do_query_variants(data, atts=[]):
    vsl = dae_query_variants(data)

    res_variants = itertools.chain(*vsl)
    return generate_response(itertools.imap(augment_vars, res_variants),
                             ['effectType',
                              'effectDetails',
                              'all.altFreq',
                              'all.nAltAlls',
                              'SSCfreq',
                              'EVSfreq',
                              'E65freq',
                              'all.nParCalled',
                              '_par_races_',
                              '_ch_prof_',
                              '_prb_viq_',
                              '_prb_nviq_',
                              'valstatus'] +
                             atts)


def __gene_effect_get_worst_effect(gs):
    if len(gs) == 0:
        return ''
    return gs[0]['eff']


def __gene_effect_get_genes(gs):
    genes_set = set([g['sym'] for g in gs])
    genes = list(genes_set)

    return ';'.join(genes)


COLUMN_TITLES = {'familyId': 'family id',
                 'location': 'location',
                 'variant': 'variant',
                 'bestSt': 'family genotype',
                 'fromParentS': 'from parent',
                 'inChS': 'in child',
                 'effectType': 'effect type',
                 'worstEffect': 'worst effect',
                 'genes': 'genes',
                 'geneEffect': 'all effects',
                 'requestedGeneEffects': 'requested effects',
                 'popType': 'population type',
                 'effectDetails': 'effect details',
                 'all.altFreq': 'alternative allele frequency',
                 'all.nAltAlls': 'number of alternative alleles',
                 'all.nParCalled': 'number of genotyped parents',
                 '_par_races_': 'parent races',
                 '_ch_prof_': 'children description',
                 '_prb_viq_': 'proband verbal iq',
                 '_prb_nviq_': 'proband non-verbal iq',
                 'studyName': 'study',
                 'counts': 'count',
                 'valstatus': 'validation status',
                 }


def attr_title(attr_key):
    return COLUMN_TITLES.get(attr_key, attr_key)


def generate_response(vs, atts=[], sep='\t'):
    def ge2Str(gs):
        return "|".join(x['sym'] + ":" + x['eff'] for x in gs)

    mainAtts = ['familyId',
                'studyName',
                'location',
                'variant',
                'bestSt',
                'fromParentS',
                'inChS',
                'worstEffect',
                'genes',
                'counts',
                'geneEffect',
                'requestedGeneEffects',
                'popType']

    specialStrF = {"bestSt": mat2Str,
                   "counts": mat2Str,
                   "geneEffect": ge2Str,
                   "requestedGeneEffects": ge2Str,
                   }

    specialGeneEffects = {"genes": __gene_effect_get_genes,
                          "worstEffect": __gene_effect_get_worst_effect}

    yield [attr_title(attr) for attr in mainAtts + atts]

    for v in vs:
        mavs = []
        for att in mainAtts:
            try:
                if att in specialStrF:
                    mavs.append(specialStrF[att](getattr(v, att)))
                elif att in specialGeneEffects:
                    mavs.append(specialGeneEffects[att](
                        getattr(v, 'requestedGeneEffects')))
                else:
                    mavs.append(str(getattr(v, att)))
            except:
                mavs.append("")
        hack = []
        for a in atts:
            if a in ['SSCfreq', 'EVSfreq', 'E65freq', ] and a not in v.atts:
                a = a[:3]+'-'+a[3:]
            if a in v.atts:
                val = str(v.atts[a]).replace(sep, ';').replace("'", '"')
                hack.append(val if val != 'False' else "")
            else:
                hack.append(getattr(v, a, ''))
        yield (mavs + hack)

#         yield (mavs + [str(v.atts[a]).replace(sep, ';').replace("'", '"')
#                 if a in v.atts else str(getattr(v, a, '')) for a in atts])


def join_line(l, sep=','):
    tl = map(lambda v: '' if v is None or v == 'None' else v, l)
    return sep.join(tl) + '\n'


def save_vs(tf, vs, atts=[]):
    for line in itertools.imap(join_line, generate_response(vs, atts)):
        tf.write(line)

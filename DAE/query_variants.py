import itertools
import re
import logging
from query_prepare import \
    prepare_denovo_studies, prepare_transmitted_studies, \
    prepare_denovo_phenotype, prepare_gender_filter, \
    prepare_denovo_pheno_filter, build_effect_type_filter


from VariantAnnotation import get_effect_types_set, get_effect_types
from VariantsDB import mat2Str
# from DAE import phDB
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


def prepare_inchild(data):
    if 'inChild' not in data:
        return None

    inChild = data['inChild']
    if not inChild:
        return None

    if inChild == 'All' or inChild == 'none' or inChild == 'None':
        return None
    if isinstance(inChild, str) or isinstance(inChild, unicode):
        inChild = str(inChild).split(',')

    res = [str(ic) for ic in inChild if str(ic) in get_child_types()]
    if not res:
        return None
    if len(res) != 1:
        LOGGER.error("inChild format wrong: %s, %s", inChild, res)
        return None
    return res[0]


PRESENT_IN_CHILD_TYPES = [
    "unaffected only",
    "affected only",
    "affected and unaffected",
    "neither",
]


def prepare_present_in_child(data):
    if "presentInChild" in data and data['presentInChild'] is not None:
        present_in_child = data['presentInChild']
        if isinstance(present_in_child, list):
            present_in_child = ','.join(present_in_child)
        present_in_child = set(str(present_in_child).split(','))
        assert any([pic in PRESENT_IN_CHILD_TYPES for pic in present_in_child])
        return list(present_in_child)

    return None


PRESENT_IN_PARENT_TYPES = [
    "mother only", "father only",
    "mother and father", "neither",
]


def prepare_present_in_parent(data):
    if "presentInParent" in data and data['presentInParent'] is not None:
        present_in_parent = data['presentInParent']
        if isinstance(present_in_parent, list):
            present_in_parent = ','.join(present_in_parent)
        present_in_parent = set(str(present_in_parent).split(','))
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

    effect_type_list = [str(et) for et in str(effect_type).split(',')
                        if et in get_effect_types(types=True, groups=True)]

    if not effect_type_list:
        return None
    return list(get_effect_types_set(','.join(effect_type_list)))


def prepare_variant_types(data):
    if 'variantTypes' not in data:
        return None

    variant_types = data['variantTypes']
    if isinstance(variant_types, list):
        variant_types = ','.join(variant_types)

    if variant_types == 'none' or variant_types == 'None' or \
       variant_types is None:
        return None

    if variant_types == 'All':
        return None

    variant_types_set = set(get_variant_types())
    variant_types_list = str(variant_types).split(',')
    result = [str(vt)
              for vt in variant_types_list if str(vt) in variant_types_set]
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
        if isinstance(families, list):
            families = ",".join(families)
    elif 'familiesList' in data and data['familiesList']:
        families = data['familiesList']
    elif 'familiesFile' in data and data['familiesFile']:
        families = __load_text_column(data['familiesFile'])
    else:
        return None

    if isinstance(families, str) or isinstance(families, unicode):
        families = str(families)
        if families.lower() == 'none' or families.lower() == 'all' or \
                families.strip() == '':
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
        except Exception:
            minAltFreqPrcnt = 0
    elif 'minAltFreqPrcnt' in data:
        try:
            minAltFreqPrcnt = float(str(data['minAltFreqPrcnt']))
        except Exception:
            minAltFreqPrcnt = 0

    return minAltFreqPrcnt


def prepare_max_alt_freq_prcnt(data):
    maxAltFreqPrcnt = 100.0
    if 'popFrequencyMax' in data:
        try:
            maxAltFreqPrcnt = float(str(data['popFrequencyMax']))
        except Exception:
            maxAltFreqPrcnt = 100.0
    elif 'maxAltFreqPrcnt' in data:
        try:
            maxAltFreqPrcnt = float(str(data['maxAltFreqPrcnt']))
        except Exception:
            maxAltFreqPrcnt = 100.0

    return maxAltFreqPrcnt


def prepare_pop_min_parents_called(data):
    minParentsCalled = 0
    if 'popMinParentsCalled' in data:
        try:
            minParentsCalled = float(str(data['popMinParentsCalled']))
        except Exception:
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


# REGION = re.compile(r"""^(\d+|[Xx]):(\d+)-(\d+)$""")
REGION = re.compile(
    r"^(chr)?(\d+|[Xx]):([\d]{1,3}(,?[\d]{3})*)(-([\d]{1,3}(,?[\d]{3})*))?$")


def fix_region(region):
    res = REGION.match(region)
    if not res:
        return None

    try:
        chromo = res.groups()[1]
        if chromo.lower() != 'x' and not (22 >= int(chromo) >= 1):
            return None
        start = res.groups()[2]
        end = res.groups()[5]
        if start and not end:
            start = int(start.replace(',', ''))
            end = start
        elif start and end:
            start = int(start.replace(',', ''))
            end = int(end.replace(',', ''))
        else:
            return None
    except ValueError:
        return None
    if start > end:
        return None
    return '{}:{}-{}'.format(chromo, start, end)


def validate_region(region):
    return fix_region(region) is not None


def prepare_gene_region(data):
    if 'geneRegion' not in data and 'regionS' not in data:
        return None
    if 'geneRegion' in data and data['geneRegion']:
        region = data['geneRegion']
    elif 'regionS' in data and data['regionS']:
        region = data['regionS']
    else:
        return None

    if isinstance(region, str) or isinstance(region, unicode):
        region = str(region).replace(';', ' ').split()
    region = [r for r in region if validate_region(r)]
    region = [fix_region(r) for r in region]

    if region:
        return region
    else:
        return None


def prepare_limit(data):
    if 'limit' not in data:
        return None
    limit = data['limit']
    res = None
    try:
        res = int(limit)
    except ValueError:
        res = None
    return res


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
               'limit': prepare_limit(data),
               }
    return dict(filters, **denovo_filters)


def prepare_denovo_filters(data):

    filters = {'inChild': prepare_inchild(data),
               'presentInChild': prepare_present_in_child(data),
               'presentInParent': prepare_present_in_parent(data),
               'gender': prepare_gender_filter(data),
               'variantTypes': prepare_variant_types(data),
               'effectTypes': prepare_effect_types(data),
               'familyIds': prepare_family_ids(data),
               'geneSyms': prepare_gene_syms(data),
               # 'geneIds': prepare_gene_ids(data),
               'regionS': prepare_gene_region(data),
               }

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


def _dae_query_families_with_transmitted_variants(
        data, tstudies, denovo_filters):

    result = set()
    if tstudies is not None:
        transmitted_filters = prepare_transmitted_filters(data, denovo_filters)
        for study in tstudies:
            fams = study.get_families_with_transmitted_variants(
                **transmitted_filters)
            result.update([f for f in fams])
    return result


def _dae_query_families_with_denovo_variants(
        data, dstudies, tstudies, denovo_filters):

    variants = []
    if dstudies is not None:
        denovo_filtered_studies = prepare_denovo_pheno_filter(data, dstudies)
        dvs = get_denovo_variants(denovo_filtered_studies, None, **
                                  denovo_filters)
        variants.append(dvs)
    result = set([v.familyId for v in itertools.chain(*variants)])
    return result


def dae_query_families_with_variants(data):
    assert "geneSet" not in data
    assert "geneWeigth" not in data

    prepare_denovo_phenotype(data)
    prepare_denovo_study_type(data)
    prepare_gender_filter(data)

    dstudies = prepare_denovo_studies(data)
    tstudies = prepare_transmitted_studies(data)

    if dstudies is None and tstudies is None:
        return []

    denovo_filters = prepare_denovo_filters(data)

    dresult = _dae_query_families_with_denovo_variants(
        data, dstudies, tstudies, denovo_filters)
    tresult = _dae_query_families_with_transmitted_variants(
        data, tstudies, denovo_filters)

    result = set()
    result.update(dresult)
    result.update(tresult)

    return result


def dae_query_variants(data):
    assert "geneSet" not in data
    assert "geneWeigth" not in data

    LOGGER.info("dae_query_variants: %s", data)

    prepare_denovo_phenotype(data)
    prepare_denovo_study_type(data)
    prepare_gender_filter(data)

    dstudies = prepare_denovo_studies(data)
    tstudies = prepare_transmitted_studies(data)

    if dstudies is None and tstudies is None:
        return []

    denovo_filters = prepare_denovo_filters(data)
    family_filters = None

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
    return v.pedigree


def augment_vars(v):
    chProf = "".join((p.role + p.gender for p in v.memberInOrder[2:]))

    v.atts["_par_races_"] = None
    v.atts["_ch_prof_"] = chProf
    v.atts["_prb_viq_"] = None
    v.atts["_prb_nviq_"] = None
    v.atts["_pedigree_"] = str(v.pedigree)
    v.atts["_phenotype_"] = v.study.get_attr('study.phenotype')
    v._phenotype_ = v.study.get_attr('study.phenotype')

    # v.atts["phenoInChS"] = v.phenoInChS()

    return v


def do_query_variants(data, atts=[]):

    vsl = dae_query_variants(data)

    res_variants = itertools.chain(*vsl)
    return generate_response(itertools.imap(augment_vars, res_variants),
                             ['familyId',
                              'studyName',
                              '_phenotype_',
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
                              'popType',
                              'effectType',
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
    if len(gs) == 0:
        return ''
    # genes_set = set([g['sym'] for g in gs if g['eff'] == gs[0]['eff']])
    genes_set = set([g['sym'] for g in gs])
    genes = list(genes_set)

    return ';'.join(genes)


DEFAULT_COLUMN_TITLES = {
    'familyId': 'family id',
    'location': 'location',
    'variant': 'variant',
    'bestSt': 'family genotype',
    'fromParentS': 'from parent',
    'inChS': 'in child',
    'effectType': 'worst effect type',
    'worstEffect': 'worst requested effect',
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
    '_phenotype_': 'study phenotype',
    'counts': 'count',
    'valstatus': 'validation status',
    '_pedigree_': '_pedigree_',
    'phenoInChs': 'phenoInChs',
    'dataset': 'dataset',
    'SSCfreq': 'SSCfreq',
    'EVSfreq': 'EVSfreq',
    'E65freq': 'E65freq',
}

def ge2Str(gs):
    return "|".join(x['sym'] + ":" + x['eff'] for x in gs)

SPECIAL_ATTRS_FORMAT = {
    "bestSt": mat2Str,
    "counts": mat2Str,
    "geneEffect": ge2Str,
    "requestedGeneEffects": ge2Str,
}

SPECIAL_GENE_EFFECTS = {
    "genes": __gene_effect_get_genes,
    "worstEffect": __gene_effect_get_worst_effect
}

def generate_web_response(variants, attrs, sep='\t'):
    return {
        'cols': attrs,
        'rows': transform_variants_to_lists(variants, attrs, sep)
    }

def generate_response(variants, attrs=DEFAULT_COLUMN_TITLES.keys(),
        attr_labels=DEFAULT_COLUMN_TITLES, sep='\t'):
    variant_rows = transform_variants_to_lists(variants, attrs, sep)
    return itertools.chain([map(lambda attr: attr_labels.get(attr, attr), attrs)],
                           variant_rows)

def transform_variants_to_lists(variants, attrs, sep='\t'):
    for v in variants:
        row_variant = []
        for attr in attrs:
            try:
                if attr in SPECIAL_ATTRS_FORMAT:
                    row_variant.append(SPECIAL_ATTRS_FORMAT[attr](getattr(v, attr, '')))
                elif attr in SPECIAL_GENE_EFFECTS:
                    row_variant.append(SPECIAL_GENE_EFFECTS[attr](
                        getattr(v, 'requestedGeneEffects')))
                elif attr in v.atts:
                    val = v.atts[attr]
                    if not isinstance(val, list):
                        val = str(val).replace(sep, ';').replace("'", "\'")
                    row_variant.append(val if val and val != 'False' and
                                val != 'None' else "")
                else:
                    row_variant.append(getattr(v, attr))
            except Exception:
                row_variant.append('')
        yield row_variant


def join_line(l, sep='\t'):
    tl = map(lambda v: '' if v is None or v == 'None' else v, l)
    return sep.join(tl) + '\n'


def save_vs(tf, vs, atts=[]):
    response = generate_response(vs, atts)
    tf.write(response['cols'])
    for line in itertools.imap(join_line, response['rows']):
        tf.write(line)

from __future__ import unicode_literals
from builtins import str

import itertools
import functools
import logging

from pheno.common import Status

LOGGER = logging.getLogger(__name__)

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


def merge_dicts(*dicts):
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


def ge2str(gs):
    return "|".join(g.symbol + ":" + g.effects for g in gs.genes)


def mat2str(mat, col_sep=" ", row_sep="/"):
    return row_sep.join([col_sep.join([str(n) for n in mat[i, :]])
                        for i in range(mat.shape[0])])


def gene_effect_get_worst_effect(gs):
    if gs is None:
        return ''
    return ','.join([gs.worst])


def gene_effect_get_genes(gs):
    if gs is None:
        return ''
    genes_set = set([x.symbol for x in gs.genes])
    genes = list(genes_set)

    return ';'.join(genes)


def normalRefCopyNumber(location, gender):
    clnInd = location.find(":")
    chrome = location[0:clnInd]

    if chrome in ['chrX', 'X', '23', 'chr23']:
        if '-' in location:
            dshInd = location.find('-')
            pos = int(location[clnInd + 1:dshInd])
        else:
            pos = int(location[clnInd + 1:])

        # hg19 pseudo autosomes region: chrX:60001-2699520
        # and chrX:154931044-155260560
        if pos < 60001 or (pos > 2699520 and pos < 154931044) \
                or pos > 155260560:

            if gender == 'M':
                return 1
            elif gender == 'U':
                LOGGER.warn(
                    'unspecified gender when calculating normal number of allels '
                    'in chr%s',
                    location
                )
                return 1
            elif gender != 'F':
                raise Exception('weird gender ' + gender)
    elif chrome in ['chrY', 'Y', '24', 'chr24']:
        if gender == 'M':
            return 1
        elif gender == 'U':
            LOGGER.warn(
                'unspecified gender when calculating normal number of allels '
                'in chr%s',
                location
            )
            return 1
        elif gender == 'F':
            return 0
        else:
            raise Exception('gender needed')
    return 2


def variant_count_v3(bs, c, location=None, gender=None, denovo_parent=None):
    normal = 2
    if location:
        normal = normalRefCopyNumber(location, gender)
        # print("variantCount: {}, {}, {}".format(
        # location, gender, normalRefCN))
        ref = bs[0, c]
        # print("count: {}".format(count))
        count = 0
        if bs.shape[0] == 2:
            alles = bs[1, c]
            if alles != 0:
                if ref == normal:
                    print("location: {}, gender: {}, c: {}, normal: {}, bs: {}"
                          .format(location, gender, c, normal, bs))
                count = alles
        elif bs.shape[0] == 1:
            if normal != ref:
                count = ref

        if c != denovo_parent:
            return [count, 0]
        else:
            return [0, 1]


STANDARD_ATTRS = {
    "family": "family_id",
    "location": "location",
    "variant": "cshl_variant",
}


def get_standard_attr(property, v):
    return getattr(v.alt_alleles[0], property)


STANDARD_ATTRS_LAMBDAS = {
    key: functools.partial(get_standard_attr, val)
    for key, val in STANDARD_ATTRS.items()
}

SPECIAL_ATTRS_FORMAT = {
    "bestSt": lambda v: mat2str(v.bestSt),
    "counts": lambda v: mat2str(v.alt_alleles[0]["counts"]),
    "genotype": lambda v: mat2str(v.alt_alleles[0].genotype),
    "pedigree": lambda v: generate_pedigree(v),
    "effects": lambda v: ge2str(v.alt_alleles[0].effects),
    "requestedGeneEffects": lambda v:
        ge2str(v.alt_alleles[0]["requestedGeneEffects"]),
    "genes": lambda v: gene_effect_get_genes(v.alt_alleles[0].effects),
    "worstEffect": lambda v: gene_effect_get_worst_effect(v.alt_alleles[0].effects)
}


SPECIAL_ATTRS = merge_dicts(
    SPECIAL_ATTRS_FORMAT,
    STANDARD_ATTRS_LAMBDAS
)


def transform_variants_to_lists(variants, attrs):
    for v in variants:
        row_variant = []
        for attr in attrs:
            try:
                if attr in SPECIAL_ATTRS:
                    row_variant.append(SPECIAL_ATTRS[attr](v))
                else:
                    row_variant.append(str(getattr(v, attr, '')))
            except (AttributeError, KeyError) as e:
                print(attr, type(e), e)
                row_variant.append('')
        yield row_variant


def generate_pedigree(variant):
    result = []
    for index, member in enumerate(variant.members_in_order):
        # FIXME: add missing denovo parent parameter to variant_count_v3 call
        result.append([
            variant.family_id,
            member.person_id,
            member.mom if member.has_mom() else '',
            member.dad if member.has_dad() else '',
            member.sex.short(),
            '#ffffff' if member.status == Status.unaffected.value else '#e35252'
            ] + variant_count_v3(
                variant.best_st, index, variant.location, member.sex.short())
        )

    return result


def get_variants_web_preview(
        variants, attrs, max_variants_count=1000):
    VARIANTS_HARD_MAX = 2000
    rows = transform_variants_to_lists(variants, attrs)
    count = min(max_variants_count, VARIANTS_HARD_MAX)

    limited_rows = itertools.islice(rows, count)

    if count <= max_variants_count:
        count = str(count)
    else:
        count = 'more than {}'.format(max_variants_count)

    return {
        'count': count,
        'cols': attrs,
        'rows': list(limited_rows)
    }


def expand_effect_types(effect_types):
    if isinstance(effect_types, str):
        effect_types = [effect_types]

    effects = []
    for effect in effect_types:
        effect_lower = effect.lower()
        if effect_lower in EFFECT_GROUPS:
            effects += EFFECT_GROUPS[effect_lower]
        else:
            effects.append(effect)

    result = []
    for effect in effects:
        if effect not in EFFECT_TYPES_MAPPING:
            result.append(effect)
        else:
            result += EFFECT_TYPES_MAPPING[effect]
    return result


EFFECT_TYPES_MAPPING = {
    "Nonsense": ["nonsense"],
    "Frame-shift": ["frame-shift"],
    "Splice-site": ["splice-site"],
    "Missense": ["missense"],
    "Non-frame-shift": ["no-frame-shift"],
    "No-frame-shift-newStop": ["no-frame-shift-newStop"],
    "noStart": ["noStart"],
    "noEnd": ["noEnd"],
    "Synonymous": ["synonymous"],
    "Non coding": ["non-coding"],
    "Intron": ["intron"],
    "Intergenic": ["intergenic"],
    "3'-UTR": ["3'UTR", "3'UTR-intron"],
    "5'-UTR": ["5'UTR", "5'UTR-intron"],
    "CNV": ["CNV+", "CNV-"],
    "CNV+": ["CNV+"],
    "CNV-": ["CNV-"],
}

EFFECT_GROUPS = {
    "coding": [
        "Nonsense",
        "Frame-shift",
        "Splice-site",
        "Missense",
        "Non-frame-shift",
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
        "Frame-shift",
        "Nonsense",
        "Splice-site",
        "No-frame-shift-newStop",
    ],
    "nonsynonymous": [
        "Nonsense",
        "Frame-shift",
        "Splice-site",
        "Missense",
        "Non-frame-shift",
        "noStart",
        "noEnd",
    ],
    "utrs": [
        "3'-UTR",
        "5'-UTR",
    ]
}

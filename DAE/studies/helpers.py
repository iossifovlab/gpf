from __future__ import unicode_literals
from builtins import str

import math
import itertools
import functools
import logging
from utils.vcf_utils import mat2str

from common.query_base import EffectTypesMixin

LOGGER = logging.getLogger(__name__)


def merge_dicts(*dicts):
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


def ge2str(gs):
    return "|".join(g.symbol + ":" + g.effects for g in gs.genes)


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


def get_people_group_attribute(v, attr):
    attributes = v.people_group_attribute(attr)

    attributes = list(filter(None.__ne__, attributes))
    attributes_set = set(attributes)
    people_group_attributes = list(attributes_set)

    return ';'.join(people_group_attributes)


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
                    'unspecified gender when calculating normal '
                    'number of allels '
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
    "location": "cshl_location",
    "variant": "cshl_variant",
}


def get_standard_attr(property, v, aa):
    return getattr(v.alt_alleles[aa], property)


STANDARD_ATTRS_LAMBDAS = {
    key: functools.partial(get_standard_attr, val)
    for key, val in STANDARD_ATTRS.items()
}

SPECIAL_ATTRS_FORMAT = {
    "bestSt": lambda v, aa: mat2str(v.bestSt),
    "counts": lambda v, aa: mat2str(v.alt_alleles[aa]["counts"]),
    "genotype": lambda v, aa: mat2str(v.alt_alleles[aa].genotype),
    "effects": lambda v, aa: ge2str(v.alt_alleles[aa].effects),
    "requestedGeneEffects": lambda v, aa:
        ge2str(v.alt_alleles[aa]["requestedGeneEffects"]),
    "genes": lambda v, aa: gene_effect_get_genes(v.alt_alleles[aa].effects),
    "worstEffect":
        lambda v, aa: gene_effect_get_worst_effect(v.alt_alleles[aa].effects),
}


SPECIAL_ATTRS = merge_dicts(
    SPECIAL_ATTRS_FORMAT,
    STANDARD_ATTRS_LAMBDAS
)


def transform_variants_to_lists(
        variants, genotype_attrs, pedigree_attrs, pedigree_selectors,
        selected_pedigree_selector):
    for v in variants:
        alt_alleles_count = len(v.alt_alleles)
        for alt_allele in range(alt_alleles_count):
            row_variant = []
            for attr in genotype_attrs:
                try:
                    if attr in SPECIAL_ATTRS:
                        row_variant.append(SPECIAL_ATTRS[attr](v, alt_allele))
                    elif attr == 'pedigree':
                        row_variant.append(generate_pedigree(
                            v, pedigree_selectors, selected_pedigree_selector))
                    else:
                        attribute =\
                            v.alt_alleles[alt_allele].get_attribute(attr, '')
                        if not isinstance(attribute, str):
                            if attribute is None or math.isnan(attribute):
                                attribute = ''
                            elif math.isinf(attribute):
                                attribute = 'inf'
                        row_variant.append(attribute)
                except (AttributeError, KeyError):
                    # print(attr, type(e), e)
                    row_variant.append('')
            for attr in pedigree_attrs:
                try:
                    if attr['source'] in SPECIAL_ATTRS:
                        row_variant.\
                            append(SPECIAL_ATTRS[attr['source']](
                                v, alt_allele))
                    else:
                        row_variant.append(get_people_group_attribute(v, attr))
                except (AttributeError, KeyError):
                    # print(attr, type(e), e)
                    row_variant.append('')
            yield row_variant


def get_person_color(member, pedigree_selectors, selected_pedigree_selector):
    if member.generated:
        return '#E0E0E0'
    if len(pedigree_selectors) == 0:
        return '#FFFFFF'
    pedigree_selector_id = selected_pedigree_selector.get('id', None)
    if pedigree_selector_id:
        selected_pedigree_selectors = list(filter(
            lambda ps: ps.id == pedigree_selector_id,
            pedigree_selectors))[0]
    else:
        selected_pedigree_selectors = pedigree_selectors[0]

    people_group_attribute =\
        member.get_attr(selected_pedigree_selectors['source'])
    domain = list(filter(lambda d: d['name'] == people_group_attribute,
                         selected_pedigree_selectors['domain']))
    if domain and people_group_attribute:
        return domain[0]['color']
    else:
        return selected_pedigree_selectors['default']['color']


def generate_pedigree(variant, pedigree_selectors, selected_pedigree_selector):
    result = []
    for index, member in enumerate(variant.members_in_order):
        # FIXME: add missing denovo parent parameter to variant_count_v3 call
        result.append([
            variant.family_id,
            member.person_id,
            member.mom_id,
            member.dad_id,
            member.sex.short(),
            get_person_color(
                member, pedigree_selectors, selected_pedigree_selector),
            member.layout_position,
            member.generated
            ] + variant_count_v3(
                variant.best_st, index, variant.location, member.sex.short())
        )

    return result


def get_variants_web_preview(
        variants, pedigree_selectors, selected_pedigree_selector,
        genotype_attrs, pedigree_attrs, max_variants_count=1000):
    VARIANTS_HARD_MAX = 2000
    rows = transform_variants_to_lists(
        variants, genotype_attrs, pedigree_attrs, pedigree_selectors,
        selected_pedigree_selector)
    count = min(max_variants_count, VARIANTS_HARD_MAX)

    limited_rows = itertools.islice(rows, count)

    if count <= max_variants_count:
        count = str(count)
    else:
        count = 'more than {}'.format(max_variants_count)

    return {
        'count': count,
        'cols': genotype_attrs + [pa['source'] for pa in pedigree_attrs],
        'rows': list(limited_rows)
    }


def expand_effect_types(effect_types):
    if isinstance(effect_types, str):
        effect_types = [effect_types]

    effects = []
    for effect in effect_types:
        effect_lower = effect.lower()
        if effect_lower in EffectTypesMixin.EFFECT_GROUPS:
            effects += EffectTypesMixin.EFFECT_GROUPS[effect_lower]
        else:
            effects.append(effect)

    result = []
    for effect in effects:
        if effect not in EffectTypesMixin.EFFECT_TYPES_MAPPING:
            result.append(effect)
        else:
            result += EffectTypesMixin.EFFECT_TYPES_MAPPING[effect]
    return result

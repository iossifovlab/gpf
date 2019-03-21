from __future__ import unicode_literals
from builtins import str

import math
import numpy as np
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


STANDARD_ATTRS = {
    "family": "family_id",
    "location": "cshl_location",
    "variant": "cshl_variant",
}


def get_standard_attr(property, aa):
    return getattr(aa, property)


STANDARD_ATTRS_LAMBDAS = {
    key: functools.partial(get_standard_attr, val)
    for key, val in STANDARD_ATTRS.items()
}

SPECIAL_ATTRS_FORMAT = {
    "genotype": lambda aa: mat2str(aa.genotype),
    "effects": lambda aa: ge2str(aa.effects),
    "genes": lambda aa: gene_effect_get_genes(aa.effects),
    "worstEffect":
        lambda aa: gene_effect_get_worst_effect(aa.effects),
}


SPECIAL_ATTRS = merge_dicts(
    SPECIAL_ATTRS_FORMAT,
    STANDARD_ATTRS_LAMBDAS
)


def transform_variants_to_lists(variants, preview_columns, pedigree_selector):

    for v in variants:
        for alt_allele_index, aa in enumerate(v.matched_alleles):
            row_variant = []
            for column in preview_columns:
                try:
                    if column in SPECIAL_ATTRS:
                        row_variant.append(SPECIAL_ATTRS[column](aa))
                    elif column == 'pedigree':
                        row_variant.append(
                            generate_pedigree(aa, pedigree_selector))
                    else:
                        attribute =\
                            aa.get_attribute(column, '')
                        if not isinstance(attribute, str):
                            if attribute is None or math.isnan(attribute):
                                attribute = ''
                            elif math.isinf(attribute):
                                attribute = 'inf'
                        row_variant.append(attribute)
                except (AttributeError, KeyError):
                    row_variant.append('')

            yield row_variant


def get_person_color(member, pedigree_selector):
    if member.generated:
        return '#E0E0E0'
    if len(pedigree_selector) == 0:
        return '#FFFFFF'

    people_group_attribute = member.get_attr(pedigree_selector['source'])
    domain = list(filter(lambda d: d['name'] == people_group_attribute,
                         pedigree_selector['domain']))

    if domain and people_group_attribute:
        return domain[0]['color']
    else:
        return pedigree_selector['default']['color']


def generate_pedigree(allele, pedigree_selector):
    result = []
    best_st = np.sum(allele.gt == allele.allele_index, axis=0)

    for index, member in enumerate(allele.members_in_order):
        # FIXME: add missing denovo parent parameter to variant_count_v3 call
        result.append([
            allele.family_id,
            member.person_id,
            member.mom_id,
            member.dad_id,
            member.sex.short(),
            str(member.role),
            get_person_color(member, pedigree_selector),
            member.layout_position,
            member.generated,
            best_st[index],
            0
        ])

    return result


def get_variants_web(
        variants, genotype_attrs, pedigree_selector, max_variants_count=1000,
        variants_hard_max=2000):
    rows = transform_variants_to_lists(
        variants, genotype_attrs, pedigree_selector)

    if max_variants_count is not None:
        max_variants_count = min(max_variants_count, variants_hard_max)

        limited_rows = itertools.islice(rows, max_variants_count)
        limited_rows = list(limited_rows)
    else:
        limited_rows = list(rows)

    if max_variants_count is None or len(limited_rows) <= max_variants_count:
        count = str(len(limited_rows))
    else:
        count = 'more than {}'.format(max_variants_count)

    return {
        'count': count,
        'cols': genotype_attrs,
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

import traceback

import math
import numpy as np
import itertools
import functools
import logging

from dae.utils.vcf_utils import mat2str
from dae.utils.dae_utils import split_iterable
from dae.common.query_base import EffectTypesMixin

LOGGER = logging.getLogger(__name__)


def merge_dicts(*dicts):
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


def ge2str(eff):
    return "|".join([
        "{}:{}".format(g.symbol, g.effect) for g in eff.genes])


def gd2str(eff):
    return "|".join([
        "{}:{}".format(t.transcript_id, t.details)
        for t in eff.transcripts.values()])


def gene_effect_get_worst_effect(gs):
    if gs is None:
        return ''
    return ','.join([gs.worst])


def gene_effect_get_genes(gs):
    if gs is None:
        return ''
    genes_set = set([x.symbol for x in gs.genes])
    genes = sorted(list(genes_set))

    return ';'.join(genes)


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
    "effects": lambda aa: ge2str(aa.effect),
    "genes": lambda aa: gene_effect_get_genes(aa.effect),
    "worst_effect":
        lambda aa: gene_effect_get_worst_effect(aa.effect),
    "effect_details":
        lambda aa: gd2str(aa.effect),
    "best_st":
        lambda aa: mat2str(aa.best_st),
    "family_structure":
        lambda aa: "".join([
            "{}{}".format(p.role.name, p.sex.short())
            for p in aa.members_in_order])
}


SPECIAL_ATTRS = merge_dicts(
    SPECIAL_ATTRS_FORMAT,
    STANDARD_ATTRS_LAMBDAS
)


def transform_variants_to_lists(variants, preview_columns, people_group):

    for v in variants:
        for aa in v.matched_alleles:
            assert not aa.is_reference_allele

            row_variant = []
            for column in preview_columns:
                try:
                    if column in SPECIAL_ATTRS:
                        row_variant.append(SPECIAL_ATTRS[column](aa))
                    elif column == 'pedigree':
                        row_variant.append(generate_pedigree(aa, people_group))
                    else:
                        attribute = aa.get_attribute(column, '')
                        if not isinstance(attribute, str):
                            if attribute is None or math.isnan(attribute):
                                attribute = ''
                            elif math.isinf(attribute):
                                attribute = 'inf'
                        row_variant.append(attribute)
                except (AttributeError, KeyError):
                    traceback.print_exc()
                    row_variant.append('')

            yield row_variant


def get_person_color(member, people_group):
    if member.generated:
        return '#E0E0E0'
    if len(people_group) == 0:
        return '#FFFFFF'

    source = people_group['source']
    people_group_attribute = member.get_attr(source)
    domain = list(filter(lambda d: d['name'] == people_group_attribute,
                         people_group['domain']))

    if domain and people_group_attribute:
        return domain[0]['color']
    else:
        return people_group['default']['color']


def generate_pedigree(allele, people_group):
    result = []
    best_st = np.sum(allele.gt == allele.allele_index, axis=0)

    for index, member in enumerate(allele.members_in_order):
        result.append([
            allele.family_id,
            member.person_id,
            member.mom_id,
            member.dad_id,
            member.sex.short(),
            str(member.role),
            get_person_color(member, people_group),
            member.layout_position,
            member.generated,
            best_st[index],
            0
        ])

    return result


def get_variants_web(
        dataset, query, genotype_attrs, weights_loader,
        variants_hard_max=2000):

    query.pop('geneSet')

    variants = dataset.query_variants(weights_loader, **query)
    people_group_id = query.get('peopleGroup', {}).get('id', None)
    people_group_config = dataset.config.people_group_config
    people_group = []
    if people_group_config is not None:
        people_group = people_group_config.get_people_group(people_group_id)

    variants = add_gene_weight_columns(
        weights_loader, variants, dataset.gene_weights_columns)

    rows = transform_variants_to_lists(variants, genotype_attrs, people_group)

    if variants_hard_max is not None:
        limited_rows = itertools.islice(rows, variants_hard_max+1)

    return {
        'cols': genotype_attrs,
        'rows': limited_rows
    }


def get_variants_web_preview(
        dataset, query, weights_loader, max_variants_count=1000,
        variants_hard_max=2000):
    web_preview = get_variants_web(
        dataset, query, dataset.preview_columns, weights_loader,
        variants_hard_max)

    web_preview['rows'] = list(web_preview['rows'])

    if variants_hard_max is None or\
            len(web_preview['rows']) < variants_hard_max:
        count = str(len(web_preview['rows']))
    else:
        count = 'more than {}'.format(variants_hard_max)

    web_preview['count'] = count
    web_preview['rows'] = list(web_preview['rows'][:max_variants_count])

    return web_preview


def get_variants_web_download(
        dataset, query, weights_loader, max_variants_count=1000,
        variants_hard_max=2000):
    web_preview = get_variants_web(
        dataset, query, dataset.download_columns, weights_loader,
        variants_hard_max)

    web_preview['rows'] =\
        itertools.islice(web_preview['rows'], max_variants_count)

    return web_preview


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


def add_gene_weight_columns(
        weights_loader, variants_iterable, gene_weights_columns):
    for variants_chunk in split_iterable(variants_iterable, 5000):
        for variant in variants_chunk:
            for allele in variant.alt_alleles:
                genes = gene_effect_get_genes(allele.effects).split(';')
                gene = genes[0]

                gene_weights_values = {}
                for gwc in gene_weights_columns:
                    gene_weights = weights_loader[gwc]
                    if gene != '':
                        gene_weights_values[gwc] =\
                            gene_weights.to_dict().get(gene, '')
                    else:
                        gene_weights_values[gwc] = ''

                allele.update_attributes(gene_weights_values)
            yield variant

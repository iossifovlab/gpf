import functools
import operator

from collections import namedtuple

import numpy as np

from utils.vcf_utils import GENOTYPE_TYPE

from variants.variant import SummaryAllele, SummaryVariant
from variants.family_variant import FamilyVariant
from variants.effects import Effect


class ParquetSerializer(object):

    summary = namedtuple(
        'summary', [
            'summary_variant_index',
            'allele_index',
            'chrom',
            'position',
            'reference',
            'alternative',
            'variant_type',
            'worst_effect',
            'alternatives_data',
        ])

    effect_gene = namedtuple(
        'effect_gene', [
            'effect_type',
            'effect_gene',
            'effect_data',
        ]
    )

    family = namedtuple(
        'family', [
            'family_variant_index',
            'family_id',
            'is_denovo',
            'variant_sexes',
            'variant_roles',
            'variant_inheritance',
            'genotype_data',
        ]
    )

    member = namedtuple(
        'member', [
            'variant_in_member',
            # 'variant_in_role',
            # 'variant_in_sex',
            # 'inheritance_in_member',
        ]
    )

    frequency = namedtuple(
        'frequency', [
            'af_parents_called_count',
            'af_parents_called_percent',
            'af_allele_count',
            'af_allele_freq',
            'frequency_data',
        ]
    )

    def __init__(
            self, include_reference=True, annotation_schema=None):
        # self.families = families
        self.include_reference = include_reference
        self.annotation_schema = annotation_schema

    def serialize_summary(
            self, summary_variant_index, allele, alternatives_data):
        # if not self.include_reference and allele.is_reference_allele:
        #     return None
        if allele.is_reference_allele:
            return self.summary(
                summary_variant_index,
                allele.allele_index,
                allele.chrom,
                allele.position,
                allele.reference,
                None,
                None,
                None,
                alternatives_data,
            )
        else:
            return self.summary(
                summary_variant_index,
                allele.allele_index,
                allele.chrom,
                allele.position,
                allele.reference,
                allele.alternative,
                allele.variant_type.value,
                allele.effect.worst,
                alternatives_data,
            )

    def serialize_effects(self, allele, effect_data):
        if allele.is_reference_allele:
            return self.effect_gene(None, None, effect_data)
        return [
            self.effect_gene(eg.effect, eg.symbol, effect_data)
            for eg in allele.effect.genes
        ]

    def serialize_alelle_frequency(self, allele, frequency_data):
        freq = self.frequency(
            allele.get_attribute('af_parents_called_count'),
            allele.get_attribute('af_parents_called_percent'),
            allele.get_attribute('af_allele_count'),
            allele.get_attribute('af_allele_freq'),
            frequency_data,
        )
        return freq

    @staticmethod
    def serialize_variant_frequency(v):
        result = np.zeros((len(v.alleles), 4), dtype=np.float32)
        for row, allele in enumerate(v.alleles):
            result[row, 0] = allele.get_attribute('af_parents_called_count')
            result[row, 1] = allele.get_attribute('af_parents_called_percent')
            result[row, 2] = allele.get_attribute('af_allele_count')
            result[row, 3] = allele.get_attribute('af_allele_freq')
        flat = result.flatten(order='F')
        buff = flat.tobytes()
        data = str(buff, 'latin1')
        return data

    @staticmethod
    def deserialize_variant_frequency(data):
        buff = bytes(data, 'latin1')
        flat = np.frombuffer(buff, dtype=np.float32)
        assert len(flat) % 4 == 0

        rows = len(flat) // 4
        result = flat.reshape([rows, 4], order='F')
        attributes = []
        for row in range(rows):
            a = {
                'af_parents_called_count': int(result[row, 0]),
                'af_parents_called_percent': result[row, 1],
                'af_allele_count': int(result[row, 2]),
                'af_allele_freq': result[row, 3],
            }
            attributes.append(a)

        return attributes

    @staticmethod
    def serialize_variant_genotype(gt):
        rows, _ = gt.shape
        assert rows == 2
        flat = gt.flatten(order='F')
        buff = flat.tobytes()
        data = str(buff, 'latin1')

        return data

    @staticmethod
    def deserialize_variant_genotype(data):
        buff = bytes(data, 'latin1')
        gt = np.frombuffer(buff, dtype=GENOTYPE_TYPE)
        assert len(gt) % 2 == 0

        size = len(gt) // 2
        gt = gt.reshape([2, size], order='F')
        return gt

    @staticmethod
    def serialize_variant_alternatives(alternatives):
        return ",".join(alternatives)

    @staticmethod
    def deserialize_variant_alternatives(data):
        res = [None]
        res.extend(data.split(","))
        return res

    @staticmethod
    def serialize_variant_effects(effects):
        if effects is None:
            return None
        return "#".join([str(e) for e in effects])

    @staticmethod
    def deserialize_variant_effects(data):
        res = [None]
        res.extend([Effect.from_string(e) for e in data.split("#")])
        return res

    def serialize_family(
            self, family_variant_index, family_allele, genotype_data):
        res = self.family(
            family_variant_index,
            family_allele.family_id,
            family_allele.get_attribute('is_denovo'),
            functools.reduce(
                operator.or_, [
                    vs.value for vs in family_allele.variant_in_sexes
                    if vs is not None
                ], 0),
            functools.reduce(
                operator.or_, [
                    vr.value for vr in family_allele.variant_in_roles
                    if vr is not None
                ], 0),
            functools.reduce(
                operator.or_, [
                    vi.value for vi in family_allele.inheritance_in_members
                    if vi is not None
                ], 0),
            genotype_data,
        )
        return res

    def serialize_members(self, family_variant_index, family):
        result = []
        for variant_in_member in family.variant_in_members:
            if variant_in_member is None:
                continue
            result.append(self.member(variant_in_member))
        return result

    def deserialize_variant(
            self, family,
            chrom, position, reference, alternatives_data,
            effect_data, genotype_data, frequency_data):
        effects = ParquetSerializer.deserialize_variant_effects(
            effect_data)
        alternatives = ParquetSerializer.deserialize_variant_alternatives(
            alternatives_data
        )
        assert len(effects) == len(alternatives)
        # family = self.families.get(family_id)
        assert family is not None

        genotype = ParquetSerializer.deserialize_variant_genotype(
            genotype_data)
        rows, cols = genotype.shape
        assert cols == len(family)

        frequencies = ParquetSerializer.deserialize_variant_frequency(
            frequency_data)
        assert len(frequencies) == len(alternatives)

        alleles = []
        for allele_index, (alt, effect, freq) in \
                enumerate(zip(alternatives, effects, frequencies)):
            allele = SummaryAllele(
                chrom, position, reference,
                alternative=alt,
                allele_index=allele_index,
                effect=effect,
                attributes=freq)
            alleles.append(allele)
        sv = SummaryVariant(alleles)

        return FamilyVariant(sv, family, genotype)

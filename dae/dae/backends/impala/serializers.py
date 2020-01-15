import functools
import operator

from collections import namedtuple

import numpy as np

from dae.utils.variant_utils import GENOTYPE_TYPE
from dae.annotation.tools.file_io_parquet import ParquetSchema

from dae.variants.variant import SummaryAllele, SummaryVariant
from dae.variants.family_variant import FamilyAllele, FamilyVariant


class ParquetSerializer(object):

    GENOMIC_SCORES_SCHEMA_CLEAN_UP = [
        'worst_effect',
        'family_bin',
        'rare',
        'genomic_scores_data',
        'frequency_bin',
        'coding',
        'position_bin',
        'chrome_bin',
        'coding2',
        'region_bin',
    ]

    summary = namedtuple(
        'summary', [
            'summary_variant_index',
            'allele_index',
            'chrom',
            'position',
            'reference',
            'alternative',
            'variant_type',
            # 'worst_effect',
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

    def __init__(self, schema, include_reference=False):
        assert schema is not None
        assert isinstance(schema, ParquetSchema), type(schema)

        self.include_reference = include_reference
        self.schema = schema
        self._setup_genomic_scores()

    def _setup_genomic_scores(self):
        base_schema = ParquetSchema.from_arrow(
            ParquetSchema.BASE_SCHEMA)
        genomic_scores_schema = ParquetSchema.diff_schemas(
            self.schema, base_schema)
        for field_name in self.GENOMIC_SCORES_SCHEMA_CLEAN_UP:
            if field_name in genomic_scores_schema.columns:
                del genomic_scores_schema.columns[field_name]

        self.genomic_scores_schema = genomic_scores_schema.to_arrow()

        self.genomic_scores_count = len(self.genomic_scores_schema.names)
        fields = [
                *(self.genomic_scores_schema.names),
                'genomic_scores_data'
        ]
        self.genomic_scores = namedtuple(
            'genomic_scores', fields
        )

    def serialize_summary(
            self, summary_variant_index, allele, alternatives_data):
        if allele.is_reference_allele:
            return self.summary(
                summary_variant_index,
                allele.allele_index,
                allele.chrom,
                allele.position,
                allele.reference,
                None,
                None,
                # None,
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
                # allele.effect.worst if allele.effect else None,
                alternatives_data,
            )

    def serialize_effects(self, allele, effect_data):
        if allele.is_reference_allele:
            return [self.effect_gene(None, None, effect_data)]
        if allele.allele_index == -1:
            return [self.effect_gene(None, None, effect_data)]
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
        res = flat.reshape([rows, 4], order='F')
        attributes = []
        for row in range(rows):
            af_parents_called_count = \
                int(res[row, 0]) if not np.isnan(res[row, 0]) else None
            af_parents_called_percent = \
                res[row, 1] if not np.isnan(res[row, 1]) else None
            af_allele_count = \
                int(res[row, 2]) if not np.isnan(res[row, 2]) else None
            af_allele_freq = \
                res[row, 3] if not np.isnan(res[row, 3]) else None
            a = {
                'af_parents_called_count': af_parents_called_count,
                'af_parents_called_percent': af_parents_called_percent,
                'af_allele_count': af_allele_count,
                'af_allele_freq': af_allele_freq,
            }
            attributes.append(a)

        return attributes

    def serialize_genomic_scores(self, allele, genomic_scores_data):
        values = []
        for gs in self.genomic_scores_schema.names:
            values.append(allele.get_attribute(gs))
        values.append(genomic_scores_data)

        genomic_scores = self.genomic_scores(*values)
        return genomic_scores

    def serialize_variant_genomic_scores(self, v):
        if self.genomic_scores_count == 0:
            return None
        result = np.zeros(
            (len(v.alleles), self.genomic_scores_count),
            dtype=np.float32)
        for row, allele in enumerate(v.alleles):
            for col, gs in enumerate(self.genomic_scores_schema.names):
                result[row, col] = allele.get_attribute(gs)
        flat = result.flatten(order='F')
        buff = flat.tobytes()
        data = str(buff, 'latin1')
        return data

    def deserialize_variant_genomic_scores(self, data):
        if data is None:
            return None
        buff = bytes(data, 'latin1')
        flat = np.frombuffer(buff, dtype=np.float32)
        assert len(flat) % self.genomic_scores_count == 0, \
            self.genomic_scores_schema

        rows = len(flat) // self.genomic_scores_count
        result = flat.reshape([rows, self.genomic_scores_count], order='F')
        attributes = []
        for row in range(rows):
            a = {
                gs: result[row, col]
                for col, gs in enumerate(self.genomic_scores_schema.names)
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
        if data is None:
            return res
        res.extend(data.split(","))
        return res

    @staticmethod
    def serialize_variant_effects(effects):
        if effects is None:
            return None
        return "#".join([str(e) for e in effects])

    @staticmethod
    def deserialize_variant_effects(data):
        res = [{'effects': None}]
        if data is None:
            return res
        res.extend([{'effects': e} for e in data.split("#")])

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
            effect_data, genotype_data, frequency_data,
            genomic_scores_data):

        effects = self.deserialize_variant_effects(
            effect_data)
        alternatives = self.deserialize_variant_alternatives(
            alternatives_data
        )
        assert len(effects) == len(alternatives)
        # family = self.families.get(family_id)
        assert family is not None

        genotype = self.deserialize_variant_genotype(
            genotype_data)
        rows, cols = genotype.shape
        assert cols == len(family)

        frequencies = self.deserialize_variant_frequency(
            frequency_data)
        assert len(frequencies) == len(alternatives)

        genomic_scores = self.deserialize_variant_genomic_scores(
            genomic_scores_data
        )
        alleles = []
        if genomic_scores is None:
            values = zip(alternatives, effects, frequencies)
        else:
            assert len(frequencies) == len(genomic_scores)
            attributes = []
            for (f, g) in zip(frequencies, genomic_scores):
                f.update(g)
                attributes.append(f)
            values = zip(
                    alternatives, effects, attributes)

        for allele_index, (alt, effect, attr) in enumerate(values):
            attr.update(effect)
            summary_allele = SummaryAllele(
                chrom, position, reference,
                alternative=alt,
                summary_index=0,
                allele_index=allele_index,
                # effect=effect,
                attributes=attr
            )

            family_allele = FamilyAllele(
                summary_allele,
                family=family,
                genotype=genotype)

            alleles.append(family_allele)

        return FamilyVariant(SummaryVariant(alleles), family, genotype)

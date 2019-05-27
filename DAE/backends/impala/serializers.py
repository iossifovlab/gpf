import pickle
import zlib

from variants.variant import SummaryAllele, SummaryVariant
from variants.family_variant import FamilyVariant


class FamilyVariantSerializer(object):

    def __init__(self, families, include_reference=True):
        self.families = families
        self.include_reference = include_reference

    def serialize(self, variant):
        data = self.serialize_family_variant(variant)
        return zlib.compress(pickle.dumps(data))

    def deserialize(self, buf):
        data = pickle.loads(zlib.decompress(buf))
        return self.deserialize_family_variant(data)

    def serialize_allele(self, allele):
        assert isinstance(allele, SummaryAllele)

        return [
            allele.chromosome,
            allele.position,
            allele.reference,
            allele.alternative,
            allele.summary_index,
            allele.allele_index,
            allele.effect,
            allele.frequency,
            allele.attributes,
        ]

    def deserialize_alelle(self, args):
        return SummaryAllele(*args)

    def serialize_summary_variant(self, variant):
        assert isinstance(variant, SummaryVariant)

        return [
            self.serialize_allele(allele) for allele in variant.alleles
        ]

    def deserialize_summary_variant(self, args_list):
        alleles = [
            self.deserialize_alelle(args) for args in args_list
        ]
        return SummaryVariant(alleles)

    def serialize_family_variant(self, variant):
        summary_data = self.serialize_summary_variant(variant)
        family_id = variant.family_id
        genotype = variant.gt
        return [
            summary_data,
            family_id,
            genotype
        ]

    def deserialize_family_variant(self, data):
        summary_data, family_id, genotype = data
        family = self.families.get(family_id)
        assert family is not None, family_id
        summary_variant = self.deserialize_summary_variant(summary_data)
        return FamilyVariant(summary_variant, family, genotype)

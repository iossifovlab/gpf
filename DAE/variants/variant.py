'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals

from builtins import str
from builtins import zip
from builtins import range
from builtins import object
from utils.vcf_utils import vcf2cshl

from variants.attributes import VariantType
from variants.effects import Effect
import itertools


class VariantBase(object):
    """
    VariantBase is a base class for variants. It supports description of
    a variant in *a la VCF* style.

    Expected parameters of the constructor are:

    :param chromosome: chromosome label where variant is located
    :param position: position of the variant using *VCF* convention
    :param reference: reference DNA string
    :param alternatives: list of alternative DNA strings

    Each object of `VariantBase` has following fields:

    :ivar chromosome: chromosome lable where variant is located
    :ivar position: position of the variant using *VCF* convention
    :ivar reference: reference DNA string
    :ivar alternative: alternative DNA string
    """

    def __init__(self, chromosome, position, reference,
                 alternative=None):

        #: chromosome on which the variant is located
        self.chromosome = chromosome
        #: 1-based start postion of this variant on the reference
        self.position = position
        #: reference DNA string
        self.reference = reference

        self._alternative = alternative

    @property
    def alternative(self):
        """
        alternative DNA string; comma separated string when multiple
        alternative DNA strings should be represented; alternative is None
        when the variant is a reference variant.
        """
        return self._alternative

    @property
    def location(self):
        return '{}:{}'.format(self.chromosome, self.position)

    @property
    def variant(self):
        if self.alternative:
            return '{}->{}'.format(self.reference, self.alternative)
        else:
            return '{} (ref)'.format(self.reference)

    def __repr__(self):
        return '{} {}'.format(self.location, self.variant)

    def __eq__(self, other):
        return self.chromosome == other.chromosome and \
            self.position == other.position and \
            self.reference == other.reference and \
            self.alternative == other.alternative

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.chromosome <= other.chromosome and \
            self.position < other.position

    def __gt__(self, other):
        return self.chromosome >= other.chromosome and \
            self.position > other.position


class AltAlleleItems(object):
    """
    1-based list for representing list of items relevant to the list
    of alternative alleles.
    """

    def __init__(self, items, alt_alleles=None):
        if not hasattr(items, '__iter__'):
            items = [items]

        if alt_alleles is None:
            self.items = items
            self.alt_alleles = list(range(1, len(self.items) + 1))
        else:
            assert len(alt_alleles) == len(items) or len(items) == 1
            if len(items) == 1:
                item = items[0]
                self.items = [item for _ in alt_alleles]
            else:
                self.items = items

        self.size = len(self.items)

    def _to_zero_based(self, index):
        if isinstance(index, slice):
            return slice(self._to_zero_based(index.start),
                         self._to_zero_based(index.stop),
                         index.step)
        else:
            if index is None or index < 0:
                return index
            elif not 1 <= index <= self.size:
                raise IndexError("invalid allele index: {}".format(index))
            return index - 1

    def __getitem__(self, key):
        index = self._to_zero_based(key)
        if isinstance(index, int):
            return self.items[index]
        elif isinstance(index, slice):
            return [
                self.items[i]
                for i in range(*index.indices(self.size))
            ]
        raise TypeError("bad allele index type: {}".format(index))

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return self.size

    def __repr__(self):
        return self.items.__repr__()

    def __str__(self):
        return str(self.items)


class VariantDetail(object):
    def __init__(self, chrom, position, variant, length):
        self.length = length
        self.type = None
        self.chrom = chrom
        self.cshl_position = position
        self.cshl_variant = variant
        self.variant_type = VariantType.from_cshl_variant(self.cshl_variant)

    def __repr__(self):
        return "{} {}".format(
            self.cshl_location,
            self.cshl_variant)

    @property
    def cshl_location(self):
        return "{}:{}".format(self.chrom, self.cshl_position)

    @staticmethod
    def from_vcf(chrom, position, reference, alternative):
        return VariantDetail(
            chrom, *vcf2cshl(position, reference, alternative))


class SummaryAllele(VariantBase):
    """
    `SummaryAllele` represents a single allele for given position.
    """

    def __init__(self,
                 chromosome,
                 position,
                 reference,
                 alternative=None,
                 summary_index=None,
                 allele_index=0,
                 effect=None,
                 frequency=None,
                 attributes=None):
        super(SummaryAllele, self).__init__(
            chromosome, position, reference, alternative)

        #: index of the summary variant this allele belongs to
        self.summary_index = summary_index
        #: index of the allele of summary variant
        self.allele_index = allele_index

        if alternative is None:
            self.details = None
        else:
            self.details = VariantDetail.from_vcf(
                chromosome, position, reference, alternative)
        #: variant effect of the allele; None for the reference allele.
        self.effect = effect
        #: frequency of the allele
        self.frequency = frequency

        if attributes is None:
            #: allele additional attributes
            self.attributes = {}
        else:
            self.attributes = {}
            self.update_attributes(attributes)

        self.update_attributes({'variant_type': self.variant_type.value
                                if self.variant_type else None})

    @property
    def cshl_variant(self):
        if self.details is not None:
            return self.details.cshl_variant
        else:
            return None

    @property
    def cshl_location(self):
        if self.details is not None:
            return self.details.cshl_location
        else:
            return None

    @property
    def variant_type(self):
        if self.details is not None:
            return self.details.variant_type
        else:
            return None

    @property
    def effects(self):
        return self.effect

    @staticmethod
    def create_reference_allele(allele):
        return SummaryAllele(
            allele.chromosome,
            allele.position,
            allele.reference,
            attributes=allele.attributes)

    @property
    def is_reference_allele(self):
        return self.alternative is None

    def get_attribute(self, item, default=None):
        """
        looks up values matching key `item` in additional attributes passed
        on creation of the variant.
        """
        val = self.attributes.get(item, default)
        return val

    def has_attribute(self, item):
        """
        checks if additional variant attributes contain values for key `item`.
        """
        return item in self.attributes

    def update_attributes(self, atts):
        """
        updates additional attributes of variant using dictionary `atts`.
        """
        for key, val in list(atts.items()):
            self.attributes[key] = val

    def __getitem__(self, item):
        """
        allows using of standard dictionary access to additional variant
        attributes. For example `sv['af_parents_called']` will return value
        matching key `af_parents_called` from addtional variant attributes.
        """
        return self.attributes.get(item)

    def __contains__(self, item):
        """
        checks if additional variant attributes contain value for key `item`.
        """
        return item in self.attribute


class SummaryVariant(VariantBase):

    def __init__(self, alleles):
        assert len(alleles) >= 1
        assert len(set([sa.position for sa in alleles])) == 1

        self._matched_alleles = [a.allele_index for a in alleles]

        if not alleles[0].is_reference_allele:
            ref_allele = SummaryAllele.create_reference_allele(alleles[0])
            alleles = list(itertools.chain([ref_allele], alleles))

        assert alleles[0].is_reference_allele
        #: list of all alleles in the variant
        self.alleles = alleles
        #: the reference allele
        self.ref_allele = alleles[0]
        #: list of all alternative alleles
        self.alt_alleles = alleles[1:]

        self.allele_count = self.ref_allele.get_attribute("allele_count")
        if self.allele_count is None:
            self.allele_count = len(self.alleles)

        super(SummaryVariant, self).__init__(
            self.ref_allele.chromosome,
            self.ref_allele.position,
            self.ref_allele.reference)

        self.summary_index = self.ref_allele.summary_index

    def get_allele(self, allele_index):
        for allele in self.alleles:
            if allele.allele_index == allele_index:
                return allele
        return None

    # def allele_count(self):
    #     if self._allele_count is None:
    #         self._allele_count = len(self.alleles)
    #
    #     return self._allele_count

    @property
    def alternative(self):
        if not self.alt_alleles:
            return None
        return ','.join([aa.alternative for aa in self.alt_alleles])

    @property
    def details(self):
        """
        1-based list of `VariantDetails`, that describes each
        alternative allele.
        """
        if not self.alt_alleles:
            return None
        return AltAlleleItems([sa.details for sa in self.alt_alleles])

    @property
    def effects(self):
        """
        1-based list of `Effect`, that describes variant effects.
        """
        if not self.alt_alleles:
            return None
        return AltAlleleItems([sa.effect for sa in self.alt_alleles])

    @property
    def frequencies(self):
        """
        0-base list of frequencies for variant.
        """
        return [sa.frequency for sa in self.alleles]

    @property
    def variant_types(self):
        """
        returns set of variant types.
        """
        return set([aa.details.variant_type for aa in self.alt_alleles])

    def get_attribute(self, item, default=None):
        return [sa.get_attribute(item, default) for sa in self.alleles]

    def has_attribute(self, item):
        return any([sa.has_attribute(item) for sa in self.alleles])

    def __getitem__(self, item):
        return self.get_attribute(item)

    def __contains__(self, item):
        return self.has_attribute(item)

    def update_attributes(self, atts):
        # FIXME:
        for key, values in list(atts.items()):
            assert len(values) == 1 or len(values) == len(self.alt_alleles)
            for sa, val in zip(self.alt_alleles, itertools.cycle(values)):
                sa.update_attributes({key: val})


class SummaryVariantFactory(object):

    @staticmethod
    def summary_allele_from_record(
            record, transmission_type='transmitted'):
        record['transmission_type'] = transmission_type
        if record.get('effect_type') is None:
            effects = None
        else:
            effects = Effect.from_effects(
                record['effect_type'],
                list(zip(record['effect_gene_genes'],
                         record['effect_gene_types'])),
                list(zip(record['effect_details_transcript_ids'],
                         record['effect_details_details'])))
        alternative = record['alternative']

        return SummaryAllele(
            record['chrom'], record['position'],
            record['reference'],
            alternative=alternative,
            summary_index=record['summary_variant_index'],
            allele_index=record['allele_index'],
            effect=effects,
            frequency=record['af_allele_freq'],
            attributes=record)

    @staticmethod
    def summary_variant_from_records(records, transmission_type='transmitted'):
        assert len(records) > 0

        alleles = []
        for record in records:
            sa = SummaryVariantFactory.\
                summary_allele_from_record(
                    record,
                    transmission_type=transmission_type)
            alleles.append(sa)

        return SummaryVariant(alleles)

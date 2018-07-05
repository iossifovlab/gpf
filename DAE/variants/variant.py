'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
from variants.family import FamilyInheritanceMixin
from variants.vcf_utils import vcf2cshl

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

        self.chromosome = chromosome
        self.position = position
        self.reference = reference
        self._alternative = alternative

    @property
    def alternative(self):
        return self._alternative

    @property
    def alts(self):
        return self.alternative if self.alternative is not None else ""

    def __repr__(self):
        if not self.alts:
            return '{}:{} {} (ref)'.format(
                self.chromosome, self.position,
                self.reference)
        else:
            return '{}:{} {}->{}'.format(
                self.chromosome, self.position,
                self.reference,
                ",".join(self.alts))

    def start(self):
        """
        The 1-based start position of this variant on the reference contig.
        VCF column 2 "POS" converted to 1-based coordinate system,
        closed-open intervals
        """
        return self.position

    def end(self):
        """
        The 1-based, exclusive end position of this variant on the reference
        contig. Calculated by start + length of reference allele.
        """
        return self.position + len(self.reference)

    def __eq__(self, other):
        return self.chromosome == other.chromosome and \
            self.position == other.position and \
            self.reference == other.reference and \
            len(self.alts) == len(other.alts) and \
            all([a1 == a2 for (a1, a2) in zip(self.alts, other.alts)])

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return int(self.chromosome) <= int(other.chromosome) and \
            self.position < other.position

    def __gt__(self, other):
        return int(self.chromosome) >= int(other.chromosome) and \
            self.position > other.position


class AltAlleleItems(object):

    def __init__(self, items, alt_alleles=None):
        if not hasattr(items, '__iter__'):
            items = [items]

        if alt_alleles is None:
            self.items = items
            self.alt_alleles = range(1, len(self.items) + 1)
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
    `AlleleSummary` represents summary variants for given position.

    :ivar alts: 1-based list of alternative DNA strings describing the variant
    :ivar effect: 1-based list of :class:`variants.variant.Effect`, that
          describes variant effects.

    :ivar frequency: 0-base list of frequencies for variant.
    :ivar alt_alleles: list of alternative alleles indexes
    :ivar atts: Additional attributes describing this variant.
    :ivar details: 1-based list of `VariantDetails`, that describes variant.
    :ivar effect: 1-based list of `Effect` for each alternative allele.

    :effect: 1-based list of `Effect` for each alternative allele.
    """

    def __init__(self,
                 chromosome,
                 position,
                 reference,
                 alternative=None,
                 summary_index=None,
                 allele_index=1,
                 effect=None,
                 frequency=None,
                 attributes=None,
                 split_from_multi_allelic=False):
        """
        Expected parameters of the constructor are:

        :param chromosome: chromosome label where variant is located
        :param position: position of the variant using *VCF* convention
        :param reference: reference DNA string
        :param alternative: alternative DNA string
        :param atts: additional variant attributes
        """
        super(SummaryAllele, self).__init__(
            chromosome, position, reference, alternative)

        self.summary_index = summary_index
        self.allele_index = allele_index
        self.split_from_multi_allelic = split_from_multi_allelic

        if alternative is None:
            self.details = None
        else:
            self.details = VariantDetail.from_vcf(
                chromosome, position, reference, alternative)

        self.effect = effect
        self.frequency = frequency

        if attributes is None:
            self.attributes = {}
        else:
            self.attributes = {}
            self.update_attributes(attributes)

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
        for key, val in atts.items():
            self.attributes[key] = val

    def __getitem__(self, item):
        """
        allows using of standard dictionary access to additional variant
        attributes. For example `sv['all.altFreq']` will return value matching
        key `all.altFreq` from addtional variant attributes.
        """
        return self.get_attribute(item)

    def __contains__(self, item):
        """
        checks if additional variant attributes contains value for key `item`.
        """
        return item in self.attribute


class SummaryAlleleDelegate(SummaryAllele):

    def __init__(self, summary_allele=None, **kwargs):
        assert summary_allele is not None
        assert isinstance(summary_allele, SummaryAllele)

        self.delegate = summary_allele

    def __getattr__(self, name):
        return getattr(self.delegate, name)


class SummaryVariant(VariantBase):

    def __init__(self, alleles):
        assert len(alleles) >= 1
        assert len(set([sa.position for sa in alleles])) == 1

        assert alleles[0].is_reference_allele

        self.alleles = alleles
        self.ref_allele = alleles[0]
        self.alt_allels = alleles[1:]

        self.summary_index = self.ref_allele.summary_index

        super(SummaryVariant, self).__init__(
            self.ref_allele.chromosome,
            self.ref_allele.position,
            self.ref_allele.reference)

        self.alt_alleles = alleles[1:]

    @property
    def alts(self):
        return ','.join([aa.alternative for aa in self.alt_alleles])

    @property
    def alternative(self):
        if len(self.alt_alleles) != 1:
            raise ValueError()
        return self.alt_alleles[0].alternative

    @property
    def details(self):
        """
        1-based list of `VariantDetails`, that describes each
        alternative allele.
        """
        if len(self.alt_alleles) == 0:
            return None
        return AltAlleleItems([sa.details for sa in self.alt_alleles])

    @property
    def effects(self):
        """
        1-based list of `Effect`, that describes variant effects.
        """
        if len(self.alt_alleles) == 0:
            return None
        return AltAlleleItems([sa.effect for sa in self.alt_alleles])

    @property
    def frequencies(self):
        """
        0-base list of frequencies for variant.
        """
        return [sa.frequency for sa in self.alleles]

    def get_attribute(self, item, default=None):
        return [sa.get_attribute(item, default) for sa in self.alt_alleles]

    def has_attribute(self, item):
        return any([sa.has_attribute(item) for sa in self.alt_alleles])

    def __getitem__(self, item):
        return self.get_attribute(item)

    def __contains__(self, item):
        return self.has_attribute(item)

    def update_attributes(self, atts):
        # FIXME:
        for key, values in atts.items():
            assert len(values) == 1 or len(values) == len(self.alt_alleles)
            for sa, val in zip(self.alt_alleles, itertools.cycle(values)):
                sa.update_attributes({key: val})


class SummaryVariantFactory(object):

    @staticmethod
    def summary_allele_from_record(row):
        if not isinstance(row['effect_type'], str):
            effects = None
        else:
            effects = Effect.from_effects(
                row['effect_type'],
                zip(row['effect_gene_genes'], row['effect_gene_types']),
                zip(row['effect_details_transcript_ids'],
                    row['effect_details_details']))
        alternative = row['alternative']

        return SummaryAllele(
            row['chrom'], row['position'],
            row['reference'],
            alternative=alternative,
            summary_index=row['summary_index'],
            allele_index=row['allele_index'],
            effect=effects,
            frequency=row['af_allele_freq'],
            attributes=row,
            split_from_multi_allelic=row['split_from_multi_allelic'])

    @staticmethod
    def summary_variant_from_records(records):
        """
        Factory method for constructing `SummaryVariant` from dictionary.

        The dictionary should contain following elements:

        * `chr` - chromosome label
        * `position` - a VCF style start positon of the variant
        * `refA` - reference allele for variant
        * `altA` - list of alternative alleles
        * `effectType` - list of worst effects matching each alternative
           allele.
        * `effectGene` - list of effect type and gene symbol for each
           alternative alleles.
        * `effectDetails` - list of transcript effects matching eash
           alternative alleles.
        * `all.refFreq` - frequency of the reference allele
        * `all.altFreq` - list of frequencies for each the alternative alleles.

        All elements of the dictionary `row` are stored as additional
        attributes of the variant. These attributes are accessible through
        `get_attr`, `has_attr`, `__getitem__` and `__contains__` methods of
        summary variant.
        """
        assert len(records) > 0

        alleles = []
        for row in records:
            sa = SummaryVariantFactory.summary_allele_from_record(row)
            alleles.append(sa)

        return SummaryVariant(alleles)


class SummaryVariantDelegate(SummaryVariant):

    def __init__(self, summary_variant=None, **kwargs):
        assert summary_variant is not None
        assert isinstance(summary_variant, SummaryVariant)

        self.summary_variant = summary_variant

    def __getattr__(self, name):
        return getattr(self.summary_variant, name)


class FamilyVariant(SummaryVariantDelegate, FamilyInheritanceMixin):

    def __init__(self, summary_variant, family, genotype):
        SummaryVariantDelegate.__init__(self, summary_variant=summary_variant)
        FamilyInheritanceMixin.__init__(self, family=family, genotype=genotype)
        self.gt = np.copy(genotype)
        alleles = [summary_variant.ref_allele]

        for allele_index in self.calc_alt_alleles(self.gt):
            fa = summary_variant.alleles[allele_index]
            alleles.append(fa)
        self.alleles = alleles
        self.alt_alleles = AltAlleleItems(alleles[1:])

    @property
    def alts(self):
        if len(self.alt_alleles) == 0:
            return ""
        else:
            return ",".join([aa.alternative for aa in self.alt_alleles])

    def __repr__(self):
        if not self.alts:
            return '{}:{} {}(ref) {}'.format(
                self.chromosome, self.position,
                self.reference, self.family_id)
        else:
            return '{}:{} {}->{} {}'.format(
                self.chromosome, self.position,
                self.reference, self.alts,
                self.family_id)

    @property
    def best_st(self):
        if self._best_st is None:
            ref = (2 * np.ones(len(self.family), dtype=np.int8))
            unknown = np.any(self.gt == -1, axis=0)

            balt = []
            if len(self.alleles) == 1:
                alt_gt = np.zeros(self.gt.shape, dtype=np.int8)
                alt = np.sum(alt_gt, axis=0, dtype=np.int8)
                balt.append(alt)
            else:
                for anum, _ in enumerate(self.alt_alleles):
                    alt_gt = np.zeros(self.gt.shape, dtype=np.int8)
                    alt_gt[self.gt == (anum + 1)] = 1

                    alt = np.sum(alt_gt, axis=0, dtype=np.int8)
                    ref = ref - alt
                    balt.append(alt)

            best = [ref]
            best.extend(balt)
            print(best)

            self._best_st = np.stack(best, axis=0)
            self._best_st[:, unknown] = -1

        return self._best_st

    @property
    def variant_types(self):
        return set([aa.details.variant_type for aa in self.alt_alleles])

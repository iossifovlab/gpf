'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
from variants.family import VcfFamily
from variants.vcf_utils import vcf2cshl

from variants.attributes import VariantType, Inheritance
from timeit import itertools

# from icecream import ic


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
                 alternative=None, allele_index=1):

        self.chromosome = chromosome
        self.position = position
        self.reference = reference
        self.alternative = alternative
        self.allele_index = allele_index

    def __repr__(self):
        return '{}:{} {}->{} ({})'.format(
            self.chromosome, self.position,
            self.reference,
            self.alternative, self.allele_index)

    def __eq__(self, other):
        return self.chromosome == other.chromosome and \
            self.position == other.position and \
            self.reference == other.reference and \
            self.alternative == other.alternative

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

    def __repr__(self):
        return "{} {}".format(
            self.cshl_location,
            self.cshl_variant)

    @property
    def variant_type(self):
        vt = self.cshl_variant[0]
        if vt == 's':
            return VariantType.substitution
        elif vt == 'i':
            return VariantType.insertion
        elif vt == 'd':
            return VariantType.deletion
        elif vt == 'c':
            return VariantType.complex
        elif vt == 'C':
            return VariantType.CNV
        else:
            raise ValueError("unexpected variant type: {}".format(
                self.variant))

    @property
    def cshl_location(self):
        return "{}:{}".format(self.chrom, self.cshl_position)

    @staticmethod
    def from_vcf(chrom, position, reference, alternative):
        return VariantDetail(
            chrom, *vcf2cshl(position, reference, alternative))


class EffectGene(object):
    def __init__(self, symbol=None, effect=None):
        self.symbol = symbol
        self.effect = effect

    def __repr__(self):
        return "{}:{}".format(self.symbol, self.effect)

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_gene_effects(cls, gene_effects):
        result = []
        for symbol, effect in gene_effects:
            result.append(cls.from_tuple((symbol, effect)))
        return result

    @classmethod
    def from_string(cls, data):
        return cls.from_tuple(data.split(":"))

    @staticmethod
    def to_string(gene_effects):
        return str(gene_effects)

    @classmethod
    def from_tuple(cls, t):
        (symbol, effect) = tuple(t)
        return EffectGene(symbol, effect)


class EffectTranscript(object):

    def __init__(self, transcript_id, details):
        self.transcript_id = transcript_id
        self.details = details

    def __repr__(self):
        return "{}:{}".format(self.transcript_id, self.details)

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_tuple(cls, t):
        (transcript_id, details) = tuple(t)
        return EffectTranscript(transcript_id, details)

    @classmethod
    def from_effect_transcripts(cls, effect_transcripts):
        result = {}
        for transcript_id, details in effect_transcripts:
            result[transcript_id] = EffectTranscript.from_tuple(
                (transcript_id, details))
        return result


class Effect(object):
    def __init__(self, worst_effect, gene_effects, effect_transcripts):
        self.worst = worst_effect
        self.genes = EffectGene.from_gene_effects(gene_effects)
        self.transcripts = EffectTranscript.from_effect_transcripts(
            effect_transcripts)

    @classmethod
    def from_effects(cls, effect_type, effect_genes, transcripts):
        return Effect(effect_type, effect_genes, transcripts)


class SummaryVariant(VariantBase):
    """
    `SummaryVariant` represents summary variants for given position.

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
                 alternative,
                 allele_index=1,
                 effects=None,
                 frequency=None,
                 attributes=None):
        """
        Expected parameters of the constructor are:

        :param chromosome: chromosome label where variant is located
        :param position: position of the variant using *VCF* convention
        :param reference: reference DNA string
        :param alternative: alternative DNA string
        :param atts: additional variant attributes
        """
        super(SummaryVariant, self).__init__(
            chromosome, position, reference, alternative, allele_index)

        if alternative is None:
            self.details = None
        else:
            self.details = VariantDetail.from_vcf(
                chromosome, position, reference, alternative)

        self.effects = effects
        self.frequency = frequency

        if attributes is None:
            self.attributes = {}
        else:
            self.attributes = {}
            self.update_attributes(attributes)

    @property
    def location(self):
        """
        Returns string representation of location of the variant constructed
        from chromosome label and position "<chromsome>:<position>" in
        *VCF* convention.
        """
        return "{}:{}".format(self.chromosome, self.position)

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

    def update_attributes(self, atts):
        """
        updates additional attributes of variant using dictionary `atts`.
        """
        for key, val in atts.items():
            self.attributes[key] = val


class FamilyVariant(object):
    """
    Represent variant in a family. Description of the variant, it's effects,
    frequencies and other attributes come from instance of `SummaryVariant`
    class. `FamilyVariant` delegates all such requests to `SummaryVariant`
    object it contains.

    `FamilyVariant` combines `SummaryVariant` and family, represented by
    instance of `Family` or `VcfFamily` class.

    Additionaly, `FamilyVariant` contains genotype information for the
    specified `SummaryVariant` and specified `Family`. The genotype information
    is passed to `FamilyVariant` construction in the form of `gt` matrix.

    Genotype matrix `gt` has 2 rows (one for each individual allele) and the
    number of columns is equal to the number of individuals in the
    corresponging family.
    """

    def __init__(self, summary_variants, family, gt):
        self.family = family

        self.gt = np.copy(gt)

        unknown = np.any(self.gt == -1, axis=0)
        self.gt[:, unknown] = -1

        self.falt_alleles = self.calc_alt_alleles(self.gt)
        self.summary = [summary_variants[0]]

        for allele_index in self.falt_alleles:
            self.summary.append(summary_variants[allele_index])

        self._best_st = None
        self._inheritance = None

        self._variant_in_members = None
        self._variant_in_roles = None
        self._variant_in_sexes = None

    def __repr__(self):
        return '{}:{} {}->{} {}'.format(
            self.chromosome, self.position,
            self.reference, ",".join(self.alts),
            self.family_id)

    @classmethod
    def from_summary_variants(cls, sv, family, gt=None, vcf=None):
        if gt is None:
            assert vcf is not None
            assert isinstance(family, VcfFamily)

            gt = vcf.gt_idxs[family.alleles]
            gt = gt.reshape([2, len(family)], order='F')

        return [FamilyVariant(sv, family, gt)]

    @property
    def alts(self):
        """
        1-based list of alternative DNA strings describing the variant
        """
        return [sv.alternative for sv in self.summary[1:]]

    @property
    def alt_alleles(self):
        return self.summary.alt_alleles

#     @property
#     def alternatives(self):
#         return self.summary.alternatives

    @property
    def chromosome(self):
        return self.summary[0].chromosome

    @property
    def position(self):
        return self.summary[0].position

    @property
    def location(self):
        return "{}:{}".format(self.chromosome, self.position)

    @property
    def reference(self):
        return self.summary[0].reference

    @property
    def details(self):
        """
        1-based list of `VariantDetails`, that describes variant.
        """
        return self.summary.details

    @property
    def effects(self):
        """
        1-based list of `Effect`, that describes variant effects.
        """
        return self.summary.effects

    @property
    def frequencies(self):
        """
        0-base list of frequencies for variant.
        """
        return [sv.frequency for sv in self.summary]

    @property
    def best_st(self):
        if self._best_st is None:
            ref = (2 * np.ones(len(self.family), dtype=np.int8))
            unknown = np.any(self.gt == -1, axis=0)

            balt = []
            for anum, _ in enumerate(self.summary):
                alt_gt = np.zeros(self.gt.shape, dtype=np.int8)
                alt_gt[self.gt == (anum + 1)] = 1

                alt = np.sum(alt_gt, axis=0, dtype=np.int8)
                ref = ref - alt
                balt.append(alt)

            best = [ref]
            best.extend(balt)
            self._best_st = np.stack(best, axis=0)
            self._best_st[:, unknown] = -1

        return self._best_st

    @property
    def genotype(self):
        return self.gt.T

    @property
    def atts(self):
        """
        Additional attributes describing this variant.
        """
        return self.summary.atts

    def get_attribute(self, item, default=None):
        return [sv.get_attribute(item, default) for sv in self.summary]

    def has_attribute(self, item):
        return any([sv.has_attribute(item) for sv in self.summary])

    def __getitem__(self, item):
        return self.get_attribute(item)

    def __contains__(self, item):
        return self.has_attribute(item)

    def update_attributes(self, atts):
        for key, values in atts.items():
            for sv, val in zip(self.summary, itertools.cycle(values)):
                sv.update_attributes({key: val})

    @staticmethod
    def calc_alt_alleles(gt):
        return sorted(list(set(gt.flatten()).difference({-1, 0})))

    @classmethod
    def calc_alt_allele_index(cls, gt):
        alt_alleles = cls.calc_alt_alleles(gt)
        alt_count = len(alt_alleles)
        if alt_count > 1 or alt_count == 0:
            return None
        else:
            alt_index, = tuple(alt_alleles)
            return alt_index - 1

    @staticmethod
    def check_mendelian_trio(p1, p2, ch):
        m1 = (ch[0] == p1[0] or ch[0] == p1[1]) and \
            (ch[1] == p2[0] or ch[1] == p2[1])
        m2 = (ch[0] == p2[0] or ch[0] == p2[1]) and \
            (ch[1] == p1[0] or ch[1] == p1[1])
        return m1 or m2

    @staticmethod
    def check_denovo_trio(p1, p2, ch):
        new_alleles = set(ch).difference(set(p1) | set(p2))
        return bool(new_alleles)

    @staticmethod
    def check_omission_trio(p1, p2, ch):
        child_alleles = set(ch)
        p1res = False
        p2res = False

        if p1[0] == p1[1]:
            p1res = not bool(p1[0] in child_alleles)
        if p2[0] == p2[1]:
            p2res = not bool(p2[0] in child_alleles)

        return p1res or p2res

    @classmethod
    def calc_inheritance_trio(cls, p1, p2, ch):
        if cls.check_mendelian_trio(p1, p2, ch):
            return Inheritance.mendelian
        elif cls.check_denovo_trio(p1, p2, ch):
            return Inheritance.denovo
        elif cls.check_omission_trio(p1, p2, ch):
            return Inheritance.omission
        else:
            print("strange inheritance:", p1, p2, ch)
            return Inheritance.unknown

    def is_reference(self):
        return self.inheritance == Inheritance.reference

    def is_mendelian(self):
        return self.inheritance == Inheritance.mendelian

    def is_denovo(self):
        return self.inheritance == Inheritance.denovo

    def is_omission(self):
        return self.inheritance == Inheritance.omission

    @staticmethod
    def combine_inheritance(*inheritance):
        inherits = np.array([i.value for i in inheritance])
        inherits = np.array(inherits)
        if len(inherits) == 0 or np.any(inherits == Inheritance.unknown.value):
            return Inheritance.unknown
        elif np.all(inherits == Inheritance.mendelian.value):
            return Inheritance.mendelian
        elif np.all(np.logical_or(
                inherits == Inheritance.mendelian.value,
                inherits == Inheritance.denovo.value)):
            return Inheritance.denovo
        elif np.all(np.logical_or(
                inherits == Inheritance.mendelian.value,
                inherits == Inheritance.omission.value)):
            return Inheritance.omission
        elif np.all(np.logical_or(
                inherits == Inheritance.mendelian.value,
                np.logical_or(
                    inherits == Inheritance.omission.value,
                    inherits == Inheritance.denovo.value
                ))):
            return Inheritance.other
        else:
            print("strange inheritance:", inherits)
            return Inheritance.unknown

    @property
    def inheritance(self):
        if self._inheritance is None:
            inherits = []
            if np.any(self.gt == -1):
                self._inheritance = Inheritance.unknown
            elif np.all(self.gt == 0):
                self._inheritance = Inheritance.reference
            else:
                for _pid, trio in self.family.trios.items():
                    index = self.family.members_index(trio)
                    tgt = self.gt[:, index]
                    ch = tgt[:, 0]
                    p1 = tgt[:, 1]
                    p2 = tgt[:, 2]

                    inherits.append(self.calc_inheritance_trio(p1, p2, ch))
                self._inheritance = self.combine_inheritance(*inherits)

        return self._inheritance

    @property
    def members_in_order(self):
        return self.family.members_in_order

    @property
    def members_ids(self):
        return self.family.members_ids

    @property
    def family_id(self):
        return self.family.family_id

    @property
    def variant_in_members(self):
        if self._variant_in_members is None:
            gt = np.copy(self.gt)
            gt[gt == -1] = 0
            index = np.nonzero(np.sum(gt, axis=0))
            self._variant_in_members = set(self.members_ids[index])
        return self._variant_in_members

    @property
    def variant_in_roles(self):
        if self._variant_in_roles is None:
            self._variant_in_roles = [
                self.family.persons[pid]['role']
                for pid in self.variant_in_members
            ]
        return self._variant_in_roles

    @property
    def variant_in_sexes(self):
        if self._variant_in_sexes is None:
            self._variant_in_sexes = set([
                self.family.persons[pid]['sex']
                for pid in self.variant_in_members
            ])
        return self._variant_in_sexes


class VariantFactory(object):

    @staticmethod
    def summary_variants_from_records(records):
        """
        Factory method for constructing `SummaryVariants` from dictionary.

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

        row = records[0]
        summary_variants = [
            SummaryVariant(
                row['chrom'],
                row['position'],
                row['reference'],
                alternative=None,
                allele_index=0,
                frequency=row['af_reference_allele_freq']
            )
        ]
        for row in records:
            effects = Effect.from_effects(
                row['effect_type'], row['effect_gene'], row['effect_details'])

            sv = SummaryVariant(
                row['chrom'], row['position'],
                row['reference'], row['alternative'],
                row['allele_index'],
                effects,
                row['af_alternative_allele_freq'],
                attributes=row)
            summary_variants.append(sv)
        return summary_variants

    @staticmethod
    def family_variant_from_vcf(summary_variants, family, vcf):
        return FamilyVariant.from_summary_variants(
            summary_variants, family, vcf=vcf)

    @staticmethod
    def family_variant_from_gt(summary_variants, family, gt):
        return FamilyVariant.from_summary_variants(
            summary_variants, family, gt=gt)


class FamilyVariantSingle(FamilyVariant):

    def __init__(self, summary_variants, family, gt, alt_index):
        super(FamilyVariantSingle, self).__init__(
            summary_variants, family, gt)

        self.alt_index = alt_index
        assert len(self.falt_alleles) <= 1

    @classmethod
    def from_summary_variants(
            cls, summary_variants, family, gt=None, vcf=None):
        assert isinstance(family, VcfFamily)

        if gt is None:
            assert vcf is not None
            gt = vcf.gt_idxs[family.alleles]
            gt = gt.reshape([2, len(family)], order='F')

        alt_index = cls.calc_alt_allele_index(gt)
        alt_alleles = cls.calc_alt_alleles(gt)

        if alt_index is not None:
            return [
                cls(summary_variants,
                    family, gt, alt_index)
            ]
        elif len(alt_alleles) > 1:
            res = []

            for alt in sorted(alt_alleles):
                a_gt = np.copy(gt)
                mask = np.logical_not(
                    np.logical_or(
                        a_gt == 0,
                        a_gt == alt
                    ))
                a_gt[mask] = -1
                res.append(cls(summary_variants, family, a_gt, alt))
            return res
        else:
            res = []
            for alt_index in range(len(summary_variants) - 1):
                res.append(cls(summary_variants, family, gt, alt_index + 1))
            return res

        assert False

    @property
    def best_st(self):
        if self._best_st is None:
            ref = (2 * np.ones(len(self.family), dtype=np.int8))
            unknown = np.any(self.gt == -1, axis=0)
            alt_alleles = self.calc_alt_alleles(self.gt)
            assert len(alt_alleles) <= 1

            if not alt_alleles:
                alt = np.zeros(len(self.family), dtype=np.int8)
            else:
                anum = next(iter(alt_alleles))
                alt_gt = np.zeros(self.gt.shape, dtype=np.int8)
                alt_gt[self.gt == anum] = 1

                alt = np.sum(alt_gt, axis=0, dtype=np.int8)
                ref = ref - alt

            best = [ref, alt]
            self._best_st = np.stack(best, axis=0)
            self._best_st[:, unknown] = -1

        return self._best_st


class VariantFactorySingle(VariantFactory):

    @staticmethod
    def family_variant_from_vcf(summary_variant, family, vcf):
        return FamilyVariantSingle.from_summary_variants(
            summary_variant, family, vcf=vcf)

    @staticmethod
    def family_variant_from_gt(summary_variant, family, gt):
        return FamilyVariantSingle.from_summary_variants(
            summary_variant, family, gt=gt)

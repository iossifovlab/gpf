#!/usr/bin/env python
import numpy as np
import argparse
import gzip
from collections import OrderedDict
from csv import DictReader
from multiprocessing import Pool
from functools import partial

from pedigrees.pedigree_reader import PedigreeReader
from pedigrees.pedigrees import FamilyConnections
from converters.dae2vcf import VcfVariant, vcfVarFormat, VcfVariantSample, \
    VcfWriter


def has_variant(frequency, choices_count=1):
    return np.random.choice(
        [False, True], p=[1-frequency, frequency], size=choices_count)


AFFECTED_ALLELES_CHOICES = [[0, 0], [1, 0], [1, 1]]


def affected_inherited_alleles(dad_affected_alleles, mom_affected_alleles):
    from_dad = np.random.choice(AFFECTED_ALLELES_CHOICES[dad_affected_alleles])
    from_mom = np.random.choice(AFFECTED_ALLELES_CHOICES[mom_affected_alleles])

    return from_dad + from_mom


def generate_variants_func(self, variant):
    return self._generate_variants(variant)


class FamilyVariantGenerator(object):

    def __init__(
            self, variants_file, families, frequency_column='all.altFreq',
            chromosome_column='chr', position_column='position',
            variant_column='variant'):
        self.variants_file = variants_file
        self.families = families

        self.frequency_column = frequency_column
        self.chromosome_column = chromosome_column
        self.position_column = position_column
        self.variant_column = variant_column

    def generate(self, writer):
        result = 0
        pool = Pool(6)

        with gzip.open(self.variants_file) as variants_file:
            reader = DictReader(variants_file, delimiter='\t')

            for generated_variants in pool.imap(
                    partial(generate_variants_func, self), reader,
                    chunksize=1000):
                for generated in generated_variants.values():
                    writer.write_variant(generated)

                result += len(generated_variants)

        return result

    def _generate_variants(self, variant):
        result = self._generate_for_independent_members(variant)
        self._generate_with_mendelian_inheritance(result)

        return result

    def _generate_for_independent_members(self, variant):

        # with gzip.open(self.variants_file) as variants_file:
        # tabix_variants = TabixCsvDictReader(self.variants_file)
        #     reader = DictReader(variants_file, delimiter='\t')

        variants = OrderedDict()
        choices_count = \
            sum(len(f.independent_members()) for f in self.families) * 2

        # print(read_variant)
        frequency = float(variant[self.frequency_column]) / 100.0

        if frequency == 0.0:
            return variants

        # print(choices_count)

        choices = has_variant(frequency, choices_count)
        choices_index = 0

        chromosome = variant[self.chromosome_column]
        position = int(variant[self.position_column])
        _, _, reference, alternative = vcfVarFormat(
            "{}:{}".format(chromosome, position),
            variant[self.variant_column])

        key = VcfVariant.get_variant_key(
            chromosome, position=position, reference=reference,
            alternative=alternative)

        for family in self.families:
            for member in family.independent_members():
                allele1_has_variant = choices[choices_index]
                choices_index += 1
                allele2_has_variant = choices[choices_index]
                choices_index += 1

                alternative_alleles_count = \
                    int(allele1_has_variant) + int(allele2_has_variant)

                if alternative_alleles_count == 0:
                    continue
                genotype = '1/1'

                if key not in variants:
                    variants[key] = VcfVariant(
                        chromosome=chromosome,
                        position=position,
                        reference=reference,
                        alternative=alternative,
                        format_='GT:AD'
                    )

                if alternative_alleles_count == 1:
                    genotype = '0/1'

                v = variants[key]

                v.samples[member.id] = VcfVariantSample(
                    member.id,
                    genotype,
                    '0,0'
                )

        return variants

    def _generate_with_mendelian_inheritance(self, variants_in_independent):
        for family in self.families:
            connected_family = FamilyConnections.from_pedigree(family)
            independent_members = set(family.independent_members())

            connected_family.add_ranks()

            current_rank = 0
            max_rank = connected_family.max_rank()
            # print("max_rank", max_rank)

            while current_rank <= max_rank:
                individuals_on_level = connected_family \
                    .get_individuals_with_rank(current_rank)

                for individual in individuals_on_level:
                    if individual.member in independent_members:
                        continue
                    self._mendelian_inheritance(
                        individual, variants_in_independent
                    )

                current_rank += 1

    def _mendelian_inheritance(self, individual, variants_in_independent):
        # print("individual", individual)
        parents = individual.parents

        dad_id = parents.father.member.id
        mom_id = parents.mother.member.id

        # print(dad_id, mom_id)

        for variant in variants_in_independent.values():
            dad_affected_alleles_count = \
                self._get_affected_alleles_count(variant, dad_id)
            mom_affected_alleles_count = \
                self._get_affected_alleles_count(variant, mom_id)

            if dad_affected_alleles_count + mom_affected_alleles_count == 0:
                continue

            affected_alleles = affected_inherited_alleles(
                dad_affected_alleles_count, mom_affected_alleles_count)

            if affected_alleles != 0:
                variant.samples[individual.member.id] = VcfVariantSample(
                    individual.member.id,
                    '0/1' if affected_alleles == 1 else '1/1',
                    '0,0'
                )

    @staticmethod
    def _get_affected_alleles_count(variant, sample):
        result = 0

        variant_sample = variant.get_sample(sample)
        if variant_sample:
            result = variant_sample.alternative_alleles_count()

        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'variants', help='tabix file with variants and frequencies')
    parser.add_argument(
        'pedigree',
        help='pedigree file of the families for which to generate variants')
    parser.add_argument(
        '--output', help='output vcf file', default='output.vcf')

    args = parser.parse_args()

    pedigree_reader = PedigreeReader()
    families = pedigree_reader.read_file(args.pedigree)

    generator = FamilyVariantGenerator(args.variants, families)

    ordered_cohort = list({i.id for f in families for i in f.members})
    writer = VcfWriter(args.output, ordered_cohort)

    writer.open()

    variants_count = generator.generate(writer)

    writer.close()

    print("variants generated: {}".format(variants_count))


if __name__ == '__main__':
    main()

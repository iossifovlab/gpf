#!/usr/bin/env python
import numpy as np
import argparse
from pedigrees.pedigree_reader import PedigreeReader
from pedigrees.pedigrees import FamilyConnections
from utils.tabix_csv_reader import TabixCsvDictReader
from converters.dae2vcf import VcfVariant, vcfVarFormat, VcfVariantSample, \
    VcfWriter

from collections import OrderedDict, defaultdict


def has_variant(frequency):
    return np.random.choice([False, True], p=[1-frequency, frequency])


def affected_inherited_alleles(dad_affected_alleles, mom_affected_alleles):
    from_dad = np.random.choice(([1] * dad_affected_alleles + [0, 0])[:2])
    from_mom = np.random.choice(([1] * mom_affected_alleles + [0, 0])[:2])

    return from_dad + from_mom


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

    def generate(self):
        variants = self._generate_for_independent_members()
        print("generated for independent members")
        self._generate_with_mendelian_inheritance(variants)
        return variants

    def _generate_for_independent_members(self):
        tabix_variants = TabixCsvDictReader(self.variants_file)

        variants = OrderedDict()

        for read_variant in tabix_variants:
            frequency = float(read_variant[self.frequency_column]) / 100.0

            if frequency == 0.0:
                continue

            chromosome = read_variant[self.chromosome_column]
            position = int(read_variant[self.position_column])
            _, _, reference, alternative = vcfVarFormat(
                "{}:{}".format(chromosome, position),
                read_variant[self.variant_column])

            key = VcfVariant.get_variant_key(
                chromosome, position=position, reference=reference,
                alternative=alternative)

            for family in self.families:
                for member in family.independent_members():
                    allele1_has_variant = has_variant(frequency)
                    allele2_has_variant = has_variant(frequency)

                    alternative_alleles_count = \
                        int(allele1_has_variant) + int(allele2_has_variant)

                    if alternative_alleles_count == 0:
                        continue
                    genotype = '0/0'

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
                    elif alternative_alleles_count == 2:
                        genotype = '1/1'

                    variant = variants[key]

                    variant.samples[member.id] = VcfVariantSample(
                        member.id,
                        genotype,
                        '0,0'
                    )

        tabix_variants.close()
        return variants

    def _generate_with_mendelian_inheritance(self, variants_in_independent):
        for family in self.families:
            connected_family = FamilyConnections.from_pedigree(family)
            independent_members = set(family.independent_members())

            connected_family.add_ranks()

            current_rank = 0
            max_rank = connected_family.max_rank()

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
    parser.add_argument('--output', help='output vcf file', default='output.vcf')

    args = parser.parse_args()

    pedigree_reader = PedigreeReader()
    families = pedigree_reader.read_file(args.pedigree)

    generator = FamilyVariantGenerator(args.variants, families)

    variants = generator.generate()
    ordered_cohort = list({i.id for f in families for i in f.members})

    writer = VcfWriter(args.output, ordered_cohort)

    writer.open()

    for variant in variants.values():
        writer.write_variant(variant)

    writer.close()

    print("variants generated: {}".format(len(variants)))


if __name__ == '__main__':
    main()

#!/usr/bin/env python2.7

from DAE import genomesDB
from datasets.datasets_factory import DatasetsFactory
from datasets.datasets_factory import DatasetsConfig
import pysam
import re
import itertools


GA = genomesDB.get_genome()
gmDB = genomesDB.get_gene_models()

subRE = re.compile('^sub\(([ACGT])->([ACGT])\)$')
insRE = re.compile('^ins\(([ACGT]+)\)$')
delRE = re.compile('^del\((\d+)\)$')


class DaeToVcf(object):

    def convert(self, dataset_id, output_filename):
        dataset_config = DatasetsConfig()
        factory = DatasetsFactory(dataset_config)
        dataset = factory.get_dataset(dataset_id)

        if dataset is None:
            raise ValueError(
                'no such dataset: {}, available: {}'.format(
                    dataset_id, dataset_config.get_dataset_ids()
                )
            )
        kwargs = {
            "presentInParent": [
                "father only",
                "mother only",
                "mother and father",
                "neither"
            ],
            "rarity": {
                "ultraRare": True,
                "minFreq": None,
                "maxFreq": None
            }
        }

        cohort = set()

        variants = dataset.get_transmitted_variants(safe=True, **kwargs)
        variant_records = []
        total = 0
        counts = 0

        for variant in itertools.islice(variants, 1000): # FIXME: remove this
            total += 1
            try:

                chromosome, position, reference, alternative = \
                    vcfVarFormat(variant.location, variant.variant)

                variant_records.append(VcfVariant(
                    chromosome=chromosome,
                    position=position,
                    reference=reference,
                    alternative=alternative,
                    quality=100,
                    info={'END': position + len(alternative)},
                    format_={},
                    samples=[],
                    metadata=self._get_metadata_for_variant(variant)
                ))
                cohort |= set(variant.memberInOrder)
            except (AssertionError, KeyError, NotImplementedError) as e:
                print(e, variant)
                continue
            counts += 1

        cohort_set = set(['FAMILY_' + str(x.personId) for x in cohort])
        assert len(cohort_set) == len(cohort), "cohort with different count"

        print("Cohort length: {}".format(len(cohort)))
        print("Variants count: {}", len(variant_records))

        print("{} variants with counts, {} total ({}%)".format(
            counts, total,
            (counts / float(total)) * 100 if total != 0 else float("inf")
        ))

        ordered_cohort = list(cohort)
        samples_names = [str(x.personId) for x in ordered_cohort]

        for variant in variant_records:
            variant.samples = self._generate_samples(variant, ordered_cohort)

        writer = VcfWriter(output_filename, samples_names)
        writer.write_variants(variant_records)

    def _get_metadata_for_variant(self, variant):
        return {
            p.personId: {
                'GT': self._get_genotype_info(index, variant),
                'AD': self._get_alleles_coverage_info(index, variant)
            } for index, p in enumerate(variant.memberInOrder)
        }

    @staticmethod
    def _generate_samples(variant, cohort):
        empty = {}
        samples = []
        for member in cohort:
            samples.append(variant.metadata.get(member.personId, empty))

        return samples

    @staticmethod
    def _get_genotype_info(index, variant):
        assert len(variant.bestSt[0]) > index, 'Ref index out of bounds'
        assert len(variant.bestSt[1]) > index, 'Alt index out of bounds'
        ref = variant.bestSt[0][index]
        alt = variant.bestSt[1][index]

        if ref == 2 and alt == 0:
            return ('0', '0')
        elif ref == 1 and alt == 1:
            return ('0', '1')
        raise NotImplementedError(
            'Unknown genotype - ref={}, alt={}'.format(ref, alt)
        )

    @staticmethod
    def _get_alleles_coverage_info(index, variant):
        assert len(variant.counts[0]) > index, 'Ref index out of bounds'
        assert len(variant.counts[1]) > index, 'Alt index out of bounds'

        return (str(variant.counts[0][index]), str(variant.counts[1][index]))


class VcfWriter(object):

    def __init__(self, filename, samples_labels):
        self.filename = filename
        self.samples_labels = samples_labels

    def write_variants(self, variants_array):
        chromosomes = set(str(v.chromosome) for v in variants_array)
        header = self._prepare_header(chromosomes)
        variants_array = sorted(
            variants_array, key=lambda v: (v.chromosome, v.position))

        vcf_file = pysam.VariantFile(self.filename, 'wb', header=header)
        print(header.info.header)

        for variant in variants_array:

            row = vcf_file.new_record(
                contig=variant.chromosome,
                alleles=(variant.reference, variant.alternative),
                filter=variant.filter,
                id=variant.id,
                start=variant.position,
                stop=variant.info['END'],
                qual=variant.quality,
                info=variant.info,
                samples=variant.samples
            )

            vcf_file.write(row)

        vcf_file.close()

    def _prepare_header(self, additional_chromosomes=set()):
        header = pysam.VariantHeader()
        header.add_meta('fileformat', value='VCFv4.1')
        header.formats.add('GT', 2, 'String', 'Genotype')
        header.formats.add(
            'AD', '.', 'String',
            'Allelic depths for the ref and alt alleles in the order listed')

        for sample in self.samples_labels:
            header.add_sample(sample)

        header.info.add('END', 1, 'Integer', 'Stop position of the interval')

        chromosomes = set([str(num) for num in range(1, 23)] + ['X', 'Y'])
        chromosomes |= additional_chromosomes
        chromosomes = sorted(list(chromosomes))

        for chromosome in chromosomes:
            header.contigs.add(chromosome)

        return header


class VcfVariant(object):

    def __init__(self, chromosome='.', position=0, id_='.', reference='.',
                 alternative='.', quality=100, filter_='.', info=None,
                 format_=None, samples=None, metadata=None):
        if not samples:
            samples = []
        if not metadata:
            metadata = {}

        self.chromosome = chromosome
        self.position = position
        self.id = id_
        self.reference = reference
        self.alternative = alternative
        self.quality = quality
        self.filter = filter_
        self.info = info
        self.format = format_
        self.samples = samples
        self.metadata = metadata

    def __repr__(self):
        return '{}:{} {}->{} ({}){}'.format(
            self.chromosome, self.position, self.reference, self.alternative,
            len(self.samples), self.samples)


class VcfVariantSample(object):

    def __init__(self, genotype, allele_depth, **kwargs):
        self.genotype = genotype
        self.allele_depth = allele_depth
        self.kwargs = kwargs


def vcfVarFormat(loc, var):
    chr, pos = loc.split(":")
    pos = int(pos)

    mS = subRE.match(var)
    if mS:
        return chr, pos, mS.group(1), mS.group(2)

    mI = insRE.match(var)
    # print(mI)
    if mI:
        sq = mI.group(1)
        reference = GA.getSequence(chr, pos-1, pos-1)
        return chr, pos-1, reference, reference+sq

    mD = delRE.match(var)
    if mD:
        l = int(mD.group(1))
        reference = GA.getSequence(chr, pos-1, pos+l-1)
        return chr, pos-1, reference, reference[0]

    raise NotImplementedError('weird variant: ' + var)


def main():
    converter = DaeToVcf()
    converter.convert('SSC', './output.vcf')


if __name__ == '__main__':
    main()

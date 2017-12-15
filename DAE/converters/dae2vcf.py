#!/usr/bin/env python2.7

from DAE import genomesDB
from datasets.datasets_factory import DatasetsFactory
from datasets.datasets_factory import DatasetsConfig
import pysam
import re


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

        variants = dataset.get_denovo_variants(safe=True)
        variant_records = []
        total = 0
        counts = 0
        for variant in variants:
            total += 1
            try:
                variant.countsAtt = 'Count'
                variant.counts
                # print("dir one:", dir(variant))
                # print('location', variant.location)
                # print('family_id', variant.familyId)
                # print('variant', variant.variant)
                # print('bestSt', variant.bestSt, variant.bestStAtt)
                # print('member', variant.memberInOrder)
                # print('counts', variant.counts)

                chromosome, position, reference, alternative = \
                    vcfVarFormat(variant.location, variant.variant)
                # print(chromosome, position, reference, alternative)

                variant_records.append(VcfVariant(
                    chromosome=chromosome,
                    position=position,
                    reference=reference,
                    alternative=alternative,
                    quality=100,
                    # info={'END': position + 1},
                    # format_={},
                    samples=[]
                ))
            except KeyError:
                continue
            counts += 1

        print("{} variants with counts, {} total ({}%)".format(
            counts, total, (counts / float(total)) * 100
        ))

        writer = VcfWriter(output_filename)
        writer.write_variants(variant_records)


class VcfWriter(object):

    def __init__(self, filename):
        self.filename = filename

    def write_variants(self, variants_array):
        chromosomes = [v.chromosome for v in variants_array]
        header = self._prepare_header(set(chromosomes))
        variants_array = sorted(
            variants_array, key=lambda v: (v.chromosome, v.position))

        # FIXME: add samples

        vcf_file = pysam.VariantFile(self.filename, 'w', header=header)
        rows = []

        for variant in variants_array:
            rows.append(header.new_record(
                contig=variant.chromosome,
                alleles=(variant.reference, variant.alternative),
                filter=variant.filter,
                id=variant.id,
                start=variant.position - 1,
                stop=variant.position + 1,
                qual=variant.quality,
                info=variant.info,
                samples=variant.samples
            ))
        print('created rows')

        for row in rows:
            vcf_file.write(row)

        vcf_file.close()

    def _prepare_header(self, additional_chromosomes=set()):
        header = pysam.VariantHeader()
        header.add_meta('fileformat', value='VCFv4.1')
        header.formats.add('GT', 1, 'String', 'Genotype')
        header.formats.add(
            'AD', '.', 'Integer',
            'Allelic depths for the ref and alt alleles in the order listed')
        header.info.add('END', 1, 'Integer', 'Stop position of the interval')

        header.add_sample('SAMPLE01')

        chromosomes = set([str(num) for num in range(1, 23)] + ['X', 'Y'])
        chromosomes |= additional_chromosomes
        chromosomes = sorted(list(chromosomes))

        for chromosome in chromosomes:
            header.contigs.add(chromosome)

        return header


class VcfVariant(object):

    def __init__(self, chromosome='.', position=0, id_='.', reference='.',
                 alternative='.', quality=100, filter_='.', info=None,
                 format_=None, samples=None):
        # if not info:
        #     info = {}
        if not samples:
            samples = []

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


class VcfVariantSample(object):

    def __init__(self, genotype, allele_depth, **kwargs):
        # if kwargs
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
    if mI:
        sq = mI.group(1)
        reference = GA.getSequence(chr, pos-1, pos-1)
        return chr, pos-1, reference, reference+sq

    mD = delRE.match(var)
    if mD:
        l = int(mD.group(1))
        reference = GA.getSequence(chr, pos-1, pos+l-1)
        return chr, pos-1, reference, reference[0]

    raise Exception('weird variant:' + var)



def main():
    converter = DaeToVcf()
    converter.convert('AGRE_WG', './output.vcf')


if __name__ == '__main__':
    main()

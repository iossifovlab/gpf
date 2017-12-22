#!/usr/bin/env python2.7

from DAE import genomesDB
from datasets.datasets_factory import DatasetsFactory
from datasets.datasets_factory import DatasetsConfig
import re
import itertools
import collections
import vcf as PyVCF
from vcf.parser import _Contig, _Format, _Info, _Filter, _Call
from vcf.model import make_calldata_tuple


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
            },
            "regions": ["X:0-100000000"]
        }

        cohort = set()

        variants = dataset.get_transmitted_variants(safe=True, **kwargs)
        variant_records = []
        total = 0
        counts = 0

        for variant in itertools.islice(variants, 1000):
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
                    info={'END': position + len(alternative) - 1},
                    format_='GT:AD',
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
        print("Variants count: {}".format(len(variant_records)))

        print("{} variants with counts, {} total ({}%)".format(
            counts, total,
            (counts / float(total)) * 100 if total != 0 else float("inf")
        ))

        ordered_cohort = list(cohort)
        samples_names = [str(x.personId) for x in ordered_cohort]

        chromosomes = set(str(v.chromosome) for v in variant_records)

        writer = VcfWriter(output_filename, samples_names, chromosomes)
        writer.open()

        for variant in variant_records:
            variant.samples = self._generate_samples(variant, ordered_cohort)
            writer.write_variant(variant)
            variant.samples = None

        writer.close()

    def _get_metadata_for_variant(self, variant):
        return {
            p.personId: {
                'GT': self._get_genotype_info(index, variant),
                'AD': self._get_alleles_coverage_info(index, variant)
            } for index, p in enumerate(variant.memberInOrder)
        }

    @staticmethod
    def _generate_samples(variant, cohort):
        empty = {'GT': '.', 'AD': '.'}
        get = variant.metadata.get
        people_ids = itertools.imap(lambda x: x.personId, cohort)
        samples = map(lambda i: get(i, empty), people_ids)

        return samples

    @staticmethod
    def _get_genotype_info(index, variant):
        assert len(variant.bestSt[0]) > index, 'Ref index out of bounds'
        assert len(variant.bestSt[1]) > index, 'Alt index out of bounds'
        ref = variant.bestSt[0][index]
        alt = variant.bestSt[1][index]

        if ref == 2 and alt == 0:
            return '0/0'
        elif ref == 1 and alt == 1:
            return '0/1'
        elif ref == 1 and alt == 0:
            return '0'
        elif ref == 0 and alt == 1:
            return '1'
        raise NotImplementedError(
            'Unknown genotype - ref={}, alt={}'.format(ref, alt)
        )

    @staticmethod
    def _get_alleles_coverage_info(index, variant):
        assert len(variant.counts[0]) > index, 'Ref index out of bounds'
        assert len(variant.counts[1]) > index, 'Alt index out of bounds'

        ref = variant.bestSt[0][index]
        alt = variant.bestSt[1][index]

        if ref + alt == 1:
            if ref == 1:
                return str(variant.counts[0][index])

            return str(variant.counts[1][index])

        return '{},{}'.format(
            variant.counts[0][index], variant.counts[1][index])


class VcfWriter(object):

    def __init__(self, filename, samples_labels, additional_chromosomes=set()):
        self.filename = filename
        self.samples_labels = samples_labels
        self.writer = None
        self.additional_chromosomes = additional_chromosomes

    def open(self):
        if self.writer is not None:
            return

        f = open(self.filename, 'w')
        template = self._prepare_template(set(self.additional_chromosomes))
        self.writer = PyVCF.Writer(f, template)

    def close(self):
        if self.writer is None:
            return

        self.writer.close()
        self.writer = None

    def _assert_open(self):
        assert self.writer is not None

    def write_variant(self, variant):
        self._assert_open()

        if ('END' in variant.info and
                variant.info['END'] == variant.position):
            variant.info.pop('END')

        record = PyVCF.model._Record(
            variant.chromosome,
            variant.position,
            variant.id,
            variant.reference,
            [PyVCF.model._Substitution(variant.alternative)],
            variant.quality,
            variant.filter,
            variant.info,
            variant.format,
            {key: index
             for index, key in enumerate(self.samples_labels)}
        )
        reverse_map = {v: k for k, v in record._sample_indexes.items()}
        calldata_tuple = make_calldata_tuple(variant.format.split(':'))

        samples = map(
            lambda x: _Call(record, reverse_map[x[0]],
                            calldata_tuple(**x[1])),
            enumerate(variant.samples))

        record.samples = samples
        self.writer.write_record(record)

    def _prepare_template(self, additional_chromosomes=set()):
        contigs = set([str(num) for num in range(1, 23)] + ['X', 'Y'])
        contigs |= additional_chromosomes
        contigs = sorted(list(contigs))

        samples = self.samples_labels

        template = PyVcfTemplate(
            metadata={'fileformat': 'VCFv4.2'},
            formats={
                'GT': [1, 'String', 'Genotype'],
                'AD': ['.', 'Integer',
                       'Allelic depths for the ref and alt alleles in the order'
                       ' listed']
            },
            samples=samples,
            contigs=contigs,
            infos={
                'END': [1, 'Integer', 'Stop position of the interval']
            },
            filters={
                'PASS': 'All filters passed'
            }
        )

        return template


class VcfVariant(object):

    def __init__(self, chromosome='.', position=0, id_='.', reference='.',
                 alternative='.', quality=100, filter_='.', info=None,
                 format_='.', samples=None, metadata=None):
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


class PyVcfTemplate(object):

    def __init__(self, infos=None, metadata=None, formats=None, filters=None,
                 alts=None, contigs=None, samples=None):
        if infos is None:
            infos = {}
        if metadata is None:
            metadata = {}
        if formats is None:
            formats = {}
        if filters is None:
            filters = {}
        if alts is None:
            alts = {}
        if contigs is None:
            contigs = []
        if samples is None:
            samples = []

        self.infos = {k: self._get_info(k, *v) for k, v in infos.items()}
        self.metadata = metadata
        self.formats = {k: _Format(k, *v) for k, v in formats.items()}
        self.filters = {k: _Filter(k, v) for k, v in filters.items()}
        self.alts = alts
        self.contigs = collections.OrderedDict(
            [(x, _Contig(x, None)) for x in contigs])
        self._column_headers = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL',
                                'FILTER', 'INFO', 'FORMAT']
        self.samples = samples

    @staticmethod
    def _get_info(name, number, type, description):
        return _Info(name, number, type, description, '_', '_')



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

    raise NotImplementedError('weird variant: ' + var)


def main():
    converter = DaeToVcf()
    converter.convert('SSC', './output.vcf')


if __name__ == '__main__':
    main()

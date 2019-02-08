#!/usr/bin/env python2.7

from DAE import genomesDB
from datasets.datasets_factory import DatasetsFactory
from datasets.datasets_factory import DatasetsConfig
import re
import itertools
import collections
import vcf as PyVCF  # @UnresolvedImport
from pprint import pprint
from vcf.parser import _Contig, _Format, _Info, _Filter, _Call  # @UnresolvedImport
from vcf.model import make_calldata_tuple  # @UnresolvedImport
import copy


GA = genomesDB.get_genome()  # @UndefinedVariable
gmDB = genomesDB.get_gene_models()  # @UndefinedVariable

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
                "ultraRare": False,
                "minFreq": 0,
                "maxFreq": 100
            },
            "effectTypes": [
                "Nonsense",
                "Frame-shift",
                "Splice-site",
                "Missense",
                "No-frame-shift",
                "noStart",
                "noEnd",
                "Synonymous",
                "Non coding",
                "Intron",
                "Intergenic",
                "3'-UTR",
                "5'-UTR",
                "CNV+",
                "CNV-"
            ],
            "familyIds": [
                "AU1921202_AU1921201",
                "AU1921102_AU1921101",
                "AU1921212_AU1921211",
                # "AU1072202_AU1072201",
                # "AU1072212_AU1072211"
            ],
            "gender": [
                "female",
                "male",
                # "unspecified"
            ],
            "variantTypes": [
                "sub",
                "ins",
                "del",
                "CNV"
            ],
            # "regions": ["22:0-51304566"],
            "regions": ["1:0-249250621"],
        }

        cohort = []

        variants = dataset.get_transmitted_variants(safe=True, **kwargs)
        total = 0
        counts = 0

        variant_map = collections.OrderedDict()
        with_difference = 0
        without_difference = 0

        for variant in itertools.islice(variants, 1000):
            total += 1
            try:

                chromosome, position, reference, alternative = \
                    vcfVarFormat(variant.location, variant.variant)
                end = position + max(len(reference), len(alternative)) - 1

                if len(chromosome) > 2:
                    print("skipping variant in {}".format(chromosome))
                    total -= 1
                    continue

                key = VcfVariant.get_variant_key(
                    chromosome, position, reference, alternative)

                if key in variant_map:
                    cached_variant = variant_map[key]
                    samples = self._get_samples_for_variant(variant)
                    cached_samples = cached_variant.samples

                    common = set(samples.keys()) & \
                        set(cached_samples.keys())

                    for each in common:
                        person1 = samples[each]
                        person2 = cached_samples[each]

                        ad1s = map(int, person1.allele_depth.split(','))
                        ad2s = map(int, person2.allele_depth.split(','))

                        if ad2s[1] > ad1s[1]:
                            person1.allele_depth = person2.allele_depth

                    cached_samples.update(samples)
                else:
                    variant_map[key] = VcfVariant(
                        chromosome=chromosome,
                        position=position,
                        reference=reference,
                        alternative=alternative,
                        info={'END': end},
                        format_='GT:AD',
                        samples=self._get_samples_for_variant(variant)
                    )
                cohort += variant.memberInOrder
            except (AssertionError, KeyError, NotImplementedError) as e:
                print(e, variant)
                continue
            counts += 1

        cohort_set = set(str(x.personId) for x in cohort)
        ordered_cohort = list(cohort_set)

        print("variants with different counts: {}".format(with_difference))
        print("variants with same counts: {}".format(without_difference))
        print("Cohort length: {}".format(len(ordered_cohort)))
        print("output variants count: {}".format(len(variant_map.values())))

        print("{} input variants with counts, {} total ({}%)".format(
            counts, total,
            (counts / float(total)) * 100 if total != 0 else float("inf")
        ))

        chromosomes = set(str(v.chromosome) for v in variant_map.values())

        writer = VcfWriter(output_filename, ordered_cohort, chromosomes)
        writer.open()

        for variant in variant_map.values():
            writer.write_variant(variant)
            # variant.samples = None

        writer.close()

    @staticmethod
    def _print_variant_info_about_person(variant, person_id):
        variant = variant
        members_in_order = variant.memberInOrder
        member1_index = (i for i, v in enumerate(members_in_order) if v.personId == person_id).next()
        print('family {}'.format(variant.familyId))
        print('variant {} {}'.format(variant.location, variant.variant))
        print(
            'variant memberInOrder position: {}, counts: {} {}'.format(
                member1_index, variant.counts[0][member1_index],
                variant.counts[1][member1_index]
            )
        )
        print('variant memberInOrder')
        pprint(members_in_order)
        print('variant counts:')
        pprint(variant.counts)

    def _get_samples_for_variant(self, variant):
        return {
            p.personId: VcfVariantSample(
                p.personId,
                genotype=self._get_genotype_info(index, variant),
                allele_depth=self._get_alleles_coverage_info(index, variant)
            )
            for index, p in enumerate(variant.memberInOrder)
        }

    ORDERED_GENOTYPE_INFO = ['0/0', '0', '0/1', '1', '1/1']

    @staticmethod
    def _get_genotype_info(index, variant):
        assert len(variant.bestSt[0]) > index, 'Ref index out of bounds'
        assert len(variant.bestSt[1]) > index, 'Alt index out of bounds'
        ref = variant.bestSt[0][index]
        alt = variant.bestSt[1][index]

        # equivalent to:
        # if ref == 2 and alt == 0:
        #     return '0/0'
        # if ref == 1 and alt == 1:
        #     return '0/1'
        # if ref == 1 and alt == 0:
        #     return '0'
        # if ref == 0 and alt == 1:
        #     return '1'
        # if ref == 0 and alt == 2:
        #     return '1/1'
        genotype_index = alt - ref + 2

        assert 0 <= genotype_index < len(DaeToVcf.ORDERED_GENOTYPE_INFO),\
            'unknown genotype: ref = {}, alt = {}'.format(ref, alt)

        return DaeToVcf.ORDERED_GENOTYPE_INFO[genotype_index]

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
        self._writer = None
        self.additional_chromosomes = additional_chromosomes

    def open(self):
        if self._writer is not None:
            return

        f = open(self.filename, 'w')
        template = self._prepare_template(set(self.additional_chromosomes))
        self._writer = PyVCF.Writer(f, template)

    def close(self):
        if self._writer is None:
            return

        self._writer.close()
        self._writer = None

    def _assert_open(self):
        assert self._writer is not None

    def write_variant(self, variant):
        self._assert_open()
        # print("SAMPLES", variant.samples)

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

        # variant.samples = self._get_public_sample_data(variant_samples)
        samples = self._generate_samples(variant, self.samples_labels)

        record_samples = map(
            lambda x: _Call(record, reverse_map[x[0]],
                            calldata_tuple(**x[1])),
            enumerate(samples))

        record.samples = record_samples
        self._writer.write_record(record)

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

    @staticmethod
    def _generate_samples(variant, cohort):
        empty = {'GT': '0/0', 'AD': '0,0'}

        get = collections.OrderedDict(
            ((k, v.to_dict())
             for k, v in variant.samples.items())).get
        samples = map(lambda i: get(i, empty), cohort)

        return samples


class VcfVariant(object):

    def __init__(self, chromosome='.', position=0, id_='.', reference='.',
                 alternative='.', quality=100, filter_='.', info=None,
                 format_='.', samples=None):
        if not samples:
            samples = {}
        if not info:
            info = {}

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

    def __repr__(self):
        return '{}:{} {}->{} ({}):{}'.format(
            self.chromosome, self.position, self.reference, self.alternative,
            len(self.samples), self.samples)

    def has_variant(self, sample_id):
        return any(
            s.sample_id == sample_id and s.genotype != '0/0'
            for s in self.samples.values())

    def get_sample(self, sample_id):
        return self.samples.get(sample_id, None)

    @staticmethod
    def get_variant_key(chromosome, position, reference, alternative):
        return "{}:{};{}:{}".format(
                    chromosome, position, reference, alternative)


class VcfVariantSample(object):

    def __init__(self, sample_id, genotype, allele_depth, **metadata):
        self.sample_id = sample_id
        self.genotype = genotype
        self.allele_depth = allele_depth
        self.metadata = metadata

    def to_dict(self):
        return {
            'GT': self.genotype,
            'AD': self.allele_depth
        }

    def alternative_alleles_count(self):
        return len(self.genotype.split("/").filter(lambda x: x != 0))
        # if self.genotype == '0/0':
        #     return 0
        # if self.genotype == '0/1':
        #     return 1
        # if self.genotype == '1/1':
        #     return 2
        raise ValueError('Unknown genotype: {}'.format(self.genotype))


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
    converter.convert('AGRE_WG', './output.vcf')


if __name__ == '__main__':
    main()

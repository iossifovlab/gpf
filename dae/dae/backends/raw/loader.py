import os
import sys
import time
import numpy as np
import pandas as pd

from typing import Iterator, Tuple, List

from dae.GenomeAccess import GenomicSequence_Ivan

from dae.pedigrees.family import FamiliesData
from dae.variants.variant import SummaryVariant, SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant, \
    calculate_simple_best_state
from dae.variants.attributes import Sex, GeneticModel

from dae.backends.raw.raw_variants import TransmissionType

from dae.utils.variant_utils import get_locus_ploidy


class FamiliesGenotypes:
    def __init__(self):
        pass

    def full_families_genotypes(self):
        raise NotImplementedError()

    def get_family_genotype(self, family):
        raise NotImplementedError()

    def get_family_best_state(self, family):
        raise NotImplementedError()

    def family_genotype_iterator(self):
        raise NotImplementedError()


class VariantsLoader:

    def __init__(
            self, families, filename, source_type,
            transmission_type, params={}):

        assert isinstance(families, FamiliesData)
        self.families = families
        self.filename = filename
        self.source_type = source_type
        self.transmission_type = transmission_type
        self.params = params

    def summary_genotypes_iterator(self):
        raise NotImplementedError()

    def full_variants_iterator(self, summary_genotypes_iterator=None):
        if summary_genotypes_iterator is None:
            summary_genotypes_iterator = self.summary_genotypes_iterator()

        for summary_variant, family_genotypes in summary_genotypes_iterator:

            family_variants = []
            for fam, gt, bs in family_genotypes.family_genotype_iterator():
                family_variants.append(
                    FamilyVariant.from_summary_variant(
                        summary_variant, fam, gt, bs
                    )
                )

            yield summary_variant, family_variants

    def family_variants_iterator(self, summary_genotypes_iterator=None):
        for _, fvs in self.full_variants_iterator(
                summary_genotypes_iterator=summary_genotypes_iterator):
            for fv in fvs:
                yield fv


class VariantsLoaderDecorator(VariantsLoader):

    def __init__(self, variants_loader):
        super(VariantsLoaderDecorator, self).__init__(
            variants_loader.families,
            variants_loader.filename,
            variants_loader.source_type,
            variants_loader.transmission_type,
            params=variants_loader.params
        )
        self.variants_loader = variants_loader


class AlleleFrequencyDecorator(VariantsLoaderDecorator):
    COLUMNS = [
        'af_parents_called_count',
        'af_parents_called_percent',
        'af_allele_count',
        'af_allele_freq',
    ]

    def __init__(self, variants_loader):
        super(AlleleFrequencyDecorator, self).__init__(variants_loader)
        assert self.transmission_type == TransmissionType.transmitted

        self.independent = self.families.persons_without_parents()
        self.independent_index = \
            np.array(sorted([p.sample_index for p in self.independent]))
        self.n_independent_parents = len(self.independent)

    def get_vcf_variant(self, allele):
        return self.vcf.vars[allele['summary_variant_index']]

    def get_variant_full_genotype(self, family_genotypes):
        gt = family_genotypes.full_families_genotypes()
        gt = gt[:, self.independent_index]

        unknown = np.any(gt == -1, axis=0)
        gt = gt[0:2, np.logical_not(unknown)]
        return gt

    def annotate_summary_variant(self, summary_variant, family_genotypes):
        gt = self.get_variant_full_genotype(family_genotypes)
        n_independent_parents = self.n_independent_parents

        n_parents_called = gt.shape[1]
        percent_parents_called = \
            (100.0 * n_parents_called) / n_independent_parents

        for allele in summary_variant.alleles:

            allele_index = allele['allele_index']
            n_alleles = np.sum(gt == allele_index)
            allele_freq = 0.0
            if n_parents_called > 0:
                allele_freq = \
                    (100.0 * n_alleles) / (2.0 * n_parents_called)

            freq = {
                'af_parents_called_count': n_parents_called,
                'af_parents_called_percent': percent_parents_called,
                'af_allele_count': n_alleles,
                'af_allele_freq': allele_freq,
            }
            allele.update_attributes(freq)
        return summary_variant

    def summary_genotypes_iterator(self):
        for summary_variant, family_genotypes in \
                self.variants_loader.summary_genotypes_iterator():

            summary_variant = self.annotate_summary_variant(
                summary_variant, family_genotypes)
            yield summary_variant, family_genotypes


class AnnotationPipelineDecorator(VariantsLoaderDecorator):

    SEP1 = '!'
    SEP2 = '|'
    SEP3 = ':'

    def __init__(self, variants_loader, annotation_pipeline):
        super(AnnotationPipelineDecorator, self).__init__(variants_loader)

        self.annotation_pipeline = annotation_pipeline
        self.annotation_schema = annotation_pipeline.build_annotation_schema()

    def summary_genotypes_iterator(self):
        for summary_variant, family_genotypes in \
                self.variants_loader.summary_genotypes_iterator():

            self.annotation_pipeline.annotate_summary_variant(summary_variant)
            yield summary_variant, family_genotypes

    CLEAN_UP_COLUMNS = set([
        'alternatives_data',
        'family_variant_index',
        'family_id',
        'variant_sexes',
        'variant_roles',
        'variant_inheritance',
        'variant_in_member',
        'genotype_data',
        'best_state_data',
        'genetic_model_data',
        'frequency_data',
        'genomic_scores_data',
    ])

    def save_annotation_file(self, filename, sep="\t"):
        def convert_array_of_strings_to_string(a):
            if not a:
                return None
            return self.SEP1.join(a)

        common_columns = [
            'chrom', 'position', 'reference', 'alternative',
            'bucket_index', 'summary_variant_index',
            'allele_index', 'allele_count',
            'effect_type', 'effect_gene',
        ]
        effect_columns = [
            'effect_gene_genes', 'effect_gene_types',
            'effect_details_transcript_ids',
            'effect_details_details',
        ]

        other_columns = filter(
            lambda col: col not in common_columns
            and col not in effect_columns
            and col not in self.CLEAN_UP_COLUMNS,
            self.annotation_schema.col_names)

        header = common_columns[:]
        header.extend(effect_columns)
        header.extend(other_columns)

        with open(filename, 'w') as outfile:
            outfile.write(sep.join(header))
            outfile.write('\n')

            for summary_variant, _ in self.summary_genotypes_iterator():
                for allele_index, summary_allele in \
                        enumerate(summary_variant.alleles):
                    line = []
                    rec = summary_allele.attributes
                    rec['allele_index'] = allele_index

                    for col in common_columns:
                        line.append(str(rec.get(col, '')))
                    for col in effect_columns:
                        line.append(
                            convert_array_of_strings_to_string(
                                rec.get(col, [''])
                            )
                        )
                    for col in other_columns:
                        line.append(str(rec.get(col, '')))
                    outfile.write(sep.join(line))
                    outfile.write('\n')


class StoredAnnotationDecorator(VariantsLoaderDecorator):

    SEP1 = '!'
    SEP2 = '|'
    SEP3 = ':'

    def __init__(self, variants_loader, annotation_filename):
        super(StoredAnnotationDecorator, self).__init__(variants_loader)

        assert os.path.exists(annotation_filename)
        self.annotation_filename = annotation_filename

    @staticmethod
    def decorate(variants_loader, source_filename):
        annotation_filename = \
            StoredAnnotationDecorator._build_annotation_filename(
                    source_filename
                )
        if not os.path.exists(annotation_filename):
            return variants_loader
        else:
            variants_loader = StoredAnnotationDecorator(
                variants_loader,
                annotation_filename
            )
            return variants_loader

    @classmethod
    def _convert_array_of_strings(cls, token):
        if not token:
            return None
        token = token.strip()
        words = [w.strip() for w in token.split(cls.SEP1)]
        return words

    @staticmethod
    def _convert_string(token):
        if not token:
            return None
        return token

    @staticmethod
    def _build_annotation_filename(filename):
        return "{}-eff.txt".format(os.path.splitext(filename)[0])

    @staticmethod
    def has_annotation_file(annotation_filename):
        return os.path.exists(annotation_filename)

    @classmethod
    def load_annotation_file(cls, filename, sep='\t'):
        assert os.path.exists(filename)
        with open(filename, 'r') as infile:
            annot_df = pd.read_csv(
                infile, sep=sep, index_col=False,
                dtype={
                    'chrom': str,
                    'position': np.int32,
                },
                converters={
                    'cshl_variant': cls._convert_string,
                    'effect_gene_genes':
                    cls._convert_array_of_strings,
                    'effect_gene_types':
                    cls._convert_array_of_strings,
                    'effect_details_transcript_ids':
                    cls._convert_array_of_strings,
                    'effect_details_details':
                    cls._convert_array_of_strings,
                },
                encoding="utf-8"
            )
        for col in ['alternative', 'effect_type']:
            annot_df[col] = annot_df[col].astype(object). \
                where(pd.notnull(annot_df[col]), None)
        return annot_df

    # @classmethod
    # def save_annotation_file(cls, annot_df, filename, sep="\t"):
    #     def convert_array_of_strings_to_string(a):
    #         if not a:
    #             return None
    #         return cls.SEP1.join(a)

    #     vars_df = annot_df.copy()
    #     vars_df['effect_gene_genes'] = vars_df['effect_gene_genes'].\
    #         apply(convert_array_of_strings_to_string)
    #     vars_df['effect_gene_types'] = vars_df['effect_gene_types'].\
    #         apply(convert_array_of_strings_to_string)
    #     vars_df['effect_details_transcript_ids'] = \
    #         vars_df['effect_details_transcript_ids'].\
    #         apply(convert_array_of_strings_to_string)
    #     vars_df['effect_details_details'] = \
    #         vars_df['effect_details_details'].\
    #         apply(convert_array_of_strings_to_string)
    #     vars_df.to_csv(
    #         filename,
    #         index=False,
    #         sep=sep
    #     )

    def summary_genotypes_iterator(self):
        variant_iterator = self.variants_loader.summary_genotypes_iterator()
        start = time.time()
        annot_df = self.load_annotation_file(self.annotation_filename)
        elapsed = time.time() - start
        print(f"Annotation loaded in in {elapsed:.2f} sec", file=sys.stderr)

        start = time.time()
        records = annot_df.to_dict(orient='record')
        index = 0

        while index < len(records):
            sv, family_genotypes = next(variant_iterator)
            variant_records = []

            current_record = records[index]
            while current_record['summary_variant_index'] \
                    == sv.summary_index:
                variant_records.append(current_record)
                index += 1
                if index >= len(records):
                    break
                current_record = records[index]

            assert len(variant_records) > 0, sv

            summary_variant = SummaryVariantFactory.\
                summary_variant_from_records(
                    variant_records,
                    transmission_type=self.transmission_type)
            yield summary_variant, family_genotypes

        elapsed = time.time() - start
        print(f"Storred annotation load in {elapsed:.2f} sec", file=sys.stderr)


class FamiliesGenotypesDecorator(VariantsLoaderDecorator):
    """
    Calculate missing best states and add a genetic model
    value to the family variant and its alleles.
    """

    def __init__(
        self, variants_loader, genome, overwrite=False, expect_none=False
    ):
        super(FamiliesGenotypesDecorator, self).__init__(variants_loader)
        self.overwrite = overwrite
        self.expect_none = expect_none
        self.genome = genome

    @classmethod
    def _get_diploid_males(cls, family_variant: FamilyVariant) -> List[bool]:
        res = []

        assert family_variant.gt.shape == (
            2, len(family_variant.family.persons)
        )
        for member_idx, member in enumerate(
            family_variant.family.members_in_order
        ):
            if member.sex in (Sex.F, Sex.U):
                continue
            res.append(bool(
                family_variant.gt[1, member_idx] != -2)
            )
        return res

    @classmethod
    def _calc_genetic_model(
        cls, family_variant: FamilyVariant, genome: GenomicSequence_Ivan
    ) -> GeneticModel:
        if family_variant.chromosome in ('X', 'chrX'):
            male_ploidy = get_locus_ploidy(
                family_variant.chromosome,
                family_variant.position,
                Sex.M,
                genome
            )
            if male_ploidy == 2:
                if not all(cls._get_diploid_males(family_variant)):
                    return GeneticModel.X_broken
                else:
                    return GeneticModel.pseudo_autosomal
            elif any(cls._get_diploid_males(family_variant)):
                return GeneticModel.X_broken
            else:
                return GeneticModel.X
        else:
            # We currently assume all other chromosomes are autosomal
            return GeneticModel.autosomal

    @classmethod
    def _calc_best_state(
        cls, family_variant: FamilyVariant, genome: GenomicSequence_Ivan
    ) -> np.array:
        best_state = calculate_simple_best_state(
            family_variant.gt, family_variant.allele_count
        )

        male_ploidy = get_locus_ploidy(
            family_variant.chromosome,
            family_variant.position,
            Sex.M,
            genome
        )

        if family_variant.chromosome in ('X', 'chrX') and male_ploidy == 1:
            male_ids = [
                person_id
                for person_id, person
                in family_variant.family.persons.items()
                if person.sex == Sex.M
            ]
            male_indices = family_variant.family.members_index(male_ids)
            for idx in male_indices:
                # A male with a haploid genotype for X cannot
                # have two alternative alleles, therefore there
                # must be one or two reference alleles left over
                # from the simple best state calculation
                assert best_state[0, idx] in (1, 2)
                best_state[0, idx] -= 1

        return best_state

    def full_variants_iterator(
        self, summary_genotypes_iterator=None
    ) -> Iterator[Tuple[SummaryVariant, List[FamilyVariant]]]:
        _ = self.variant_loader.full_variants_iterator(
            summary_genotypes_iterator
        )
        for summary_variant, family_variants in _:
            for family_variant in family_variants:
                if self.expect_none:
                    assert family_variant._best_st is None
                    assert family_variant._genetic_model is None
                    continue
                if self.overwrite or family_variant._genetic_model is None:
                    family_variant._genetic_model = \
                        self._calc_genetic_model(
                            family_variant,
                            self.genome
                        )
                if self.overwrite or family_variant._best_st is None:
                    if family_variant.genetic_model != GeneticModel.X_broken:
                        family_variant._best_state = \
                            self._calc_best_state(
                                family_variant,
                                self.genome
                            )

            yield summary_variant, family_variants

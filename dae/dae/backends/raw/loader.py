import os
import pathlib
import sys
import time
import copy
import numpy as np
import pandas as pd

from typing import Iterator, Tuple, List, Dict, Any, Optional

from dae.GenomeAccess import GenomicSequence

from dae.pedigrees.family import FamiliesData

from dae.variants.variant import SummaryVariant
from dae.variants.family_variant import FamilyVariant, \
    calculate_simple_best_state
from dae.variants.attributes import Sex, GeneticModel

from dae.variants.attributes import TransmissionType

from dae.utils.variant_utils import get_locus_ploidy, best2gt


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
            self, families: FamiliesData,
            filenames: List[str],
            transmission_type: TransmissionType,
            params: Dict[str, Any] = {},
            attributes: Optional[Dict[str, Any]] = None):

        assert isinstance(families, FamiliesData)
        self.families = families
        assert all([os.path.exists(fn) for fn in filenames])
        self.filenames = filenames

        assert isinstance(transmission_type, TransmissionType)
        self.transmission_type = transmission_type
        self.params = params
        if attributes is None:
            self._attributes = {}
        else:
            self._attributes = copy.deepcopy(attributes)

    def full_variants_iterator(self):
        raise NotImplementedError()

    def family_variants_iterator(self):
        for _, fvs in self.full_variants_iterator():
            for fv in fvs:
                yield fv

    def get_attribute(self, key: str) -> Any:
        return self._attributes.get(key, None)

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value


class VariantsLoaderDecorator(VariantsLoader):

    def __init__(
            self, variants_loader: VariantsLoader):

        super(VariantsLoaderDecorator, self).__init__(
            variants_loader.families,
            variants_loader.filenames,
            variants_loader.transmission_type,
            params=variants_loader.params,
            attributes=variants_loader._attributes
        )
        self.variants_loader = variants_loader

    def get_attribute(self, key: str) -> Any:
        result = self._attributes.get(key, None)
        if result is not None:
            return result

        return self.variants_loader.get_attribute(key)

    def __getattr__(self, attr):
        return getattr(self.variants_loader, attr, None)


class AlleleFrequencyDecorator(VariantsLoaderDecorator):
    COLUMNS = [
        'af_parents_called_count',
        'af_parents_called_percent',
        'af_allele_count',
        'af_allele_freq',
    ]

    def __init__(self, variants_loader: VariantsLoader):
        super(AlleleFrequencyDecorator, self).__init__(variants_loader)
        assert self.transmission_type == TransmissionType.transmitted

        self.independent = self.families.persons_without_parents()
        self.n_independent_parents = len(self.independent)

    # def get_vcf_variant(self, allele):
    #     return self.vcf.vars[allele['summary_variant_index']]

    def annotate_summary_variant(self, summary_variant, family_variants):
        n_independent_parents = self.n_independent_parents

        for allele in summary_variant.alleles:
            allele_index = allele['allele_index']
            n_alleles = 0  # np.sum(gt == allele_index)
            allele_freq = 0.0
            n_parents_called = 0

            for fv in family_variants:
                independent_indexes = list()

                for idx, person in enumerate(fv.members_in_order):
                    if person in self.independent:
                        independent_indexes.append(idx)
                        n_parents_called += 1

                for idx in independent_indexes:
                    person_gt = fv.genotype[idx]
                    n_alleles += np.sum(person_gt == allele_index)

            percent_parents_called = \
                (100.0 * n_parents_called) / n_independent_parents
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

    def full_variants_iterator(self):
        for summary_variant, fvs in \
                self.variants_loader.full_variants_iterator():

            summary_variant = self.annotate_summary_variant(
                summary_variant, fvs)

            yield summary_variant, fvs


class AnnotationDecorator(VariantsLoaderDecorator):

    SEP1 = '!'
    SEP2 = '|'
    SEP3 = ':'

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
        'inheritance_data',
        'frequency_data',
        'genomic_scores_data',
        'effect_type',
        'effect_gene'
    ])

    def __init__(self, variants_loader):
        super(AnnotationDecorator, self).__init__(variants_loader)

    @staticmethod
    def build_annotation_filename(filename):
        path = pathlib.Path(filename)
        suffixes = path.suffixes

        if not suffixes:
            return f'{filename}-eff.txt'
        else:
            suffix = ''.join(suffixes)
            replace_with = suffix.replace('.', '-')
            filename = filename.replace(suffix, replace_with)

            return f'{filename}-eff.txt'

    @staticmethod
    def has_annotation_file(annotation_filename):
        return os.path.exists(annotation_filename)

    @staticmethod
    def save_annotation_file(variants_loader, filename, sep="\t"):
        def convert_array_of_strings_to_string(a):
            if not a:
                return None
            return AnnotationDecorator.SEP1.join(a)

        common_columns = [
            'chrom', 'position', 'reference', 'alternative',
            'bucket_index', 'summary_variant_index',
            'allele_index', 'allele_count',
        ]

        if variants_loader.annotation_schema is not None:
            other_columns = filter(
                lambda col: col not in common_columns
                and col not in AnnotationDecorator.CLEAN_UP_COLUMNS,
                variants_loader.annotation_schema.col_names)
        else:
            other_columns = []

        header = common_columns[:]
        header.extend(['effects'])
        header.extend(other_columns)

        with open(filename, 'w') as outfile:
            outfile.write(sep.join(header))
            outfile.write('\n')

            for summary_variant, _ in variants_loader.full_variants_iterator():
                for allele_index, summary_allele in \
                        enumerate(summary_variant.alleles):
                    line = []
                    rec = summary_allele.attributes
                    rec['allele_index'] = allele_index

                    for col in common_columns:
                        line.append(str(rec.get(col, '')))
                    if summary_allele.effect is None:
                        line.append('')
                    else:
                        line.append(
                            str(summary_allele.effect)
                        )
                    for col in other_columns:
                        line.append(str(rec.get(col, '')))
                    outfile.write(sep.join(line))
                    outfile.write('\n')


class AnnotationPipelineDecorator(AnnotationDecorator):

    def __init__(self, variants_loader, annotation_pipeline):
        super(AnnotationPipelineDecorator, self).__init__(variants_loader)

        self.annotation_pipeline = annotation_pipeline
        self.annotation_schema = annotation_pipeline.build_annotation_schema()
        self.set_attribute('annotation_schema', self.annotation_schema)

    def full_variants_iterator(self):
        for summary_variant, family_variants in \
                self.variants_loader.full_variants_iterator():
            self.annotation_pipeline.annotate_summary_variant(summary_variant)
            yield summary_variant, family_variants


class StoredAnnotationDecorator(AnnotationDecorator):

    def __init__(self, variants_loader, annotation_filename):
        super(StoredAnnotationDecorator, self).__init__(variants_loader)

        assert os.path.exists(annotation_filename)
        self.annotation_filename = annotation_filename

    @staticmethod
    def decorate(variants_loader, source_filename):
        annotation_filename = \
            StoredAnnotationDecorator.build_annotation_filename(
                    source_filename
                )
        # assert os.path.exists(annotation_filename), \
        #     annotation_filename
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

    @classmethod
    def _load_annotation_file(cls, filename, sep='\t'):
        assert os.path.exists(filename)
        with open(filename, 'r') as infile:
            annot_df = pd.read_csv(
                infile, sep=sep, index_col=False,
                dtype={
                    'chrom': str,
                    'position': np.int32,
                    # 'effects': str,
                },
                converters={
                    'cshl_variant': cls._convert_string,
                    'effects': cls._convert_string,
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
        special_columns = set(annot_df.columns) \
            & set(['alternative', 'effect_type'])
        for col in special_columns:
            annot_df[col] = annot_df[col].astype(object). \
                where(pd.notnull(annot_df[col]), None)
        return annot_df

    def full_variants_iterator(self):
        variant_iterator = self.variants_loader.full_variants_iterator()
        start = time.time()
        annot_df = self._load_annotation_file(self.annotation_filename)
        elapsed = time.time() - start
        print(
            f"Storred annotation file loaded in in {elapsed:.2f} sec",
            file=sys.stderr)

        start = time.time()
        records = annot_df.to_dict(orient='record')
        index = 0

        while index < len(records):
            sv, family_variants = next(variant_iterator)
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

            for sa in sv.alleles:
                sa.update_attributes(variant_records[sa.allele_index])
            yield sv, family_variants

        elapsed = time.time() - start
        print(
            f"Storred annotation file parsed in {elapsed:.2f} sec",
            file=sys.stderr)


class VariantsGenotypesLoader(VariantsLoader):
    """
    Calculate missing best states and adds a genetic model
    value to the family variant and its alleles.
    """

    def __init__(
        self,
        families: FamiliesData,
        filenames: List[str],
        transmission_type: TransmissionType,
        genome: GenomicSequence,
        overwrite: bool = False,
        expect_genotype: bool = True,
        expect_best_state: bool = False,
        params: Dict[str, Any] = {},
    ):
        super(VariantsGenotypesLoader, self).__init__(
            families=families,
            filenames=filenames,
            transmission_type=transmission_type,
            params=params)

        self.genome = genome

        self.overwrite = overwrite
        self.expect_genotype = expect_genotype
        self.expect_best_state = expect_best_state

    def _full_variants_iterator_impl(self):
        raise NotImplementedError()

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
        cls, family_variant: FamilyVariant, genome: GenomicSequence
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
        cls, family_variant: FamilyVariant, genome: GenomicSequence
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

    @classmethod
    def _calc_genotype(
        cls, family_variant: FamilyVariant, genome: GenomicSequence
    ) -> np.array:
        best_state = family_variant._best_state
        genotype = best2gt(best_state)
        male_ploidy = get_locus_ploidy(
            family_variant.chromosome,
            family_variant.position,
            Sex.M,
            genome
        )
        ploidy = np.sum(best_state, 0)
        genetic_model = GeneticModel.autosomal

        if family_variant.chromosome in ('X', 'chrX'):
            genetic_model = GeneticModel.X
            if male_ploidy == 2:
                genetic_model = GeneticModel.pseudo_autosomal

            male_ids = [
                person_id
                for person_id, person
                in family_variant.family.persons.items()
                if person.sex == Sex.M
            ]
            male_indices = family_variant.family.members_index(male_ids)
            for idx in male_indices:
                if ploidy[idx] != male_ploidy:
                    genetic_model = GeneticModel.X_broken
                    break

        elif np.any(ploidy == 1):
            genetic_model = GeneticModel.autosomal_broken

        return genotype, genetic_model

    def full_variants_iterator(
            self) -> Iterator[Tuple[SummaryVariant, List[FamilyVariant]]]:
        full_iterator = self._full_variants_iterator_impl()
        for summary_variant, family_variants in full_iterator:
            for family_variant in family_variants:
                if self.expect_genotype:
                    assert family_variant._best_state is None
                    assert family_variant._genetic_model is None
                    assert family_variant.gt is not None

                    family_variant._genetic_model = \
                        self._calc_genetic_model(
                            family_variant,
                            self.genome
                        )

                    family_variant._best_state = \
                        self._calc_best_state(
                            family_variant,
                            self.genome
                        )
                    for fa in family_variant.alleles:
                        fa._best_state = family_variant.best_state
                        fa._genetic_model = family_variant.genetic_model
                elif self.expect_best_state:
                    assert family_variant._best_state is not None
                    assert family_variant._genetic_model is None
                    assert family_variant.gt is None

                    family_variant.gt, family_variant._genetic_model = \
                        self._calc_genotype(family_variant, self.genome)
                    for fa in family_variant.alleles:
                        fa.gt = family_variant.gt
                        fa._genetic_model = family_variant.genetic_model

            yield summary_variant, family_variants

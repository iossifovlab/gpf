import itertools
import traceback
import logging
from typing import List, Dict

from dae.utils.dae_utils import join_line, split_iterable
from dae.utils.variant_utils import mat2str, fgt2str
from dae.utils.effect_utils import ge2str, \
    gd2str, \
    gene_effect_get_worst_effect, \
    gene_effect_get_genes
from dae.variants.attributes import Inheritance, VariantDesc
from dae.variants.variant import SummaryVariant
from dae.variants.family_variant import FamilyVariant


def members_in_order_get_family_structure(mio):
    return ";".join([
        f"{p.role.name}:{p.sex.short()}:{p.status.name}" for p in mio])


class ResponseTransformer:

    STREAMING_CHUNK_SIZE = 20

    SPECIAL_ATTRS = {
        "family":
        lambda v: [v.family_id],

        "location":
        lambda v: v.cshl_location,

        "variant":
        lambda v: VariantDesc.combine([
            aa.details.variant_desc for aa in v.alt_alleles]),

        "position":
        lambda v: [aa.position for aa in v.alt_alleles],

        "reference":
        lambda v: [aa.reference for aa in v.alt_alleles],

        "alternative":
        lambda v: [aa.alternative for aa in v.alt_alleles],

        "genotype":
        lambda v: [fgt2str(v.family_genotype)],

        "best_st":
        lambda v: [mat2str(v.family_best_state)],

        "family_person_attributes":
        lambda v: [members_in_order_get_family_structure(
            v.members_in_order)],

        "family_structure":
        lambda v: [members_in_order_get_family_structure(
            v.members_in_order)],

        "family_person_ids":
        lambda v: [";".join(list(map(
            lambda m: m.person_id, v.members_in_order
        )))],

        "carrier_person_ids":
        lambda v: list(
            map(
                lambda aa: ";".join(list(filter(None, aa.variant_in_members))),
                v.alt_alleles
            )),

        "carrier_person_attributes": 
        lambda v: list(
            map(
                lambda aa: members_in_order_get_family_structure(
                    filter(None, aa.variant_in_members_objects)
                ),
                v.alt_alleles
            )),

        "inheritance_type":
        lambda v: list(
            map(
                lambda aa:
                "denovo"
                if Inheritance.denovo in aa.inheritance_in_members
                else "mendelian"
                if Inheritance.mendelian in aa.inheritance_in_members
                else "-",
                v.alt_alleles)
        ),

        "is_denovo":
        lambda v: list(
            map(
                lambda aa:
                Inheritance.denovo in aa.inheritance_in_members,
                v.alt_alleles)
        ),

        "effects":
        lambda v: [ge2str(e) for e in v.effects],

        "genes":
        lambda v: [gene_effect_get_genes(e) for e in v.effects],

        "worst_effect":
        lambda v: [gene_effect_get_worst_effect(e) for e in v.effects],

        "effect_details":
        lambda v: [gd2str(e) for e in v.effects],

        "seen_in_affected":
        lambda v: bool(v.get_attribute("seen_in_status") in {2, 3}),

        "seen_in_unaffected":
        lambda v: bool(v.get_attribute("seen_in_status") in {1, 3}),
    }

    PHENOTYPE_ATTRS = {
        "family_phenotypes":
        lambda v, phenotype_person_sets:
        [
            ':'.join([
                phenotype_person_sets.get_person_set_of_person(mid).name
                for mid in v.members_ids])
        ],

        "carrier_phenotypes":
        lambda v, phenotype_person_sets:
        [':'.join([
            phenotype_person_sets.get_person_set_of_person(mid).name
            for mid in filter(None, aa.variant_in_members)])
         for aa in v.alt_alleles],
    }

    def __init__(self, study_wrapper):
        self.study_wrapper = study_wrapper

    def add_additional_columns(self, variants_iterable):
        for variants_chunk in split_iterable(
                variants_iterable, self.STREAMING_CHUNK_SIZE):

            families = {variant.family_id for variant in variants_chunk}

            pheno_column_values = self.study_wrapper._get_all_pheno_values(families)

            for variant in variants_chunk:
                pheno_values = self.study_wrapper._get_pheno_values_for_variant(
                    variant, pheno_column_values
                )

                for allele in variant.alt_alleles:
                    gene_weights_values = self.study_wrapper._get_gene_weights_values(allele)
                    allele.update_attributes(gene_weights_values)

                    if pheno_values:
                        allele.update_attributes(pheno_values)

                yield variant

    def add_additional_columns_summary(self, variants_iterable):
        for variants_chunk in split_iterable(
                variants_iterable, self.STREAMING_CHUNK_SIZE):

            for variant in variants_chunk:
                for allele in variant.alt_alleles:
                    gene_weights_values = self.study_wrapper._get_gene_weights_values(allele)

                    allele.update_attributes(gene_weights_values)

                yield variant

    def build_variant_row(
            self, v: FamilyVariant, column_descs: List[Dict], **kwargs):

        row_variant = []
        for col_desc in column_descs:
            try:
                col_source = col_desc["source"]
                col_format = col_desc.get("format")

                if col_format is None:
                    def col_formatter(val):
                        if val is None:
                            return "-"
                        else:
                            return str(val)
                else:
                    def col_formatter(val):
                        if val is None:
                            return "-"
                        try:
                            return col_format % val
                        except Exception:
                            logging.exception(f'error build variant: {v}')
                            traceback.print_stack()
                            return "-"

                if col_source == "pedigree":
                    person_set_collection = \
                        kwargs.get("person_set_collection")
                    row_variant.append(
                        self.study_wrapper.generate_pedigree(
                            v, person_set_collection
                        )
                    )
                elif col_source in self.PHENOTYPE_ATTRS:
                    phenotype_person_sets = \
                        self.study_wrapper.person_set_collections.get("phenotype")
                    if phenotype_person_sets is None:
                        row_variant.append("-")
                    else:
                        fn = self.PHENOTYPE_ATTRS[col_source]
                        row_variant.append(
                            ",".join(fn(v, phenotype_person_sets)))

                elif col_source == "study_phenotype":
                    row_variant.append(self.study_wrapper.config.study_phenotype)

                else:
                    if col_source in self.SPECIAL_ATTRS:
                        attribute = self.SPECIAL_ATTRS[col_source](v)
                    else:
                        attribute = v.get_attribute(col_source)

                    if all([a == attribute[0] for a in attribute]):
                        attribute = [attribute[0]]
                    attribute = list(map(col_formatter, attribute))

                    row_variant.append(",".join([str(a) for a in attribute]))

            except (AttributeError, KeyError, Exception):
                logging.exception(f'error build variant: {v}')
                traceback.print_stack()
                row_variant.append([""])
                raise

        return row_variant

    def transform_gene_view_summary_variant(self, variant: SummaryVariant, frequency_column):
        for a in variant.alt_alleles:
            yield {
                "location": a.cshl_location,
                "position": a.position,
                "end_position": a.end_position,
                "chrom": a.chrom,
                "frequency": a.get_attribute(frequency_column),
                "effect": gene_effect_get_worst_effect(a.effect),
                "variant": a.cshl_variant,
                "family_variants_count":
                    a.get_attribute("family_variants_count"),
                "is_denovo": a.get_attribute("seen_as_denovo"),
                "seen_in_affected":
                    a.get_attribute("seen_in_status") in {2, 3},
                "seen_in_unaffected":
                    a.get_attribute("seen_in_status") in {1, 3},
            }

    def gene_view_summary_download_variants_iterator(
        self, variants: List[SummaryVariant], frequency_column
    ):
        for v in variants:
            for a in v.alt_alleles:
                yield [
                    a.cshl_location,
                    a.position,
                    a.end_position,
                    a.chrom,
                    a.get_attribute(frequency_column),
                    gene_effect_get_worst_effect(a.effect),
                    a.cshl_variant,
                    a.get_attribute("family_variants_count"),
                    a.get_attribute("seen_as_denovo"),
                    a.get_attribute("seen_in_status") in {2, 3},
                    a.get_attribute("seen_in_status") in {1, 3},
                ]

    def transform_gene_view_summary_variant_download(
        self, variants: List[SummaryVariant], frequency_column
    ):
        columns = [
            "location",
            "position",
            "end_position",
            "chrom",
            "frequency",
            "effect",
            "variant",
            "family_variants_count",
            "is_denovo",
            "seen_in_affected",
            "seen_in_unaffected"
        ]
        rows = self.gene_view_summary_download_variants_iterator(variants, frequency_column)
        return map(join_line, itertools.chain([columns], rows))

import itertools
import traceback
import logging
import math
from functools import partial
from typing import Optional, Any, Union, Generator, Iterator, Iterable, \
    Callable, cast

import pandas as pd

from dae.utils.dae_utils import join_line, split_iterable
from dae.utils.variant_utils import mat2str, fgt2str
from dae.utils.effect_utils import ge2str, \
    gd2str, \
    gene_effect_get_worst_effect, \
    gene_effect_get_genes
from dae.variants.attributes import Inheritance
from dae.variants.variant import SummaryVariant, VariantDesc
from dae.variants.family_variant import FamilyVariant, FamilyAllele
from dae.pedigrees.family import Person, FamiliesData
from dae.person_sets import PersonSetCollection

logger = logging.getLogger(__name__)


def members_in_order_get_family_structure(mio: list[Person]) -> str:
    return ";".join([
        f"{p.role.name}:{p.sex.short()}:{p.status.name}" for p in mio])


class ResponseTransformer:
    """Helper class to transform genotype browser response."""

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
                lambda aa:
                members_in_order_get_family_structure(
                    list(filter(None, aa.variant_in_members_objects))
                ),
                v.alt_alleles
            )),

        "inheritance_type":
        lambda v: list(map(
            lambda aa:
            "denovo"
            if Inheritance.denovo in aa.inheritance_in_members
            else "-"
            if set([
                Inheritance.possible_denovo, Inheritance.possible_omission])
                & set(aa.inheritance_in_members)
            else "mendelian",
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

        "raw_effects":
        lambda v: [repr(e) for e in v.effects],

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
            ":".join([
                phenotype_person_sets.get_person_set_of_person(mid).name
                for mid in v.members_ids])
        ],

        "carrier_phenotypes":
        lambda v, phenotype_person_sets:
        [
            ":".join([  # type: ignore
                phenotype_person_sets.get_person_set_of_person(mid).name
                for mid in filter(None, aa.variant_in_members)])
            for aa in v.alt_alleles
        ],
    }

    def __init__(self, study_wrapper: Any):
        # pylint: disable=import-outside-toplevel
        from studies.study_wrapper import StudyWrapper

        self.study_wrapper = cast(StudyWrapper, study_wrapper)
        self._pheno_columns = study_wrapper.config_columns.phenotype

    @property
    def families(self) -> FamiliesData:
        return self.study_wrapper.families

    def _get_all_pheno_values(
        self, family_ids: Iterable[str]
    ) -> Optional[list[tuple[pd.DataFrame, str]]]:
        if not self.study_wrapper.phenotype_data \
           or not self.study_wrapper.config_columns.phenotype:
            return None

        pheno_column_names = []
        pheno_column_dfs = []
        for column in self.study_wrapper.config_columns.phenotype.values():
            assert column.role
            persons = self.study_wrapper.families.persons_with_roles(
                [column.role], family_ids)
            person_ids = [p.person_id for p in persons]

            kwargs = {
                "person_ids": list(person_ids),
            }

            pheno_column_names.append(f"{column.source}.{column.role}")
            pheno_column_dfs.append(
                self.study_wrapper.phenotype_data.get_measure_values_df(
                    column.source, **kwargs
                )
            )

        result = list(zip(pheno_column_dfs, pheno_column_names))
        return result

    @staticmethod
    def _get_pheno_values_for_variant(
        variant: FamilyVariant,
        pheno_column_values: Optional[list[tuple[pd.DataFrame, str]]]
    ) -> Optional[dict[str, str]]:
        if not pheno_column_values:
            return None

        pheno_values = {}

        for pheno_column_df, pheno_column_name in pheno_column_values:
            variant_pheno_value_df = pheno_column_df[
                pheno_column_df["person_id"].isin(variant.members_ids)
            ]
            variant_pheno_value_df.set_index("person_id", inplace=True)
            assert len(variant_pheno_value_df.columns) == 1
            column = variant_pheno_value_df.columns[0]

            pheno_values[pheno_column_name] = ",".join(
                variant_pheno_value_df[column].map(str).tolist()
            )

        return pheno_values

    def _get_gene_scores_values(
        self, allele: FamilyAllele, default: Optional[str] = None
    ) -> dict[str, Any]:
        if not self.study_wrapper.gene_score_column_sources:
            return {}
        genes = gene_effect_get_genes(allele.effects).split(";")
        gene = genes[0]

        gene_scores_values = {}
        for gwc in self.study_wrapper.gene_score_column_sources:
            if gwc not in self.study_wrapper.gene_scores_db:
                continue

            if gene != "":
                score_desc = self.study_wrapper.gene_scores_db.get_score_desc(
                    gwc
                )

                gene_scores = self.study_wrapper.gene_scores_db.get_gene_score(
                    score_desc.resource_id
                )
                # pylint: disable=protected-access
                gene_scores_values[gwc] = gene_scores._to_dict(gwc).get(
                    gene, default
                )
            else:
                gene_scores_values[gwc] = default

        return gene_scores_values

    @staticmethod
    def _get_wdae_member(
            member: Person,
            person_set_collection: PersonSetCollection,
            best_st: Union[str, int]) -> list:
        return [
            member.family_id,
            member.person_id,
            member.mom_id if member.mom_id else "0",
            member.dad_id if member.dad_id else "0",
            member.sex.short(),
            str(member.role),
            PersonSetCollection.get_person_color(
                member, person_set_collection
            ),
            member.layout,
            (member.generated or member.not_sequenced),
            best_st,
            0,
        ]

    def _generate_pedigree(
        self, variant: FamilyVariant, collection_id: str
    ) -> list:
        result = []
        # best_st = np.sum(allele.gt == allele.allele_index, axis=0)
        person_set_collection = self.study_wrapper.get_person_set_collection(
            collection_id
        )
        genotype = variant.family_genotype

        missing_members = set()
        for index, member in enumerate(variant.members_in_order):
            try:
                result.append(
                    ResponseTransformer._get_wdae_member(
                        member, person_set_collection,
                        "/".join([
                            str(v) for v in filter(
                                lambda g: g != 0, genotype[index]
                            )]
                        )
                    )
                )
            except IndexError:
                missing_members.add(member.person_id)
                logger.error(
                    "problems generating pedigree: %s, %s, %s",
                    genotype, index, member, exc_info=True)

        for member in variant.family.full_members:
            if (member.generated or member.not_sequenced) \
                    or (member.person_id in missing_members):
                result.append(ResponseTransformer._get_wdae_member(
                    member, person_set_collection, 0)
                )

        return result

    def _add_additional_columns_summary(
        self, variants_iterable: Generator[SummaryVariant, None, None]
    ) -> Generator[SummaryVariant, None, None]:
        for variants_chunk in split_iterable(
                variants_iterable, self.STREAMING_CHUNK_SIZE):

            for variant in variants_chunk:
                for allele in variant.alt_alleles:
                    gene_scores_values = self._get_gene_scores_values(allele)

                    allele.update_attributes(gene_scores_values)

                yield variant

    def build_variant_row(  # noqa
        self, v: Union[SummaryVariant, FamilyVariant],
        column_descs: list[dict], **kwargs: Union[str]
    ) -> list:
        """Construct response row for a variant."""
        # pylint: disable=too-many-branches
        row_variant: list[Any] = []
        for col_desc in column_descs:
            try:
                col_source = col_desc["source"]
                col_format = col_desc.get("format")
                col_role = col_desc.get("role")

                if col_format is None:
                    # pylint: disable=unused-argument
                    def col_formatter(val, col_format):  # type: ignore
                        if val is None:
                            return "-"
                        return str(val)
                else:
                    def col_formatter(val, col_format):  # type: ignore
                        if val is None:
                            return "-"
                        try:
                            return col_format % val
                        except Exception:  # pylint: disable=broad-except
                            logging.warning(
                                "error formatting variant: %s (%s) (%s)",
                                v, col_format, val, exc_info=True)
                            if math.isnan(val):
                                return None
                            return val

                if col_role is not None:
                    col_source = f"{col_source}.{col_role}"

                if col_source == "pedigree":
                    assert kwargs.get("person_set_collection") is not None
                    assert isinstance(v, FamilyVariant)
                    row_variant.append(self._generate_pedigree(
                        v, kwargs["person_set_collection"]
                    ))
                elif col_source in self.PHENOTYPE_ATTRS:
                    phenotype_person_sets = \
                        self.study_wrapper.person_set_collections.get(
                            "phenotype"
                        )
                    if phenotype_person_sets is None:
                        row_variant.append("-")
                    else:
                        fn_format = self.PHENOTYPE_ATTRS[col_source]
                        row_variant.append(
                            ",".join(fn_format(v, phenotype_person_sets)))
                elif col_source == "study_phenotype":
                    row_variant.append(
                        self.study_wrapper.config.study_phenotype
                    )
                else:
                    if col_source in self.SPECIAL_ATTRS:
                        attribute = self.SPECIAL_ATTRS[col_source](v)
                    else:
                        attribute = v.get_attribute(col_source)

                    if kwargs.get("reduceAlleles", True):
                        if all(a == attribute[0] for a in attribute):
                            attribute = [attribute[0]]
                    attribute = list(
                        map(
                            partial(col_formatter, col_format=col_format),
                            attribute))
                    row_variant.append(attribute)

            except (AttributeError, KeyError, Exception):
                logging.exception("error build variant: %s", v)
                traceback.print_stack()
                row_variant.append([""])
                raise

        return row_variant

    @staticmethod
    def _gene_view_summary_download_variants_iterator(
        variants: list[SummaryVariant], frequency_column: str
    ) -> Generator[list, None, None]:
        for v in variants:
            for aa in v.alt_alleles:
                yield [
                    aa.cshl_location,
                    aa.position,
                    aa.end_position,
                    aa.chrom,
                    aa.get_attribute(frequency_column),
                    gene_effect_get_worst_effect(aa.effects),
                    aa.cshl_variant,
                    aa.get_attribute("family_variants_count"),
                    aa.get_attribute("seen_as_denovo"),
                    aa.get_attribute("seen_in_status") in {2, 3},
                    aa.get_attribute("seen_in_status") in {1, 3},
                ]

    @staticmethod
    def transform_gene_view_summary_variant(
        variant: SummaryVariant, frequency_column: str
    ) -> Generator[dict, None, None]:
        """Transform gene view summary response into dicts."""
        out: dict[str, Any] = {
            "svuid": variant.svuid,
        }
        alleles = []
        for aa in variant.alt_alleles:
            alleles.append({
                "location": aa.cshl_location,
                "position": aa.position,
                "end_position": aa.end_position,
                "chrom": aa.chrom,
                "frequency": aa.get_attribute(frequency_column),
                "effect": gene_effect_get_worst_effect(aa.effects),
                "variant": aa.cshl_variant,
                "family_variants_count":
                    aa.get_attribute("family_variants_count"),
                "is_denovo": aa.get_attribute("seen_as_denovo"),
                "seen_in_affected":
                    aa.get_attribute("seen_in_status") in {2, 3},
                "seen_in_unaffected":
                    aa.get_attribute("seen_in_status") in {1, 3},
            })
        out["alleles"] = alleles
        yield out

    def transform_gene_view_summary_variant_download(
        self,
        variants: list[SummaryVariant],
        frequency_column: str,
        summary_variant_ids: set[str],
    ) -> Iterator[str]:
        """Transform gene view summary response into rows."""
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

        rows = filter(
            lambda sa: f"{sa[0]}:{sa[6]}" in summary_variant_ids,
            self._gene_view_summary_download_variants_iterator(
                variants, frequency_column
            )
        )
        return map(join_line, itertools.chain([columns], rows))

    def variant_transformer(self) -> Callable[[FamilyVariant], FamilyVariant]:
        """Build and return a variant transformer function."""
        assert not self.study_wrapper.is_remote
        pheno_column_values = self._get_all_pheno_values(self.families)

        def transformer(variant: FamilyVariant) -> FamilyVariant:
            pheno_values = self._get_pheno_values_for_variant(
                variant, pheno_column_values
            )

            for allele in variant.alt_alleles:
                fallele = cast(FamilyAllele, allele)
                gene_scores_values = self._get_gene_scores_values(
                    fallele
                )
                fallele.update_attributes(gene_scores_values)

                if pheno_values:
                    fallele.update_attributes(pheno_values)

            return variant

        return transformer

    def transform_summary_variants(
        self, variants_iterable: Generator[SummaryVariant, None, None]
    ) -> Generator[list, None, None]:
        for v in self._add_additional_columns_summary(variants_iterable):
            yield self.build_variant_row(
                v, self.study_wrapper.summary_preview_descs
            )

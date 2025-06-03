import itertools
import logging
import math
from collections.abc import Callable, Generator, Iterable, Iterator
from functools import partial
from typing import (
    Any,
    ClassVar,
    cast,
)

from dae.effect_annotation.effect import (
    gd2str,
    ge2str,
    gene_effect_get_genes,
    gene_effect_get_genes_worst,
    gene_effect_get_worst_effect,
)
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import Person
from dae.person_sets import PersonSetCollection
from dae.utils.dae_utils import join_line, split_iterable
from dae.utils.variant_utils import fgt2str, mat2str
from dae.variants.attributes import Inheritance, Role
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.variants.variant import SummaryVariant, VariantDesc

logger = logging.getLogger(__name__)


def members_in_order_get_family_structure(mio: list[Person]) -> str:
    return ";".join([
        f"{p.role.name}:{p.sex.short()}:{p.status.name}"  # type: ignore
        for p in mio])


class ResponseTransformer:
    """Helper class to transform genotype browser response."""

    STREAMING_CHUNK_SIZE = 20

    SPECIAL_ATTRS: ClassVar[dict[str, Callable]] = {
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
        lambda v: [";".join([m.person_id for m in v.members_in_order])],

        "carrier_person_ids":
        lambda v: [
            ";".join(m for m in aa.variant_in_members if m is not None)
            for aa in v.alt_alleles
        ],

        "carrier_person_attributes":
        lambda v: [
                members_in_order_get_family_structure([
                    m for m in aa.variant_in_members_objects if m is not None])
                for aa in v.alt_alleles
        ],

        "inheritance_type":
        lambda v: [
            "denovo"
            if Inheritance.denovo in aa.inheritance_in_members
            else "-"
            if {Inheritance.possible_denovo, Inheritance.possible_omission}
            & set(aa.inheritance_in_members)
            else "mendelian"
            for aa in v.alt_alleles
        ],

        "is_denovo":
        lambda v: [
            Inheritance.denovo in aa.inheritance_in_members
            for aa in v.alt_alleles
        ],

        "effects":
        lambda v: [ge2str(e) for e in v.effects],

        "raw_effects":
        lambda v: [repr(e) for e in v.effects],

        "genes":
        lambda v: [gene_effect_get_genes_worst(e) for e in v.effects],

        "worst_effect":
        lambda v: [gene_effect_get_worst_effect(e) for e in v.effects],

        "effect_details":
        lambda v: [gd2str(e) for e in v.effects],

        "full_effect_details":
        lambda v: (
            [v.family_id]
            + v.cshl_location
            + [gd2str(e) for e in v.effects]
            + [ge2str(e) for e in v.effects]
        ),

        "seen_in_affected":
        lambda v: bool(v.get_attribute("seen_in_status") in {2, 3}),

        "seen_in_unaffected":
        lambda v: bool(v.get_attribute("seen_in_status") in {1, 3}),
    }

    PHENOTYPE_ATTRS: ClassVar[dict[str, Callable]] = {
        "family_phenotypes":
        lambda v, phenotype_person_sets:
        [
            ":".join([
                phenotype_person_sets.get_person_set_of_person(mid).name
                for mid in v.members_fpids]),
        ],

        "carrier_phenotypes":
        lambda v, phenotype_person_sets:
        [
            ":".join([  # type: ignore
                phenotype_person_sets.get_person_set_of_person(mid).name
                for mid in filter(None, aa.variant_in_members_fpid)])
            for aa in v.alt_alleles
        ],
    }

    def __init__(self, study_wrapper: Any) -> None:
        # pylint: disable=import-outside-toplevel
        from studies.study_wrapper import StudyWrapper

        self.study_wrapper = cast(StudyWrapper, study_wrapper)
        self._pheno_columns = study_wrapper.config_columns.phenotype
        self._pheno_values: dict[str, Any] | None = None

        self.gene_scores_dicts = {}
        if not study_wrapper.is_remote \
                and self.study_wrapper.gene_scores_db is not None:
            gene_scores_db = self.study_wrapper.gene_scores_db
            for score_id, score_desc in gene_scores_db.score_descs.items():
                gene_score = gene_scores_db.get_gene_score(
                    score_desc.resource_id,
                )
                if gene_score is None:
                    continue
                self.gene_scores_dicts[score_id] = \
                    gene_score._to_dict(score_id)  # noqa: SLF001
            self._get_all_pheno_values()

    @property
    def families(self) -> FamiliesData:
        return self.study_wrapper.families

    def _get_all_pheno_values(
        self,
    ) -> dict | None:
        if self._pheno_values is not None:
            return self._pheno_values
        if not self.study_wrapper.has_pheno_data \
           or not self.study_wrapper.config_columns.phenotype:
            return None

        pheno_values = {}

        for column in self.study_wrapper.config_columns.phenotype.values():
            assert column.role
            result = {}
            column_values_iter = self.study_wrapper\
                .phenotype_data.get_people_measure_values(
                    [column.source], roles=[Role.from_name(column.role)])
            for column_value in column_values_iter:
                result[column_value["family_id"]] = column_value[column.source]

            pheno_column_name = f"{column.source}.{column.role}"
            pheno_values[pheno_column_name] = result
        self._pheno_values = pheno_values
        return self._pheno_values

    @staticmethod
    def _get_pheno_values_for_variant(
        variant: FamilyVariant,
        pheno_column_values: dict | None,
    ) -> dict[str, str] | None:
        if not pheno_column_values:
            return None

        pheno_values = {}

        for pheno_column_name in pheno_column_values:
            family_id = variant.family_id
            pheno_value = pheno_column_values[pheno_column_name].get(family_id)
            pheno_values[pheno_column_name] = pheno_value

        return pheno_values

    def _get_gene_scores_values(
        self, allele: FamilyAllele, default: str | None = None,
    ) -> dict[str, Any]:
        if not self.study_wrapper.gene_score_column_sources:
            return {}
        if allele.effects is None:
            return {}
        genes = gene_effect_get_genes(allele.effects).split(";")
        gene = genes[0]

        gene_scores_values = {}
        for gwc in self.study_wrapper.gene_score_column_sources:
            if gwc not in self.gene_scores_dicts:
                continue

            if gene != "":
                gene_scores_values[gwc] = self.gene_scores_dicts[gwc].get(
                    gene, default,
                )
            else:
                gene_scores_values[gwc] = default

        return gene_scores_values

    @staticmethod
    def _get_wdae_member(
            member: Person,
            psc: PersonSetCollection | None,
            best_st: str | int) -> list:
        return [
            member.family_id,
            member.person_id,
            member.mom_id or "0",
            member.dad_id or "0",
            member.sex.short(),
            str(member.role),
            PersonSetCollection.get_person_color(member, psc),
            member.layout,
            (member.generated or member.not_sequenced),
            best_st,
            0,
        ]

    def _generate_pedigree(
        self, variant: FamilyVariant,
        psc_id: str | None,
    ) -> list:
        result = []
        psc = self.study_wrapper.get_person_set_collection(psc_id)
        genotype = variant.family_genotype

        missing_members = set()
        for index, member in enumerate(variant.members_in_order):
            try:
                result.append(
                    ResponseTransformer._get_wdae_member(
                        member, psc,
                        "/".join([
                            str(v) for v in filter(
                                lambda g: g != 0, genotype[index],
                            )],
                        ),
                    ),
                )
            except IndexError:
                missing_members.add(member.person_id)
                logger.info(
                    "problems generating pedigree: %s, %s, %s",
                    fgt2str(genotype), index, member.person_id)  # type: ignore

        result.extend([
            ResponseTransformer._get_wdae_member(member, psc, 0)
            for member in variant.family.full_members
            if (member.generated or member.not_sequenced) or (
                member.person_id in missing_members)
        ])

        return result

    def _add_additional_columns_summary(
        self, variants_iterable: Generator[SummaryVariant, None, None],
    ) -> Generator[SummaryVariant, None, None]:
        for variants_chunk in split_iterable(
                variants_iterable, self.STREAMING_CHUNK_SIZE):

            for variant in variants_chunk:
                for allele in variant.alt_alleles:
                    gene_scores_values = self._get_gene_scores_values(allele)

                    allele.update_attributes(gene_scores_values)

                yield variant

    def build_variant_row(
        self, v: SummaryVariant | FamilyVariant,
        column_descs: list[dict], **kwargs: str | None,
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
                    def col_formatter(
                        val: Any,
                        col_format: str | None,  # noqa: ARG001
                    ) -> str:
                        if val is None:
                            return "-"
                        return str(val)
                else:
                    def col_formatter(
                        val: Any,
                        col_format: str | None,
                    ) -> str:
                        # pylint: disable=broad-except
                        if val is None:
                            return "-"
                        try:
                            assert col_format is not None
                            return str(col_format % val)
                        except Exception:  # noqa: BLE001
                            logger.warning(
                                "error formatting variant: %s (%s) (%s)",
                                v, col_format, val, exc_info=True)
                            if math.isnan(val):
                                return "-"
                        return str(val)

                if col_role is not None:
                    col_source = f"{col_source}.{col_role}"

                if col_source == "pedigree":
                    assert isinstance(v, FamilyVariant)
                    psc_id = kwargs["person_set_collection"]
                    row_variant.append(self._generate_pedigree(
                        v, psc_id,
                    ))
                elif col_source in self.PHENOTYPE_ATTRS:
                    phenotype_person_sets = \
                        self.study_wrapper.person_set_collections.get(
                            "phenotype",
                        )
                    if phenotype_person_sets is None:
                        row_variant.append("-")
                    else:
                        fn_format = self.PHENOTYPE_ATTRS[col_source]
                        row_variant.append(
                            ",".join(fn_format(v, phenotype_person_sets)))
                elif col_source == "study_phenotype":
                    row_variant.append(
                        self.study_wrapper.config.study_phenotype,
                    )
                else:
                    if col_source in self.SPECIAL_ATTRS:
                        attribute = self.SPECIAL_ATTRS[col_source](v)
                    else:
                        attribute = v.get_attribute(col_source)

                    if kwargs.get("reduceAlleles", True) and \
                            all(a == attribute[0] for a in attribute):
                        attribute = [attribute[0]]
                    attribute = list(
                        map(
                            partial(col_formatter, col_format=col_format),
                            attribute))
                    row_variant.append(attribute)

            except (
                AttributeError, KeyError, IndexError, AssertionError,
                Exception,
            ):
                if isinstance(v, FamilyVariant):
                    logger.info(
                        "problem building family variant %s, %s",
                        v, v.family_id,
                    )
                else:
                    logger.info(
                        "problem building summary variant %s", v)

        return row_variant

    @staticmethod
    def _gene_view_summary_download_variants_iterator(
        variants: Iterable[SummaryVariant],
        frequency_column: str,
        summary_variants_ids: set[str],
    ) -> Generator[list[str | int | bool | None], None, None]:
        for v in variants:
            for aa in v.alt_alleles:
                if summary_variants_ids is not None:
                    svid = f"{aa.cshl_location}:{aa.cshl_variant}"
                    if svid not in summary_variants_ids:
                        continue

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
        variant: SummaryVariant, frequency_column: str,
    ) -> Generator[dict[str, Any], None, None]:
        """Transform gene view summary response into dicts."""
        out: dict[str, Any] = {
            "svuid": variant.svuid,
        }
        alleles = [
            {
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
            }
            for aa in variant.alt_alleles
        ]
        out["alleles"] = alleles
        yield out

    def transform_gene_view_summary_variant_download(
        self,
        variants: Iterable[SummaryVariant],
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
            "seen_in_unaffected",
        ]

        rows = self._gene_view_summary_download_variants_iterator(
                variants, frequency_column, summary_variant_ids,
            )

        return map(join_line, itertools.chain([columns], rows))  # type: ignore

    def variant_transformer(self) -> Callable[[FamilyVariant], FamilyVariant]:
        """Build and return a variant transformer function."""
        assert not self.study_wrapper.is_remote
        pheno_column_values = self._get_all_pheno_values()

        def transformer(variant: FamilyVariant) -> FamilyVariant:
            pheno_values = self._get_pheno_values_for_variant(
                variant, pheno_column_values,
            )

            for allele in variant.alt_alleles:
                fallele = cast(FamilyAllele, allele)
                gene_scores_values = self._get_gene_scores_values(
                    fallele,
                )
                fallele.update_attributes(gene_scores_values)

                if pheno_values:
                    fallele.update_attributes(pheno_values)

            return variant

        return transformer

    def transform_summary_variants(
        self, variants_iterable: Generator[SummaryVariant, None, None],
    ) -> Generator[list, None, None]:
        for v in self._add_additional_columns_summary(variants_iterable):
            yield self.build_variant_row(
                v, self.study_wrapper.summary_preview_descs,
            )

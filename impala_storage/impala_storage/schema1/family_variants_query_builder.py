import logging
from collections.abc import Callable, Iterable
from typing import Any

from dae.annotation.annotation_pipeline import AttributeInfo
from dae.genomic_resources.gene_models.gene_models import GeneModels
from dae.pedigrees.families_data import FamiliesData
from dae.utils.regions import Region
from dae.variants.attributes import Role, Sex, Status

from impala_storage.schema1.base_query_builder import BaseQueryBuilder
from impala_storage.schema1.serializers import AlleleParquetSerializer

logger = logging.getLogger(__name__)
RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]


class FamilyVariantsQueryBuilder(BaseQueryBuilder):
    """Build queries related to family variants."""

    def __init__(
        self, db: str,
        variants_table: str,
        pedigree_table: str, *,
        variants_schema: list[AttributeInfo],
        table_properties: dict[str, Any],
        pedigree_schema: dict[str, str],
        families: FamiliesData,
        gene_models: GeneModels | None = None,
        do_join: bool = False,
    ) -> None:
        self.do_join = do_join
        super().__init__(
            db, variants_table, pedigree_table,
            variants_schema, table_properties, pedigree_schema,
            families, gene_models=gene_models)
        self.families = families

    @staticmethod
    def _get_pedigree_column_value(source: str, str_value: str) -> Any:
        if source == "status":
            return Status.from_name(str_value).value
        if source == "role":
            return Role.from_name(str_value).value
        if source == "sex":
            return Sex.from_name(str_value).value

        return f'"{str_value}"'

    def _query_columns(self) -> list[str]:
        self.select_accessors = {
            "bucket_index": "variants.bucket_index",
            "summary_index": "variants.summary_index",
            "chromosome": "variants.chromosome",
            "`position`": "variants.`position`",
            "end_position": "variants.end_position",
            "variant_type": "variants.variant_type",
            "reference": "variants.reference",
            "family_id": "variants.family_id",
            "variant_data": "variants.variant_data",
        }
        if self.has_extra_attributes:
            self.select_accessors["extra_attributes"] = \
                "variants.extra_attributes"
        if not self.do_join:
            for k in self.select_accessors:
                self.select_accessors[k] = k
        return list(self.select_accessors.values())

    def _where_accessors(self) -> dict[str, str]:
        accessors = super()._where_accessors()

        if self.do_join:
            for key, value in accessors.items():
                accessors[key] = f"variants.{value}"
        return accessors

    def build_from(self) -> None:
        if self.do_join:
            from_clause = f"FROM {self.db}.{self.variants_table} as variants"
        else:
            from_clause = f"FROM {self.db}.{self.variants_table}"
        self._add_to_product(from_clause)

    def build_join(self) -> None:
        if not self.do_join:
            return
        join_clause = f"JOIN {self.db}.{self.pedigree_table} as pedigree"
        self._add_to_product(join_clause)

    def _build_pedigree_where(
        self, pedigree_fields: tuple[list[str], list[str]],
    ) -> str:
        assert len(pedigree_fields) == 2, pedigree_fields

        def pedigree_where_clause(
            query_fields: list[dict[str, str]], sign: str,
        ) -> list[list[str]]:
            clause = []
            for person_set_query in query_fields:

                person_set_clause = []
                for source, str_value in person_set_query.items():
                    value = self._get_pedigree_column_value(
                        source, str_value)
                    person_set_clause.append(
                        f"pedigree.{source} {sign} {value}",
                    )
                clause.append(person_set_clause)
            return clause

        positive, negative = pedigree_fields

        if len(positive) > 0:
            assert len(negative) == 0
            clause = [
                " AND ".join(person_set_clause)
                for person_set_clause in pedigree_where_clause(
                    positive, "=")  # type: ignore
            ]
            return " OR ".join([
                f"( {wc} )" for wc in clause])

        if len(negative) > 0:
            assert len(positive) == 0
            clause = [
                " OR ".join(person_set_clause)
                for person_set_clause in pedigree_where_clause(
                    negative, "!=")  # type: ignore
            ]
            return " AND ".join([
                f"( {wc} )" for wc in clause])

        logger.error(
            "unexpected pedigree_fields argument: %s",
            pedigree_fields)
        raise ValueError("unexpected pedigree_fields argument")

    # pylint: disable=arguments-differ,too-many-arguments
    def build_where(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: Iterable[str] | None = None,
        person_ids: Iterable[str] | None = None,
        inheritance: list[str] | str | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        affected_statuses: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        # pylint: disable=unused-argument
        where_clause = self._base_build_where(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            affected_statuses=affected_statuses,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
        )
        self._add_to_product(where_clause)

        if not self.do_join:
            return

        if where_clause:
            in_members = "AND variants.variant_in_members = pedigree.person_id"
        else:
            in_members = \
                "WHERE variants.variant_in_members = pedigree.person_id"
        self._add_to_product(in_members)

    def build_group_by(self) -> None:
        # nothing to do for family variants
        pass

    def create_row_deserializer(
        self, serializer: AlleleParquetSerializer,
    ) -> Callable:
        seen = set()

        def deserialize_row(row: tuple) -> Any | None:
            cols = {}
            for idx, col_name in enumerate(self.query_columns):
                cols[col_name] = row[idx]

            bucket_index = cols[self.select_accessors["bucket_index"]]
            summary_index = cols[self.select_accessors["summary_index"]]
            family_id = cols[self.select_accessors["family_id"]]
            chrom = cols[self.select_accessors["chromosome"]]
            position = cols[self.select_accessors["`position`"]]
            end_position = cols[self.select_accessors["end_position"]]
            reference = cols[self.select_accessors["reference"]]
            variant_data = cols[self.select_accessors["variant_data"]]

            extra_attributes = None
            extra_attr_sel = self.select_accessors.get("extra_attributes")
            if extra_attr_sel is not None:
                extra_attributes = cols.get(extra_attr_sel)

            fvuid = f"{bucket_index}:{summary_index}:{family_id}"
            if fvuid in seen:
                return None
            seen.add(fvuid)

            if isinstance(variant_data, str):
                logger.debug(
                    "variant_data is string!!!! %s, %s, %s, %s, %s",
                    family_id, chrom, position, end_position, reference,
                )
                variant_data = bytes(variant_data, "utf8")
            if isinstance(extra_attributes, str):
                extra_attributes = bytes(extra_attributes, "utf8")

            family = self.families.get(family_id)
            if family is None:
                return None
            return serializer.deserialize_family_variant(
                variant_data, family, extra_attributes,
            )

        return deserialize_row

import logging
import abc
import configparser

from typing import Optional, Any

import pandas as pd

from dae.pedigrees.family import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.query_variants.query_runners import QueryRunner
from dae.inmemory_storage.raw_variants import RawFamilyVariants
from dae.query_variants.sql.schema2.family_builder import FamilyQueryBuilder
from dae.query_variants.sql.schema2.summary_builder import SummaryQueryBuilder

logger = logging.getLogger(__name__)


class SqlSchema2Variants(abc.ABC):
    """Base class for Schema2 SQL like variants' query interface."""

    RUNNER_CLASS: type[QueryRunner]

    def __init__(
            self,
            dialect,
            db,
            family_variant_table,
            summary_allele_table,
            pedigree_table,
            meta_table,
            gene_models=None):
        assert db
        assert pedigree_table

        self.dialect = dialect
        self.db = db
        self.family_variant_table = family_variant_table
        self.summary_allele_table = summary_allele_table
        self.pedigree_table = pedigree_table
        self.meta_table = meta_table
        self.gene_models = gene_models

        self.summary_allele_schema = self._fetch_schema(
            self.summary_allele_table
        )
        self.family_variant_schema = self._fetch_schema(
            self.family_variant_table
        )
        self.combined_columns = {
            **self.family_variant_schema,
            **self.summary_allele_schema,
        }

        self.pedigree_schema = self._fetch_schema(self.pedigree_table)
        self.ped_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(self.ped_df)
        # Temporary workaround for studies that are imported without tags
        FamiliesLoader._build_families_tags(
            self.families, {"ped_tags": True}
        )

        _tbl_props = self._fetch_tblproperties()
        self.table_properties = self._normalize_tblproperties(_tbl_props)

    @abc.abstractmethod
    def _fetch_schema(self, table) -> dict[str, str]:
        """Fetch schema of a table and return it as a Dict."""

    @abc.abstractmethod
    def _fetch_pedigree(self) -> pd.DataFrame:
        """Fetch the pedigree and return it as a data frame."""

    @abc.abstractmethod
    def _fetch_tblproperties(self) -> Optional[configparser.ConfigParser]:
        """Fetch partion description from metadata table."""

    @staticmethod
    def _normalize_tblproperties(tbl_props) -> dict:
        if tbl_props is None:
            return {
                "region_length": 0,
                "chromosomes": [],
                "family_bin_size": 0,
                "coding_effect_types": set(),
                "rare_boundary": 0
            }

        return {
            "region_length": int(
                tbl_props["region_bin"]["region_length"]
            ),
            "chromosomes": [
                c.strip()
                for c in tbl_props["region_bin"]["chromosomes"].split(",")
            ],
            "family_bin_size": int(
                tbl_props["family_bin"]["family_bin_size"]
            ),
            "rare_boundary": int(
                tbl_props["frequency_bin"]["rare_boundary"]
            ),
            "coding_effect_types": set(
                s.strip()
                for s in tbl_props["coding_bin"][
                    "coding_effect_types"
                ].split(",")
            ),
        }

    @abc.abstractmethod
    def _get_connection_factory(self) -> Any:
        """Return the connection factory for specific SQL engine."""

    @abc.abstractmethod
    def _deserialize_summary_variant(self, record):
        """Deserialize a summary variant from SQL record."""

    @abc.abstractmethod
    def _deserialize_family_variant(self, record):
        """Deserialize a family variant from SQL record."""

    # pylint: disable=too-many-arguments
    def build_summary_variants_query_runner(
            self,
            regions=None,
            genes=None,
            effect_types=None,
            family_ids=None,
            person_ids=None,
            inheritance=None,
            roles=None,
            sexes=None,
            variant_type=None,
            real_attr_filter=None,
            ultra_rare=None,
            frequency_filter=None,
            return_reference=None,
            return_unknown=None,
            limit=None) -> QueryRunner:
        """Build a query selecting the appropriate summary variants."""
        query_builder = SummaryQueryBuilder(
            self.dialect,
            self.db,
            self.family_variant_table,
            self.summary_allele_table,
            self.pedigree_table,
            self.family_variant_schema,
            self.summary_allele_schema,
            self.table_properties,
            self.pedigree_schema,
            self.ped_df,
            gene_models=self.gene_models,
            do_join_affected=False,
        )

        query = query_builder.build_query(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit,
        )
        logger.debug("SUMMARY VARIANTS QUERY: %s", query)

        # pylint: disable=protected-access
        runner = self.RUNNER_CLASS(
            self._get_connection_factory(), query,
            deserializer=self._deserialize_summary_variant)

        filter_func = RawFamilyVariants.summary_variant_filter_function(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit)

        runner.adapt(filter_func)

        return runner

    # pylint: disable=too-many-arguments,too-many-locals
    def build_family_variants_query_runner(
            self,
            regions=None,
            genes=None,
            effect_types=None,
            family_ids=None,
            person_ids=None,
            inheritance=None,
            roles=None,
            sexes=None,
            variant_type=None,
            real_attr_filter=None,
            ultra_rare=None,
            frequency_filter=None,
            return_reference=None,
            return_unknown=None,
            limit=None,
            pedigree_fields=None):
        """Build a query selecting the appropriate family variants."""
        do_join_pedigree = pedigree_fields is not None
        query_builder = FamilyQueryBuilder(
            self.dialect,
            self.db,
            self.family_variant_table,
            self.summary_allele_table,
            self.pedigree_table,
            self.family_variant_schema,
            self.summary_allele_schema,
            self.table_properties,
            self.pedigree_schema,
            self.ped_df,
            gene_models=self.gene_models,
            do_join_pedigree=do_join_pedigree,
        )

        query = query_builder.build_query(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit,
            pedigree_fields=pedigree_fields
        )

        logger.debug("FAMILY VARIANTS QUERY: %s", query)
        deserialize_row = self._deserialize_family_variant

        # pylint: disable=protected-access
        runner = self.RUNNER_CLASS(
            self._get_connection_factory(), query,
            deserializer=deserialize_row)

        filter_func = RawFamilyVariants.family_variant_filter_function(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit)

        runner.adapt(filter_func)

        return runner

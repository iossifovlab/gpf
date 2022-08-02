import time
import json
import logging
import configparser
from contextlib import closing
from typing import Iterator, Optional
import numpy as np
from impala.util import as_pandas
from dae.pedigrees.family import FamiliesData
from dae.variants.attributes import Role, Status, Sex
from dae.backends.schema2.base_query_builder import Dialect
from dae.backends.schema2.family_builder import FamilyQueryBuilder
from dae.backends.schema2.summary_builder import SummaryQueryBuilder
from dae.variants.variant import SummaryVariant, SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant

logger = logging.getLogger(__name__)


class ImpalaDialect(Dialect):
    def __init__(self):
        super().__init__()


class ImpalaVariants:
    """A backend implementing an impala backend."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        impala_helpers,
        db,
        family_variant_table,
        summary_allele_table,
        pedigree_table,
        meta_table,
        gene_models=None,
    ):

        super().__init__()
        assert db
        assert pedigree_table

        self.dialect = ImpalaDialect()
        self.db = db
        self._impala_helpers = impala_helpers
        self.family_variant_table = family_variant_table
        self.summary_allele_table = summary_allele_table
        self.pedigree_table = pedigree_table
        self.meta_table = meta_table
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
        self.pedigree_schema = self._fetch_pedigree_schema()
        self.ped_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(self.ped_df)

        assert gene_models is not None
        self.gene_models = gene_models

        _tbl_props = self._fetch_tblproperties(self.meta_table)

        # pass config to PartitionDesciption

        if _tbl_props is not None:
            self.table_properties = {
                "region_length": int(
                    _tbl_props["region_bin"]["region_length"]
                ),
                "chromosomes": list(
                    map(
                        lambda c: c.strip(),
                        _tbl_props["region_bin"]["chromosomes"].split(","),
                    )
                ),
                "family_bin_size": int(
                    _tbl_props["family_bin"]["family_bin_size"]
                ),
                "rare_boundary": int(
                    _tbl_props["frequency_bin"]["rare_boundary"]
                ),
                "coding_effect_types": set(
                    lambda s: s.strip()
                    for s in _tbl_props["coding_bin"][
                        "coding_effect_types"
                    ].split(",")
                ),
            }
        else:
            self.table_properties = {
                "region_length": 0,
                "chromosomes": [],
                "family_bin_size": 0,
                "coding_effect_types": [],
                "rare_boundary": 0
            }

    def connection(self):
        conn = self._impala_helpers.connection()
        logger.debug(
            "getting connection to host %s from impala helpers %s",
            conn.host, id(self._impala_helpers)
        )
        return conn

    def _fetch_schema(self, table) -> dict[str, str]:
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"""DESCRIBE {self.db}.{table}"""
                cursor.execute(query)
                df = as_pandas(cursor)

            records = df[["name", "type"]].to_records()
            schema = {
                col_name: col_type for (_, col_name, col_type) in records
            }
            return schema

    def _fetch_tblproperties(self, meta_table) \
            -> Optional[configparser.ConfigParser]:
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"""SELECT value FROM {self.db}.{meta_table}
                            WHERE key = 'partition_description'
                            LIMIT 1
                """

                cursor.execute(query)
                config = configparser.ConfigParser()

                for row in cursor:
                    config.read_string(row[0])
                    return config
        return None

    def _summary_variants_iterator(
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
        affected_status=None,
    ) -> Iterator[SummaryVariant]:
        # pylint: disable=too-many-arguments,too-many-locals
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
            affected_status=affected_status,
        )

        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)

                for row in cursor:
                    try:
                        sv_record = json.loads(row[-1])
                        summary_variant = (
                            SummaryVariantFactory.summary_variant_from_records(
                                sv_record
                            )
                        )
                        if summary_variant is None:  # TODO WHY?
                            continue
                        yield summary_variant
                    except Exception as ex:  # pylint: disable=broad-except
                        logger.error(
                            "Unable to deserialize summary variant (BQ)"
                        )
                        logger.exception(ex)
                        continue

    def _family_variants_iterator(
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
        affected_status=None,
    ):
        # pylint: disable=too-many-arguments,too-many-locals
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                do_join_affected = affected_status is not None
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
                    do_join_affected=do_join_affected,
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
                    affected_status=affected_status,
                )

                logger.info("FAMILY VARIANTS QUERY (%s):\n %s", conn.host,
                            query)
                start = time.perf_counter()
                cursor.execute(query)
                end = time.perf_counter()
                logger.info("TIME (IMPALA DB): %s", end - start)

                for row in cursor:
                    try:
                        # columns: ..summary_variant_data, family_variant_data
                        sv_record = json.loads(row[-2])
                        fv_record = json.loads(row[-1])

                        family_variant = FamilyVariant(
                            SummaryVariantFactory.summary_variant_from_records(
                                sv_record
                            ),
                            self.families[fv_record["family_id"]],
                            np.array(fv_record["genotype"]),
                            np.array(fv_record["best_state"]),
                        )

                        yield family_variant
                    except Exception as ex:  # pylint: disable=broad-except
                        logger.info(
                            "unable to deserialize family variant (IMPALA)"
                        )
                        logger.exception(ex)
                        continue

    def query_summary_variants(
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
    ):
        """Query summary variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if limit is None:
            count = -1
        else:
            count = limit
            limit = 10 * limit  # TODO WHY?

        with closing(
            self._summary_variants_iterator(
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
        ) as sv_iterator:
            for summary_variant in sv_iterator:
                yield summary_variant
                count -= 1
                if count == 0:
                    break

    def query_variants(
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
        affected_status=None,
    ):
        """Query family variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if limit is None:
            count = -1
        else:
            count = limit
            limit = 10 * limit

        with closing(
            self._family_variants_iterator(
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
                affected_status=affected_status,
            )
        ) as fv_iterator:

            for family_variant in fv_iterator:
                yield family_variant
                count -= 1
                if count == 0:
                    break

    def _fetch_pedigree(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"""SELECT * FROM {self.db}.{self.pedigree_table}"""
                cursor.execute(query)
                ped_df = as_pandas(cursor)

        ped_df.role = ped_df.role.apply(Role)
        ped_df.sex = ped_df.sex.apply(Sex)
        ped_df.status = ped_df.status.apply(Status)

        return ped_df

    def _fetch_pedigree_schema(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"""DESCRIBE {self.db}.{self.pedigree_table}"""
                cursor.execute(query)
                df = as_pandas(cursor)

                records = df[["name", "type"]].to_records()
                schema = {
                    col_name: col_type for (_, col_name, col_type) in records
                }
                return schema

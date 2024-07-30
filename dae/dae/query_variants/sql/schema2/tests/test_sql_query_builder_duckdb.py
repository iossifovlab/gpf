# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from typing import Any

import duckdb
import pytest

from dae.duckdb_storage.duckdb2_variants import DuckDb2Variants
from dae.duckdb_storage.duckdb_genotype_storage import DuckDbGenotypeStorage
from dae.gpf_instance import GPFInstance
from dae.query_variants.sql.schema2.sql_query_builder import (
    Db2Layout,
    SqlQueryBuilder,
)
from dae.studies.study import GenotypeData
from dae.utils.regions import Region


@pytest.fixture()
def duckdb2_variants(
    t4c8_study_1: GenotypeData,
    duckdb_storage: DuckDbGenotypeStorage,
    t4c8_instance: GPFInstance,
) -> DuckDb2Variants:
    base_dir = duckdb_storage.get_base_dir()
    db_file = duckdb_storage.get_db()
    assert base_dir is not None
    assert db_file is not None

    db_filename = os.path.join(
        base_dir,
        db_file,
    )
    assert os.path.exists(db_filename)
    study_storage = t4c8_study_1.config.genotype_storage

    meta_table = study_storage.tables.meta
    assert meta_table is not None

    db_layout = Db2Layout(
        db=db_filename,
        study=t4c8_study_1.study_id,
        pedigree=study_storage.tables.pedigree,
        summary=study_storage.tables.summary,
        family=study_storage.tables.family,
        meta=study_storage.tables.meta,
    )

    assert db_layout is not None
    connection = duckdb.connect(db_filename, read_only=True)
    duckdb_variants = DuckDb2Variants(
        connection,
        db_layout,
        t4c8_instance.gene_models,
        t4c8_instance.reference_genome,
    )
    duckdb_variants.query_builder.GENE_REGIONS_HEURISTIC_EXTEND = 0
    return duckdb_variants


@pytest.fixture()
def query_builder(
    duckdb2_variants: DuckDb2Variants,
) -> SqlQueryBuilder:
    sql_query_builder = duckdb2_variants.query_builder
    assert sql_query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
    return sql_query_builder


@pytest.mark.parametrize("params, count", [
    ({"genes": ["t4"]}, 1),
    ({"genes": ["c8"]}, 2),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["synonymous"]}, 3),
    ({"regions": [Region("chr1")]}, 3),
    ({"regions": [Region("chr1", None, 55)]}, 1),
    ({"regions": [Region("chr1", 55, None)]}, 2),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, 3),
    ({"frequency_filter": [("af_allele_freq", (15.0, None))]}, 1),
    ({"real_attr_filter": [("af_allele_count", (None, 1))]}, 3),
    ({"real_attr_filter": [("af_allele_count", (1, None))]}, 3),
    ({"real_attr_filter": [("af_allele_count", (1, 1))]}, 3),
    ({"real_attr_filter": [("af_allele_count", (2, None))]}, 1),
    ({"real_attr_filter": [("af_allele_count", (2, 2))]}, 1),
    ({"limit": 1}, 1),
    ({"limit": 2}, 2),
])
def test_query_summary_variants_counting(
    params: dict[str, Any],
    count: int,
    duckdb2_variants: DuckDb2Variants,
) -> None:
    svs = list(duckdb2_variants.query_summary_variants(**params))
    assert len(svs) == count


@pytest.mark.parametrize("params, count", [
    ({"genes": ["t4"]}, 1),
    ({"genes": ["c8"]}, 3),
    ({"effect_types": ["missense"]}, 2),
    ({"effect_types": ["synonymous"]}, 3),
    ({"regions": [Region("chr1")]}, 4),
    ({"regions": [Region("chr1", None, 55)]}, 1),
    ({"regions": [Region("chr1", 55, None)]}, 3),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, 3),
    ({"frequency_filter": [("af_allele_freq", (15.0, None))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (None, 1))]}, 3),
    ({"real_attr_filter": [("af_allele_count", (1, None))]}, 4),
    ({"real_attr_filter": [("af_allele_count", (1, 1))]}, 3),
    ({"real_attr_filter": [("af_allele_count", (2, None))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (2, 2))]}, 2),
    ({"limit": 1}, 1),
    ({"limit": 2}, 2),
])
def test_query_family_variants_counting(
    params: dict[str, Any],
    count: int,
    duckdb2_variants: DuckDb2Variants,
) -> None:
    fvs = list(duckdb2_variants.query_variants(**params))
    assert len(fvs) == count

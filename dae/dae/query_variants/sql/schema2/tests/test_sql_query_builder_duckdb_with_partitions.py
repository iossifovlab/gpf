# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
from typing import Any, Optional

import pytest

import duckdb

from dae.utils.regions import Region
from dae.query_variants.sql.schema2.sql_query_builder import Db2Layout

from dae.duckdb_storage.duckdb_genotype_storage import DuckDbGenotypeStorage
from dae.genotype_storage.genotype_storage_registry import \
    get_genotype_storage_factory

from dae.query_variants.sql.schema2.sql_query_builder import SqlQueryBuilder
from dae.parquet.partition_descriptor import PartitionDescriptor

from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData

from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.t4c8_import import t4c8_gpf


@pytest.fixture(scope="module")
def duckdb_storage(
    tmp_path_factory: pytest.TempPathFactory
) -> DuckDbGenotypeStorage:
    storage_path = tmp_path_factory.mktemp("duckdb_storage")
    storage_config = {
        "id": "duckdb_test",
        "storage_type": "duckdb",
        "db": "duckdb_storage/test.duckdb",
        "base_dir": str(storage_path)
    }
    storage_factory = get_genotype_storage_factory("duckdb")
    assert storage_factory is not None
    storage = storage_factory(storage_config)
    assert storage is not None
    assert isinstance(storage, DuckDbGenotypeStorage)
    return storage


@pytest.fixture(scope="module")
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
    duckdb_storage: DuckDbGenotypeStorage,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_instance")
    gpf_instance = t4c8_gpf(root_path, duckdb_storage)
    return gpf_instance


@pytest.fixture(scope="module")
def t4c8_study_1(
    t4c8_instance: GPFInstance,
    duckdb_storage: DuckDbGenotypeStorage
) -> GenotypeData:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_1" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_1" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS  ID REF ALT  QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   4    .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/1  0/2  0/2
chr1   54   .  T   C    .    .      .    GT     0/1  0/1  0/1 0/1  0/0  0/1
chr1   90   .  G   C,GA .    .      .    GT     0/1  0/2  0/2 0/1  0/2  0/1
chr1   100  .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/2  0/2  0/0
chr1   119  .  A   G,C  .    .      .    GT     0/0  0/2  0/2 0/1  0/2  0/1
chr1   122  .  A   C,AC .    .      .    GT     0/1  0/1  0/1 0/2  0/2  0/2
        """)  # noqa

    project_config_update = {
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 100,
            },
            "frequency_bin": {
                "rare_boundary": 25.0,
            },
            "coding_bin": {
                "coding_effect_types": [
                    "frame-shift",
                    "noStart",
                    "missense",
                    "synonymous",
                ]
            },
            "family_bin": {
                "family_bin_size": 2,
            }
        },
    }

    study = vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
    )
    duckdb_storage.shutdown()
    return study


@pytest.fixture(scope="module")
def query_builder(
    t4c8_study_1: GenotypeData,
    duckdb_storage: DuckDbGenotypeStorage,
    t4c8_instance: GPFInstance,
) -> SqlQueryBuilder:
    base_dir = duckdb_storage.get_base_dir()
    db_file = duckdb_storage.get_db()
    assert base_dir is not None
    assert db_file is not None

    db_filename = os.path.join(
        base_dir,
        db_file
    )
    assert os.path.exists(db_filename)
    study_storage = t4c8_study_1.config.genotype_storage

    meta_table = study_storage.tables.meta
    assert meta_table is not None

    with duckdb.connect(db_filename, read_only=True) as connection:
        with connection.cursor() as cursor:
            query = f"""SELECT value FROM {meta_table}
                WHERE key = 'summary_schema'
                LIMIT 1
                """

            schema_content = ""
            result = cursor.execute(query).fetchall()
            for row in result:
                schema_content = row[0]
            summary_schema = dict(
                line.split("|") for line in schema_content.split("\n"))

    with duckdb.connect(db_filename, read_only=True) as connection:
        with connection.cursor() as cursor:
            query = f"""SELECT value FROM {meta_table}
                WHERE key = 'family_schema'
                LIMIT 1
                """

            schema_content = ""
            result = cursor.execute(query).fetchall()
            for row in result:
                schema_content = row[0]
            family_schema = dict(
                line.split("|") for line in schema_content.split("\n"))

    with duckdb.connect(db_filename, read_only=True) as connection:
        with connection.cursor() as cursor:
            query = f"""SELECT value FROM {meta_table}
                WHERE key = 'partition_description'
                LIMIT 1
                """

            content = ""
            result = cursor.execute(query).fetchall()
            for row in result:
                content = row[0]
            partition_descriptor = PartitionDescriptor.parse_string(content)

    db_layout = Db2Layout(
        db=db_filename,
        study=t4c8_study_1.study_id,
        pedigree=study_storage.tables.pedigree,
        pedigree_schema={},
        summary=study_storage.tables.summary,
        summary_schema=summary_schema,
        family=study_storage.tables.family,
        family_schema=family_schema,
        meta=study_storage.tables.meta,
    )

    assert db_layout is not None

    sql_query_builder = SqlQueryBuilder(
        db_layout,
        partition_descriptor,
        t4c8_study_1.families,
        t4c8_instance.gene_models,
        t4c8_instance.reference_genome
    )
    return sql_query_builder


def test_query_summary_variants_simple(
    query_builder: SqlQueryBuilder
) -> None:
    query = query_builder.build_summary_variants_query()
    assert query is not None

    db_layout = query_builder.db_layout
    with duckdb.connect(db_layout.db, read_only=True) as connection:
        with connection.cursor() as cursor:
            result = cursor.execute(query).fetchall()
            assert len(result) == 6


@pytest.mark.parametrize("index, params, count", [
    (0, {"genes": ["t4"]}, 1),
    (1, {"genes": ["c8"]}, 3),
    (2, {"effect_types": ["missense"]}, 1),
    (3, {"effect_types": ["synonymous"]}, 3),
    (4, {"regions": [Region("chr1")]}, 6),
    (5, {"regions": [Region("chr1", None, 55)]}, 2),
    (6, {"regions": [Region("chr1", 55, None)]}, 4),
    (7, {"frequency_filter": [("af_allele_freq", (None, 15.0))]}, 2),
    (8, {"frequency_filter": [("af_allele_freq", (15.0, None))]}, 6),
    (9, {"frequency_filter": [("af_allele_freq", (None, 25.0))]}, 5),
    (10, {"frequency_filter": [("af_allele_freq", (25.0, None))]}, 6),
    (11, {"real_attr_filter": [("af_allele_count", (None, 1))]}, 2),
    (12, {"real_attr_filter": [("af_allele_count", (1, None))]}, 6),
    (13, {"real_attr_filter": [("af_allele_count", (1, 1))]}, 2),
    (14, {"real_attr_filter": [("af_allele_count", (2, None))]}, 6),
    (15, {"real_attr_filter": [("af_allele_count", (2, 2))]}, 4),
    (16, {"limit": 1}, 1),
    (17, {"limit": 2}, 2),
    (15, {"ultra_rare": True}, 2),
])
def test_query_summary_variants_counting(
    index: int,
    params: dict[str, Any],
    count: int,
    query_builder: SqlQueryBuilder
) -> None:
    query_builder.GENE_REGIONS_HEURISTIC_EXTEND = 2
    query = query_builder.build_summary_variants_query(**params)
    assert query is not None

    db_layout = query_builder.db_layout
    with duckdb.connect(db_layout.db, read_only=True) as connection:
        with connection.cursor() as cursor:
            result = cursor.execute(query).fetchall()
            assert len(result) == count


@pytest.mark.parametrize("index, params, coding_bin", [
    (0, {"effect_types": ["missense"]}, 1),
    (1, {"effect_types": ["synonymous"]}, 1),
    (2, {"effect_types": ["intergenic"]}, 0),
    (3, {"effect_types": ["intergenic", "synonymous"]}, None),
    (4, {}, None),
])
def test_coding_bin_heuristics_query(
    index: int,
    params: dict[str, Any],
    coding_bin: Optional[int],
    query_builder: SqlQueryBuilder
) -> None:
    query_builder.GENE_REGIONS_HEURISTIC_EXTEND = 0
    query = query_builder.build_summary_variants_query(**params)
    assert query is not None

    if coding_bin is None:
        assert "coding_bin" not in query
    else:
        assert f"coding_bin = {coding_bin}" in query


@pytest.mark.parametrize("index, params, region_bins", [
    (0, {"regions": [Region("chr1", 2, 20)]}, ["chr1_0"]),
    (1, {"regions": [Region("chr1", 2, 120)]}, ["chr1_0", "chr1_1"]),
    (2, {"regions": [Region("chr1")]}, ["chr1_0", "chr1_1", "chr1_2"]),
    (3, {"regions": [Region("chr1", 105)]}, ["chr1_1", "chr1_2"]),
    (4, {"regions": [Region("chr1", None, 105)]}, ["chr1_0", "chr1_1"]),
])
def test_region_bin_heuristics_query(
    index: int,
    params: dict[str, Any],
    region_bins: Optional[list[str]],
    query_builder: SqlQueryBuilder
) -> None:
    query_builder.GENE_REGIONS_HEURISTIC_EXTEND = 0
    query = query_builder.build_summary_variants_query(**params)
    assert query is not None

    if region_bins is None:
        assert "region_bin" not in query
    else:
        assert "region_bin" in query
        for region_bin in region_bins:
            assert f"'{region_bin}'" in query

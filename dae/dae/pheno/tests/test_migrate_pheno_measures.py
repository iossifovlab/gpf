# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pathlib
from typing import cast
from sqlalchemy.sql import select
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.pheno.pheno_data import PhenotypeStudy
from dae.pheno.registry import PhenoRegistry
from dae.tools.migrate_pheno_measures import main


def test_migrate_pheno_measures_functions(clean_pheno_db_dir: str) -> None:
    main([clean_pheno_db_dir, "--dbs", "fake"])

    pheno_registry = PhenoRegistry()

    pheno_configs = GPFConfigParser.collect_directory_configs(
        clean_pheno_db_dir
    )

    with PhenoRegistry.CACHE_LOCK:
        for config in pheno_configs:
            pheno_registry.register_phenotype_data(
                PhenoRegistry.load_pheno_data(pathlib.Path(config)),
                lock=False
            )

    pheno_data = cast(
        PhenotypeStudy, pheno_registry.get_phenotype_data("fake")
    )
    metadata = pheno_data.db.pheno_metadata
    assert "measures" in metadata.tables.keys()
    assert "instruments" in metadata.tables.keys()
    assert "i1_measure_values" in metadata.tables.keys()
    assert "i2_measure_values" in metadata.tables.keys()


def test_migrate_pheno_measures_values(clean_pheno_db_dir: str) -> None:
    main([clean_pheno_db_dir, "--dbs", "fake"])

    pheno_configs = GPFConfigParser.collect_directory_configs(
        clean_pheno_db_dir
    )

    pheno_registry = PhenoRegistry()

    with PhenoRegistry.CACHE_LOCK:
        for config in pheno_configs:
            pheno_registry.register_phenotype_data(
                PhenoRegistry.load_pheno_data(pathlib.Path(config)),
                lock=False
            )
    db = cast(PhenotypeStudy, pheno_registry.get_phenotype_data("fake")).db

    with db.pheno_engine.connect() as connection:
        table = db.instrument_values_tables["i1"]
        query = select(table).where(table.c.person_id == "f9.s3")
        result = list(connection.execute(query))[0]._mapping

        assert result["person_id"] == "f9.s3"
        assert result["family_id"] == "f9"
        assert result["role"] == "sib"
        assert result["i1_age"] == 181.57243659222985
        assert result["i1_iq"] == 143.877335515254
        assert result["i1_m1"] == 58.9790551741459
        assert result["i1_m2"] == 36.290690684019935
        assert result["i1_m3"] == 76.42214586628911
        assert result["i1_m4"] == 5.0
        assert result["i1_m5"] == "catC"
        assert result["i1_m6"] is None
        assert result["i1_m7"] == 72.98241821928552
        assert result["i1_m8"] == 2.0
        assert result["i1_m9"] == "valA"
        assert result["i1_m10"] == 55.96855614275782

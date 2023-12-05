# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pytest
from sqlalchemy.sql import select
from dae.tools.build_pheno_measures import main


@pytest.fixture
def mock_gpf_instance(mocker, fake_phenotype_data):
    gpf_instance = mocker.MagicMock()
    gpf_instance.get_phenotype_data_ids.return_value = ["fake"]
    gpf_instance.get_phenotype_data.return_value = fake_phenotype_data
    return gpf_instance


def test_build_pheno_measures_functions(mock_gpf_instance):
    main(["--dbs", "fake"], gpf_instance=mock_gpf_instance)

    pheno_db = mock_gpf_instance.get_phenotype_data("fake")
    metadata = pheno_db.db.pheno_metadata
    assert "measures" in metadata.tables.keys()
    assert "instruments" in metadata.tables.keys()
    assert "i1_measure_values" in metadata.tables.keys()
    assert "i2_measure_values" in metadata.tables.keys()


def test_build_pheno_measures_values(mock_gpf_instance):
    main(["--dbs", "fake"], gpf_instance=mock_gpf_instance)
    db = mock_gpf_instance.get_phenotype_data("fake").db

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

# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
import time
from pathlib import Path

import duckdb
import pytest
from sqlglot.expressions import table_

from dae.genomic_resources.testing import (
    setup_directories,
)
from dae.pheno.common import (
    InstrumentConfig,
    MeasureDescriptionsConfig,
    PhenoImportConfig,
)
from dae.pheno.pheno_data import PhenotypeStudy
from dae.pheno.pheno_import import (
    ImportInstrument,
    ImportManifest,
    collect_instruments,
    load_descriptions,
    main,
)
from dae.testing import (
    setup_pedigree,
)


@pytest.fixture
def import_data_fixture(
        tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, Path, Path, Path]:
    root_path = tmp_path_factory.mktemp("pheno_import")
    ped_path = setup_pedigree(
        root_path / "pedigree.ped",
        """
        familyId	personId	dadId	momId	sex	status	role	layout	test_col
        fam1	fam1.mom	0	0	2	1	mom	1:53.5,50.0	test1
        fam1	fam1.dad	0	0	1	1	dad	1:10.0,50.0	test2
        fam1	fam1.prb	fam1.dad	fam1.mom	2	2	prb	2:31.75,80.0	test3
        fam2	fam2.mom	0	0	2	1	mom	1:53.5,50.0	test4
        fam2	fam2.dad	0	0	1	1	dad	1:10.0,50.0	test5
        fam2	fam2.prb	fam2.dad	fam2.mom	2	2	prb	2:31.75,80.0	test6
        fam3	fam3.mom	0	0	2	1	mom	1:53.5,50.0	test7
        fam3	fam3.dad	0	0	1	1	dad	1:10.0,50.0	test8
        fam3	fam3.prb	fam3.dad	fam3.mom	2	2	prb	2:31.75,80.0	test9
        fam4	fam4.mom	0	0	2	1	mom	1:53.5,50.0	test10
        fam4	fam4.dad	0	0	1	1	dad	1:10.0,50.0	test11
        fam4	fam4.prb	fam4.dad	fam4.mom	2	2	prb	2:31.75,80.0	test12
        """)  # noqa: E501
    setup_directories(root_path, {
        "instruments": {
            "instr1.csv": textwrap.dedent("""
                person_id,m1,m2,m3
                fam1.mom,1,8,3
                fam1.dad,3,1,3
                fam1.prb,4,0,3
                fam2.mom,9,4,3
                fam2.dad,10,,3
                fam2.prb,23,asdf,3
            """),
        },
    })
    instruments_dir = root_path / "instruments"
    out_dir = root_path / "out"
    tasks_dir = root_path / "tasks"
    return ped_path, instruments_dir, out_dir, tasks_dir


def test_simple_import(
    import_data_fixture: tuple[Path, Path, Path, Path],
) -> None:
    ped_path, instruments_dir, out_dir, tasks_dir = import_data_fixture

    argv = [
        "-p",
        str(ped_path.absolute()),
        "-i",
        str(instruments_dir.absolute()),
        "-j",
        "1",
        "-o",
        str(out_dir.absolute()),
        "-d",
        str(tasks_dir.absolute()),
        "--pheno-id",
        "test",
    ]
    main(argv)
    study = PhenotypeStudy("test", str(out_dir / "test.db"))
    assert set(study.measures.keys()) == {
        "instr1.m1",
        "instr1.m2",
        "instr1.m3",
        "pheno_common.test_col",
    }


def test_import_no_pheno_common(
    import_data_fixture: tuple[Path, Path, Path, Path],
) -> None:
    ped_path, instruments_dir, out_dir, tasks_dir = import_data_fixture

    argv = [
        "-p",
        str(ped_path.absolute()),
        "-i",
        str(instruments_dir.absolute()),
        "-j",
        "1",
        "-o",
        str(out_dir.absolute()),
        "-d",
        str(tasks_dir.absolute()),
        "--pheno-id",
        "test",
        "--skip-pheno-common",
    ]
    main(argv)

    study = PhenotypeStudy("test", str(out_dir / "test.db"))
    assert set(study.measures.keys()) == {
        "instr1.m1",
        "instr1.m2",
        "instr1.m3",
    }


def test_write_and_read_manifest(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    tmp_dir = tmp_path_factory.mktemp("pheno_import_manifest")
    dbfile = tmp_dir / "db"
    connection = duckdb.connect(dbfile)
    table = table_("test")
    import_config = PhenoImportConfig(
        id="asdf",
        input_dir="test",
        work_dir="test1",
        instrument_files=["test"],
        pedigree="test",
        person_column="test",
    )
    ImportManifest.create_table(connection, table)
    start = time.time()
    ImportManifest.write_to_db(connection, table, import_config)
    end = time.time()

    manifest = ImportManifest.from_table(connection, table)[0]

    assert manifest is not None
    assert manifest.unix_timestamp > start
    assert manifest.unix_timestamp < end
    assert manifest.import_config == import_config


def test_empty_manifest_read(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    tmp_dir = tmp_path_factory.mktemp("pheno_import_manifest")
    dbfile = tmp_dir / "db"
    connection = duckdb.connect(dbfile)
    table = table_("test")
    out = ImportManifest.from_table(connection, table)
    assert len(out) == 0


def test_collect_instruments(tmp_path: pathlib.Path) -> None:
    setup_directories(tmp_path, {
        "instrument_1.csv": "asdf",
        "subdir_1": {
            "instrument_2.txt": "asdf",
        },
        "subdir_2": {
            "subsubdir": {
                "instrument_3.txt": "asdf",
            },
        },
        "instrument_special.csv": "asdf",
    })

    instrument_files: list[str | InstrumentConfig] = [
        "instrument_1.csv",
        "subdir_1",
        "subdir_2/**/*.txt",
        InstrumentConfig(
            path="instrument_special.csv",
            instrument="The Special Instrument",
            delimiter="\t",
            person_column="VIP_id",
        ),
        InstrumentConfig(
            path="instrument_not_so_special.csv",
        ),
    ]

    instruments = collect_instruments(
        PhenoImportConfig(
            id="test",
            input_dir=str(tmp_path),
            work_dir="N/A",
            instrument_files=instrument_files,
            pedigree="N/A",
            delimiter=",",
            person_column="person_id",
        ),
    )
    assert instruments == [
        ImportInstrument(
            [pathlib.Path(tmp_path, "instrument_1.csv")],
            "instrument_1",
            ",",
            "person_id",
        ),
        ImportInstrument(
            [pathlib.Path(tmp_path, "subdir_1", "instrument_2.txt")],
            "instrument_2",
            ",",
            "person_id",
        ),
        ImportInstrument(
            [pathlib.Path(tmp_path, "subdir_2", "subsubdir", "instrument_3.txt")],  # noqa: E501
            "instrument_3",
            ",",
            "person_id",
        ),
        ImportInstrument(
            [pathlib.Path(tmp_path, "instrument_special.csv")],
            "The Special Instrument",
            "\t",
            "VIP_id",
        ),
        ImportInstrument(
            [pathlib.Path(tmp_path, "instrument_not_so_special.csv")],
            "instrument_not_so_special",
            ",",
            "person_id",
        ),
    ]


def test_load_descriptions_files(tmp_path: pathlib.Path) -> None:
    pathlib.Path(tmp_path, "i1_descriptions.tsv").write_text(
       "instrumentName\tmeasureName\tdescription\n"
       "testInstrument1\tmeasure1\tdescription one\n"
       "testInstrument1\tmeasure2\tdescription two"  # noqa: COM812
    )

    pathlib.Path(tmp_path, "i2_descriptions.tsv").write_text(
      "instrumentName\tmeasureName\tdescription\n"
      "testInstrument2\tmeasure1\tdescription three"  # noqa: COM812
    )

    config = MeasureDescriptionsConfig.model_validate({
        "files": [
            {"path": "i1_descriptions.tsv"},
            {"path": "i2_descriptions.tsv"},
        ],
    })

    assert load_descriptions(str(tmp_path), config) == {
        "testInstrument1.measure1": "description one",
        "testInstrument1.measure2": "description two",
        "testInstrument2.measure1": "description three",
    }


def test_load_descriptions_dictionary() -> None:
    config = MeasureDescriptionsConfig.model_validate({
        "dictionary": {
            "testInstrument1": {
                "measure1": "description one",
                "measure2": "description two",
            },
            "testInstrument2": {
                "measure1": "description three",
            },
        },
    })

    assert load_descriptions("N/A", config) == {
        "testInstrument1.measure1": "description one",
        "testInstrument1.measure2": "description two",
        "testInstrument2.measure1": "description three",
    }


def test_load_descriptions_mixed(tmp_path: pathlib.Path) -> None:
    pathlib.Path(tmp_path, "descriptions.tsv").write_text(
        "instrumentName\tmeasureName\tdescription\n"
        "testInstrument1\tmeasure1\tdescription one\n"
        "testInstrument1\tmeasure2\tdescription two\n"
        "testInstrument2\tmeasure1\tdescription three"  # noqa: COM812
    )

    pathlib.Path(tmp_path, "i2_descriptions.tsv").write_text(
      "instrumentName\tmeasureName\tdescription\n"
      "testInstrument2\tmeasure2\tdescription four"  # noqa: COM812
    )

    config = MeasureDescriptionsConfig.model_validate({
        "files": [
            {"path": "descriptions.tsv"},
            {"path": "i2_descriptions.tsv"},
        ],
        "dictionary": {
            "testInstrument1": {
                "measure1": "description one updated",
            },
        },
    })

    assert load_descriptions(str(tmp_path), config) == {
        "testInstrument1.measure1": "description one updated",
        "testInstrument1.measure2": "description two",
        "testInstrument2.measure1": "description three",
        "testInstrument2.measure2": "description four",
    }


def test_load_descriptions_file_with_overrides(tmp_path: pathlib.Path) -> None:
    pathlib.Path(tmp_path, "descriptions.tsv").write_text(
        "instrumentName,m_name,m_desc\n"
        "testInstrument1,measure1,description one\n"
        "testInstrument1,measure2,description two\n"
        "testInstrument2,measure1,description three"  # noqa: COM812
    )

    config = MeasureDescriptionsConfig.model_validate({
        "files": [
            {
                "path": "descriptions.tsv",
                "delimiter": ",",
                "instrument": "theSpecialInstrument",
                "measure_column": "m_name",
                "description_column": "m_desc",
            },
        ],
    })

    assert load_descriptions(str(tmp_path), config) == {
        "theSpecialInstrument.measure1": "description three",
        "theSpecialInstrument.measure2": "description two",
    }

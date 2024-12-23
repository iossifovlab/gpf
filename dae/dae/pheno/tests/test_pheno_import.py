# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from pathlib import Path

import pytest

from dae.genomic_resources.testing import (
    setup_directories,
)
from dae.pheno.pheno_data import PhenotypeStudy
from dae.pheno.pheno_import import collect_instruments, main
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
    })
    instruments = collect_instruments(
        str(tmp_path),
        ["instrument_1.csv", "subdir_1", "subdir_2/**/*.txt"],
    )
    assert instruments == {
        "instrument_1": [pathlib.Path(
            tmp_path, "instrument_1.csv")],
        "instrument_2": [pathlib.Path(
            tmp_path, "subdir_1", "instrument_2.txt")],
        "instrument_3": [pathlib.Path(
            tmp_path, "subdir_2", "subsubdir", "instrument_3.txt")],
    }

# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import shutil

import duckdb

from gpf.pheno.pheno_data import PhenotypeStudy


def test_close_releases_the_pheno_db_file(
    tmp_path: pathlib.Path,
    fake_pheno_db_dir: pathlib.Path,
) -> None:
    dbfile = tmp_path / "fake.db"
    shutil.copy(fake_pheno_db_dir / "fake" / "fake.db", dbfile)
    study = PhenotypeStudy("fake", str(dbfile))

    study.close()

    with duckdb.connect(dbfile, read_only=False) as conn:
        assert conn.execute("SELECT 1").fetchone() == (1,)

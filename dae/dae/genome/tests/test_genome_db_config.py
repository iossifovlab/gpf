import os
from dae.genome.genomes_db import GenomesDB


def test_genomes_db_config_load(fixture_dirname, mocker):

    config_filename = fixture_dirname("genomesDB.conf")
    assert os.path.exists(config_filename), config_filename
    print(config_filename)

    mocker.patch("os.path.exists", return_value=True)

    genomes_db = GenomesDB(os.path.dirname(config_filename), config_filename)

    assert genomes_db is not None

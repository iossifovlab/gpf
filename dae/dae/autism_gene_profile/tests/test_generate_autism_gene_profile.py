# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from pytest_mock import MockerFixture

from dae.autism_gene_profile.generate_autism_gene_profile import main
from dae.autism_gene_profile.db import AutismGeneProfileDB
from dae.gpf_instance import GPFInstance


def test_generate_autism_gene_profile(
        agp_gpf_instance: GPFInstance,
        tmp_path: pathlib.Path, mocker: MockerFixture) -> None:
    agpdb_filename = str(tmp_path / "agpdb")
    argv = [
        "--dbfile",
        agpdb_filename,
        "-vv",
        "--genes",
        "PCDHA4",
    ]

    main(agp_gpf_instance, argv)
    agpdb = AutismGeneProfileDB(
        agp_gpf_instance._autism_gene_profile_config,
        agpdb_filename,
        clear=False
    )
    agp = agpdb.get_agp("PCDHA4")
    assert agp is not None

    counts = agp.variant_counts["iossifov_we2014_test"]
    assert counts is not None

    unknown = counts["unknown"]
    assert unknown["denovo_noncoding"] == {
        "count": 1,
        "rate": 90.9090909090909
    }
    assert unknown["denovo_missense"] == {
        "count": 0,
        "rate": 0.0
    }

    counts = agp.variant_counts["iossifov_we2014_test"]
    assert counts is not None

    unaffected = counts["unaffected"]
    assert unaffected["denovo_noncoding"] == {
        "count": 0,
        "rate": 0.0
    }
    assert unaffected["denovo_missense"] == {
        "count": 0,
        "rate": 0.0
    }

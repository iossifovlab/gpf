# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.tools.generate_autism_gene_profile import main
from dae.autism_gene_profile.db import AutismGeneProfileDB


def test_generate_autism_gene_profile(
        agp_gpf_instance, temp_dbfile):
    argv = [
        "--dbfile",
        temp_dbfile,
        "-vv",
        "--genes",
        "PCDHA4",
    ]

    main(agp_gpf_instance, argv)
    agpdb = AutismGeneProfileDB(
        agp_gpf_instance._autism_gene_profile_config,
        temp_dbfile,
        clear=False
    )
    agp = agpdb.get_agp("PCDHA4")

    unknown = agp.variant_counts["iossifov_we2014_test"]["unknown"]
    assert unknown["denovo_noncoding"] == {
        "count": 1,
        "rate": 90.9090909090909
    }
    assert unknown["denovo_missense"] == {
        "count": 0,
        "rate": 0.0
    }

    unaffected = agp.variant_counts["iossifov_we2014_test"]["unaffected"]
    assert unaffected["denovo_noncoding"] == {
        "count": 0,
        "rate": 0.0
    }
    assert unaffected["denovo_missense"] == {
        "count": 0,
        "rate": 0.0
    }

from dae.tools.generate_autism_gene_profile import main
from dae.autism_gene_profile.db import AutismGeneProfileDB


def test_generate_autism_gene_profile(
        agp_gpf_instance, temp_dbfile):
    argv = [
        "--dbfile",
        temp_dbfile,
        "-vv"
    ]
    import time

    main(agp_gpf_instance, argv)
    agpdb = AutismGeneProfileDB(
        agp_gpf_instance._autism_gene_profile_config,
        temp_dbfile,
        clear=False
    )
    agp = agpdb.get_agp("PCDHA4")

    unknown = agp.variant_counts["iossifov_we2014_test"]["unknown"]
    assert unknown["noncoding"] == 1
    assert unknown["missense"] == 0

    unaffected = agp.variant_counts["iossifov_we2014_test"]["unaffected"]
    assert unaffected["noncoding"] == 0
    assert unaffected["missense"] == 0

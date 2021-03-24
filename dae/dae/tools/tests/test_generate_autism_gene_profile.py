from dae.tools.generate_autism_gene_profile import main
from dae.autism_gene_profile.db import AutismGeneProfileDB


def test_generate_autism_gene_profile(
        agp_gpf_instance, temp_dbfile, calc_gene_sets):
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
    agp = agpdb.get_agp("C2orf42")

    unknown = agp.variant_counts["iossifov_we2014_test"]["unknown"]
    assert unknown["synonymous"] == 0
    assert unknown["missense"] == 2

    unaffected = agp.variant_counts["iossifov_we2014_test"]["unaffected"]
    assert unaffected["synonymous"] == 0
    assert unaffected["missense"] == 0

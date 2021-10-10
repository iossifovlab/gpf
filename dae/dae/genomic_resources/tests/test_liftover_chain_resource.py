def test_liftover_chain_resource(genomic_resource_fixture_dir_repo):
    chain_resource = genomic_resource_fixture_dir_repo.get_resource(
        "hg38/hg38tohg19")
    assert chain_resource
    chain_resource.open()

    def check_coordinate(pos, expected_chrom, expected_pos, expected_strand):
        out = chain_resource.convert_coordinate("chr1", pos)
        assert out[0] == expected_chrom
        assert out[1] == expected_pos
        assert out[2] == expected_strand
    check_coordinate(100_000, "chr1", 99_999, "+")
    check_coordinate(180_000, "chr16", 90_188_902, "-")
    check_coordinate(190_000, "chr2", 114_351_526, "-")
    check_coordinate(260_000, "chr1", 229_750, "+")

def test_liftover_chain_resource(anno_grdb):
    chain_resource = anno_grdb.get_resource("hg38/hg38tohg19")
    chain_resource.open()

    def check_coordinate(pos, expected_chrom, expected_pos, expected_strand):
        out = chain_resource.convert_coordinate("chr1", pos)
        assert out[0] == expected_chrom
        assert out[1] == expected_pos
        assert out[2] == expected_strand
    check_coordinate(100_000, "1", 99_999, "+")
    check_coordinate(180_000, "16", 90_188_902, "-")
    check_coordinate(190_000, "2", 114_351_526, "-")
    check_coordinate(260_000, "1", 229_750, "+")

import os

from dae.genome.genome_access import GenomicSequence


def test_genomic_sequence_resource(test_grdb):

    res = test_grdb.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/genome")
    assert res is not None
    res.open()

    print(res.get_all_chrom_lengths())
    assert len(res.get_all_chrom_lengths()) == 3

    assert res.get_chrom_length("X") == 300_000
    assert res.get_chrom_length("alabala") is None

    assert len(res.chromosomes) == 3
    assert tuple(res.chromosomes) == ("1", "2", "X")

    seq = res.get_sequence("1", 12001, 12050)
    assert seq == "CATCTGCAGGTGTCTGACTTCCAGCAACTGCTGGCCTGTGCCAGGGTGCA"

    seq = res.get_sequence("2", 12001, 12050)
    assert seq == "CTGAAACGGAGCTATTAGTGGGGAGAGCTGATGTCCCAGTTCTTGTTTAA"

    seq = res.get_sequence("X", 150001, 150050)
    assert seq == "ACCCTGACAGCCTCGTTCTAATACTATGAGGCCAAATACACTCACGTTCT"

    res.close()


def test_genomic_sequence_resource_http(test_http_grdb, resources_http_server):

    res = test_http_grdb.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/genome")
    assert res is not None
    res.open()

    print(res.get_all_chrom_lengths())
    assert len(res.get_all_chrom_lengths()) == 3

    assert res.get_chrom_length("X") == 300_000
    assert res.get_chrom_length("alabala") is None

    assert len(res.chromosomes) == 3
    assert tuple(res.chromosomes) == ("1", "2", "X")

    seq = res.get_sequence("1", 12001, 12050)
    assert seq == "CATCTGCAGGTGTCTGACTTCCAGCAACTGCTGGCCTGTGCCAGGGTGCA"

    seq = res.get_sequence("2", 12001, 12050)
    assert seq == "CTGAAACGGAGCTATTAGTGGGGAGAGCTGATGTCCCAGTTCTTGTTTAA"

    seq = res.get_sequence("X", 150001, 150050)
    assert seq == "ACCCTGACAGCCTCGTTCTAATACTATGAGGCCAAATACACTCACGTTCT"


def test_filesystem_genomic_sequence(fixture_dirname):
    genome = GenomicSequence.load_genome(
        os.path.join(
            fixture_dirname("genomic_resources"),
            "hg19/GATK_ResourceBundle_5777_b37_phiX174/genome/chrAll.fa"))

    assert genome is not None

    print(genome.get_all_chrom_lengths())
    assert len(genome.get_all_chrom_lengths()) == 3

    assert genome.get_chrom_length("X") == 300_000
    assert genome.get_chrom_length("alabala") is None

    assert len(genome.chromosomes) == 3
    assert tuple(genome.chromosomes) == ("1", "2", "X")

    seq = genome.get_sequence("1", 12001, 12050)
    assert seq == "CATCTGCAGGTGTCTGACTTCCAGCAACTGCTGGCCTGTGCCAGGGTGCA"

    seq = genome.get_sequence("2", 12001, 12050)
    assert seq == "CTGAAACGGAGCTATTAGTGGGGAGAGCTGATGTCCCAGTTCTTGTTTAA"

    seq = genome.get_sequence("X", 150001, 150050)
    assert seq == "ACCCTGACAGCCTCGTTCTAATACTATGAGGCCAAATACACTCACGTTCT"

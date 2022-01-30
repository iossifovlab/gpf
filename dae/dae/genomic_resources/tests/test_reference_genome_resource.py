import os
import pytest

from dae.genomic_resources.test_tools import convert_to_tab_separated
from dae.genomic_resources.test_tools import build_a_test_resource
from dae.genomic_resources.reference_genome import \
    open_reference_genome_from_file
from dae.genomic_resources.reference_genome import \
    open_reference_genome_from_resource


def test_basic_sequence_resoruce():
    res = build_a_test_resource({
        "genomic_resource.yaml": "{type: genome, filename: chr.fa}",
        "chr.fa": convert_to_tab_separated('''
                >pesho
                NNACCCAAAC
                GGGCCTTCCN
                NNNA
        '''),
        "chr.fa.fai": "pesho\t24\t7\t10\t11\n"
    })
    ref = open_reference_genome_from_resource(res)
    assert ref.get_chrom_length("pesho") == 24
    assert ref.get_sequence("pesho", 1, 12) == "NNACCCAAACGG"


@pytest.mark.fixture_repo
def test_genomic_sequence_resource(genomic_resource_fixture_dir_repo):

    res = genomic_resource_fixture_dir_repo.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome")
    assert res is not None
    ref = open_reference_genome_from_resource(res)

    print(ref.get_all_chrom_lengths())
    assert len(ref.get_all_chrom_lengths()) == 3

    assert ref.get_chrom_length("X") == 300_000
    assert ref.get_chrom_length("alabala") is None

    assert len(ref.chromosomes) == 3
    assert tuple(ref.chromosomes) == ("1", "2", "X")

    seq = ref.get_sequence("1", 12001, 12050)
    assert seq == "CATCTGCAGGTGTCTGACTTCCAGCAACTGCTGGCCTGTGCCAGGGTGCA"

    seq = ref.get_sequence("2", 12001, 12050)
    assert seq == "CTGAAACGGAGCTATTAGTGGGGAGAGCTGATGTCCCAGTTCTTGTTTAA"

    seq = ref.get_sequence("X", 150001, 150050)
    assert seq == "ACCCTGACAGCCTCGTTCTAATACTATGAGGCCAAATACACTCACGTTCT"

    ref.close()


@pytest.mark.fixture_repo
def test_genomic_sequence_resource_http(genomic_resource_fixture_http_repo):

    res = genomic_resource_fixture_http_repo.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome")
    assert res is not None
    ref = open_reference_genome_from_resource(res)

    print(ref.get_all_chrom_lengths())
    assert len(ref.get_all_chrom_lengths()) == 3

    assert ref.get_chrom_length("X") == 300_000
    assert ref.get_chrom_length("alabala") is None

    assert len(ref.chromosomes) == 3
    assert tuple(ref.chromosomes) == ("1", "2", "X")

    seq = ref.get_sequence("1", 12001, 12050)
    assert seq == "CATCTGCAGGTGTCTGACTTCCAGCAACTGCTGGCCTGTGCCAGGGTGCA"

    seq = ref.get_sequence("2", 12001, 12050)
    assert seq == "CTGAAACGGAGCTATTAGTGGGGAGAGCTGATGTCCCAGTTCTTGTTTAA"

    seq = ref.get_sequence("X", 150001, 150050)
    assert seq == "ACCCTGACAGCCTCGTTCTAATACTATGAGGCCAAATACACTCACGTTCT"


@pytest.mark.fixture_repo
def test_filesystem_genomic_sequence(fixture_dirname):
    genome = open_reference_genome_from_file(
        os.path.join(
            fixture_dirname("genomic_resources"),
            "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/"
            "genome/chrAll.fa"))

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

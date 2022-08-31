# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os

import pytest

from dae.genomic_resources.testing import convert_to_tab_separated
from dae.genomic_resources.testing import build_test_resource
from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol, \
    build_local_resource
from dae.genomic_resources.repository import GenomicResourceProtocolRepo

from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_file
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource


def test_basic_sequence_resoruce():
    res = build_test_resource(
        content={
            "genomic_resource.yaml": "{type: genome, filename: chr.fa}",
            "chr.fa": convert_to_tab_separated("""
                    >pesho
                    NNACCCAAAC
                    GGGCCTTCCN
                    NNNA
            """),
            "chr.fa.fai": "pesho\t24\t7\t10\t11\n"
        })
    ref = build_reference_genome_from_resource(res)
    ref.open()
    assert ref.get_chrom_length("pesho") == 24
    assert ref.get_sequence("pesho", 1, 12) == "NNACCCAAACGG"


def test_genomic_sequence_resource(fixture_dirname):

    dirname = fixture_dirname("genomic_resources")
    proto = build_fsspec_protocol("d", dirname)
    repo = GenomicResourceProtocolRepo(proto)

    res = repo.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome")

    ref = build_reference_genome_from_resource(res)
    ref.open()

    print(ref.get_all_chrom_lengths())
    assert len(ref.get_all_chrom_lengths()) == 3

    assert ref.get_chrom_length("X") == 300_000
    with pytest.raises(ValueError):
        ref.get_chrom_length("alabala")

    assert len(ref.chromosomes) == 3
    assert tuple(ref.chromosomes) == ("1", "2", "X")

    seq = ref.get_sequence("1", 12001, 12050)
    assert seq == "CATCTGCAGGTGTCTGACTTCCAGCAACTGCTGGCCTGTGCCAGGGTGCA"

    seq = ref.get_sequence("2", 12001, 12050)
    assert seq == "CTGAAACGGAGCTATTAGTGGGGAGAGCTGATGTCCCAGTTCTTGTTTAA"

    seq = ref.get_sequence("X", 150001, 150050)
    assert seq == "ACCCTGACAGCCTCGTTCTAATACTATGAGGCCAAATACACTCACGTTCT"

    ref.close()


def test_genomic_sequence_resource_http(fixture_dirname, proto_builder):

    dirname = fixture_dirname("genomic_resources")
    src_proto = build_fsspec_protocol("d", dirname)

    proto = proto_builder(
        src_proto,
        scheme="http",
        proto_id="testing_http")
    repo = GenomicResourceProtocolRepo(proto)

    res = repo.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome")

    ref = build_reference_genome_from_resource(res)
    ref.open()

    print(ref.get_all_chrom_lengths())
    assert len(ref.get_all_chrom_lengths()) == 3

    assert ref.get_chrom_length("X") == 300_000
    with pytest.raises(ValueError):
        ref.get_chrom_length("alabala")

    assert len(ref.chromosomes) == 3
    assert tuple(ref.chromosomes) == ("1", "2", "X")

    seq = ref.get_sequence("1", 12001, 12050)
    assert seq == "CATCTGCAGGTGTCTGACTTCCAGCAACTGCTGGCCTGTGCCAGGGTGCA"

    seq = ref.get_sequence("2", 12001, 12050)
    assert seq == "CTGAAACGGAGCTATTAGTGGGGAGAGCTGATGTCCCAGTTCTTGTTTAA"

    seq = ref.get_sequence("X", 150001, 150050)
    assert seq == "ACCCTGACAGCCTCGTTCTAATACTATGAGGCCAAATACACTCACGTTCT"


def test_filesystem_genomic_sequence(fixture_dirname):
    genome = build_reference_genome_from_file(
        os.path.join(
            fixture_dirname("genomic_resources"),
            "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/"
            "genome/chrAll.fa"))

    assert genome is not None
    genome.open()

    print(genome.get_all_chrom_lengths())
    assert len(genome.get_all_chrom_lengths()) == 3

    assert genome.get_chrom_length("X") == 300_000
    with pytest.raises(ValueError):
        genome.get_chrom_length("alabala")

    assert len(genome.chromosomes) == 3
    assert tuple(genome.chromosomes) == ("1", "2", "X")

    seq = genome.get_sequence("1", 12001, 12050)
    assert seq == "CATCTGCAGGTGTCTGACTTCCAGCAACTGCTGGCCTGTGCCAGGGTGCA"

    seq = genome.get_sequence("2", 12001, 12050)
    assert seq == "CTGAAACGGAGCTATTAGTGGGGAGAGCTGATGTCCCAGTTCTTGTTTAA"

    seq = genome.get_sequence("X", 150001, 150050)
    assert seq == "ACCCTGACAGCCTCGTTCTAATACTATGAGGCCAAATACACTCACGTTCT"


def test_local_genomic_sequence(fixture_dirname):

    dirname = fixture_dirname(
        "genomic_resources/hg19/"
        "GATK_ResourceBundle_5777_b37_phiX174_short/genome")

    res = build_local_resource(dirname, {
        "type": "genome",
        "filename": "chrAll.fa"
    })
    assert res is not None

    ref = build_reference_genome_from_resource(res)
    ref.open()

    print(ref.get_all_chrom_lengths())
    assert len(ref.get_all_chrom_lengths()) == 3

    assert ref.get_chrom_length("X") == 300_000

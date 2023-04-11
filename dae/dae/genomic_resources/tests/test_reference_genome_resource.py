# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import textwrap
import pytest

from dae.genomic_resources.testing import setup_directories, \
    setup_genome, build_filesystem_test_resource, \
    build_http_test_protocol
from dae.genomic_resources.fsspec_protocol import build_local_resource

from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_file, ReferenceGenome
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource


@pytest.fixture
def genome_fixture(tmp_path):
    root_path = tmp_path / "genome"
    setup_directories(root_path, {
        "genomic_resource.yaml": "{type: genome, filename: chr.fa}",
    })
    setup_genome(root_path / "chr.fa", textwrap.dedent("""
            >pesho
            NNACCCAAAC
            GGGCCTTCCN
            NNNA
            >gosho
            NNAACCGGTT
            TTGGCCAANN
    """))
    return root_path


def test_basic_sequence_resource_file(genome_fixture):
    res = build_filesystem_test_resource(genome_fixture)
    reference_genome = build_reference_genome_from_resource(res)
    with reference_genome.open() as ref:
        assert len(ref.get_all_chrom_lengths()) == 2

        assert ref.get_chrom_length("pesho") == 24
        assert ref.get_sequence("pesho", 1, 12) == "NNACCCAAACGG"

        assert ref.get_chrom_length("gosho") == 20
        assert ref.get_sequence("gosho", 11, 20) == "TTGGCCAANN"


def test_basic_sequence_resource_http(genome_fixture):
    with build_http_test_protocol(genome_fixture) as proto:
        res = proto.get_resource("")
        reference_genome = build_reference_genome_from_resource(res)
        with reference_genome.open() as ref:
            assert len(ref.get_all_chrom_lengths()) == 2

            assert ref.get_chrom_length("pesho") == 24
            assert ref.get_sequence("pesho", 1, 12) == "NNACCCAAACGG"

            assert ref.get_chrom_length("gosho") == 20
            assert ref.get_sequence("gosho", 11, 20) == "TTGGCCAANN"


def test_filesystem_genomic_sequence(genome_fixture):
    reference_genome = build_reference_genome_from_file(
        str(genome_fixture / "chr.fa"))

    assert reference_genome is not None
    with reference_genome.open() as ref:
        assert len(ref.get_all_chrom_lengths()) == 2

        assert ref.get_chrom_length("pesho") == 24
        assert ref.get_sequence("pesho", 1, 12) == "NNACCCAAACGG"

        assert ref.get_chrom_length("gosho") == 20
        assert ref.get_sequence("gosho", 11, 20) == "TTGGCCAANN"


def test_local_genomic_sequence(genome_fixture):

    res = build_local_resource(str(genome_fixture), {
        "type": "genome",
        "filename": "chr.fa"
    })
    assert res is not None

    reference_genome = build_reference_genome_from_resource(res)
    with reference_genome.open() as ref:
        assert len(ref.get_all_chrom_lengths()) == 2

        assert ref.get_chrom_length("pesho") == 24
        assert ref.get_sequence("pesho", 1, 12) == "NNACCCAAACGG"

        assert ref.get_chrom_length("gosho") == 20
        assert ref.get_sequence("gosho", 11, 20) == "TTGGCCAANN"


def test_chromosome_statistic_basic(genome_fixture):
    res = build_filesystem_test_resource(genome_fixture)
    stat = ReferenceGenome._do_chrom_statistic(res, "pesho", 1, None)

    assert stat.length == 24

    assert stat.nucleotide_counts["A"] == 5
    assert stat.nucleotide_counts["C"] == 8
    assert stat.nucleotide_counts["G"] == 3
    assert stat.nucleotide_counts["T"] == 2
    assert stat.nucleotide_counts["N"] == 6
    total_nucleotides = stat.length

    assert stat.nucleotide_pair_counts["AA"] == 2
    assert stat.nucleotide_pair_counts["AG"] == 0
    assert stat.nucleotide_pair_counts["AC"] == 2
    assert stat.nucleotide_pair_counts["AT"] == 0
    assert stat.nucleotide_pair_counts["GA"] == 0
    assert stat.nucleotide_pair_counts["GG"] == 2
    assert stat.nucleotide_pair_counts["GC"] == 1
    assert stat.nucleotide_pair_counts["GT"] == 0
    assert stat.nucleotide_pair_counts["CA"] == 1
    assert stat.nucleotide_pair_counts["CG"] == 1
    assert stat.nucleotide_pair_counts["CC"] == 4
    assert stat.nucleotide_pair_counts["CT"] == 1
    assert stat.nucleotide_pair_counts["TA"] == 0
    assert stat.nucleotide_pair_counts["TG"] == 0
    assert stat.nucleotide_pair_counts["TC"] == 1
    assert stat.nucleotide_pair_counts["TT"] == 1
    total_pairs = sum(stat.nucleotide_pair_counts.values())

    for pair, count in stat.nucleotide_pair_counts.items():
        assert stat.bi_nucleotide_distribution[pair] == \
            pytest.approx(count / total_pairs * 100)

    for nuc, count in stat.nucleotide_counts.items():
        assert stat.nucleotide_distribution[nuc] == \
            pytest.approx(count / total_nucleotides * 100)

    stat.finish()

    print(stat.serialize())
    print(stat.bi_nucleotide_distribution)
    print(stat.nucleotide_distribution)

    ReferenceGenome._save_chrom_statistic(res, "pesho", stat)

    assert os.path.exists(os.path.join(
        genome_fixture,
        "statistics",
        "pesho_statistic.yaml"
    ))


def test_reference_genome_fetch(genome_fixture):
    res = build_filesystem_test_resource(genome_fixture)
    reference_genome = build_reference_genome_from_resource(res)

    with reference_genome.open():
        result = list(reference_genome.fetch("pesho", 1, 10))

        assert result == [
            "N",
            "N",
            "A",
            "C",
            "C",
            "C",
            "A",
            "A",
            "A",
            "C"
        ]

        result = list(reference_genome.fetch("pesho", 18, 36))

        assert result == [
            "C",
            "C",
            "N",
            "N",
            "N",
            "N",
            "A"
        ]

        result = list(reference_genome.fetch("pesho", 1, None))

        assert result == [
            "N",
            "N",
            "A",
            "C",
            "C",
            "C",
            "A",
            "A",
            "A",
            "C",
            "G",
            "G",
            "G",
            "C",
            "C",
            "T",
            "T",
            "C",
            "C",
            "N",
            "N",
            "N",
            "N",
            "A"
        ]


def test_reference_genome_pair_iter(genome_fixture):
    res = build_filesystem_test_resource(genome_fixture)
    reference_genome = build_reference_genome_from_resource(res)

    with reference_genome.open():
        result = list(reference_genome.pair_iter("pesho", 1, 10))

        assert result == [
            (None, "N"),
            ("N", "N"),
            ("N", "A"),
            ("A", "C"),
            ("C", "C"),
            ("C", "C"),
            ("C", "A"),
            ("A", "A"),
            ("A", "A"),
            ("A", "C")
        ]
        result = list(reference_genome.pair_iter("pesho", 2, 10))

        print(result)
        assert result == [
            ("N", "N"),
            ("N", "A"),
            ("A", "C"),
            ("C", "C"),
            ("C", "C"),
            ("C", "A"),
            ("A", "A"),
            ("A", "A"),
            ("A", "C")
        ]

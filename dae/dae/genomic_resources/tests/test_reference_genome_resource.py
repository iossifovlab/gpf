# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
import pytest

from dae.genomic_resources.testing import setup_directories, \
    setup_genome, build_filesystem_test_resource, \
    build_http_test_protocol
from dae.genomic_resources.fsspec_protocol import build_local_resource

from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_file
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


def test_basic_sequence_resoruce_file(genome_fixture):
    res = build_filesystem_test_resource(genome_fixture)
    reference_genome = build_reference_genome_from_resource(res)
    with reference_genome.open() as ref:
        assert len(ref.get_all_chrom_lengths()) == 2

        assert ref.get_chrom_length("pesho") == 24
        assert ref.get_sequence("pesho", 1, 12) == "NNACCCAAACGG"

        assert ref.get_chrom_length("gosho") == 20
        assert ref.get_sequence("gosho", 11, 20) == "TTGGCCAANN"


def test_basic_sequence_resoruce_http(genome_fixture):
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

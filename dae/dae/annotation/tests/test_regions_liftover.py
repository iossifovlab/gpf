# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import textwrap
import pytest

from dae.genomic_resources.testing import \
    setup_directories, convert_to_tab_separated, setup_genome, \
    build_filesystem_test_repository, setup_gzip

from dae.genomic_resources.liftover_resource import \
    build_liftover_chain_from_resource


@pytest.fixture
def fixture_repo(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("regions_effect_annotation")
    setup_directories(root_path, {
        "genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "target_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "liftover_chain": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: liftover_chain

                filename: liftover.chain.gz
            """),
        }
    })
    setup_genome(
        root_path / "genome" / "genome.fa",
        textwrap.dedent(f"""
            >chr1
            {25 * 'AGCT'}
            >chr2
            {25 * 'AGCT'}
            """)
    )
    setup_genome(
        root_path / "target_genome" / "genome.fa",
        textwrap.dedent(f"""
            >1
            NNNN{25 * 'AGCT'}
            >2
            NNNN{25 * 'AGCT'}
            """)
    )
    setup_gzip(
        root_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain||4900||1||100||+||4||104||chr1||100||+||1||101||1
        100 0 0
        0
        """)
    )
    return build_filesystem_test_repository(root_path)


def test_liftover_chain_fixture(fixture_repo):
    res = fixture_repo.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)

    assert liftover_chain is not None
    liftover_chain.open()

    lo_coordinates = liftover_chain.convert_coordinate("1", 14)
    chrom, pos, strand, _ = lo_coordinates
    assert chrom == "chr1"
    assert pos == 10
    assert strand == "+"

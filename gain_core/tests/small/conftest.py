# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest
from gain.genomic_resources.gene_models.gene_models import (
    GeneModels,
)
from gain.genomic_resources.gene_models.gene_models_factory import (
    build_gene_models_from_resource_id,
)
from gain.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource_id,
)
from gain.genomic_resources.repository import (
    GenomicResourceRepo,
)
from gain.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from gain.genomic_resources.testing import (
    build_filesystem_test_repository,
    convert_to_tab_separated,
    setup_directories,
    setup_genome,
    setup_gzip,
)
from gain.testing.t4c8_import import setup_t4c8_grr, t4c8_genes, t4c8_genome


@pytest.fixture(scope="module")
def liftover_grr_fixture(
        tmp_path_factory: pytest.TempPathFactory) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("liftover_grr_fixture")
    setup_directories(root_path, {
        "target_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "source_genome": {
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
        },
    })
    setup_gzip(
        root_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain 4900 foo 104 + 4 104 chrFoo 100 + 0 96 1
        48 4 0
        48 0 0
        0

        chain 4800 bar 112 + 4 108 chrBar 100 + 0 96 2
        48 8 0
        48 0 0
        0

        chain 4700 baz 108 + 4 104 chrBaz 100 - 4 100 3
        48 4 0
        48 0 0
        0
        """),
    )
    setup_genome(
        root_path / "target_genome" / "genome.fa",
        textwrap.dedent(f"""
            >chrFoo
            {25 * 'ACGT'}
            >chrBar
            {25 * 'ACGT'}
            >chrBaz
            {25 * 'ACGT'}
            """),
    )
    setup_genome(
        root_path / "source_genome" / "genome.fa",
        textwrap.dedent(f"""
            >foo
            NNNN{12 * 'ACGT'}NNNN{12 * 'ACGT'}
            >bar
            NNNN{12 * 'ACGT'}NNNNNNNN{12 * 'ACGT'}NNNN
            >baz
            NNNN{12 * 'TGCA'}NNNN{12 * 'TGCA'}NNNN
            """),
    )

    return build_filesystem_test_repository(root_path)


@pytest.fixture(scope="module")
def liftover_grr_fixture_reverse_strand(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("liftover_grr_fixture_2")
    setup_directories(root_path, {
        "target_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "source_genome": {
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
        },
    })
    setup_gzip(
        root_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain 1000 foo 125 + 0 125 chrFoo 125 - 0 125 1
        125
        """),
    )
    setup_genome(
        root_path / "target_genome" / "genome.fa",
        textwrap.dedent(f"""
          >chrFoo
          {25 * 'AAAAA'}
        """),
    )
    setup_genome(
        root_path / "source_genome" / "genome.fa",
        textwrap.dedent(f"""
          >foo
          {25 * 'TTTT'}
        """),
    )
    return build_filesystem_test_repository(root_path)


@pytest.fixture(scope="session")
def acgt_genome_38(
    tmp_path_factory: pytest.TempPathFactory,
) -> ReferenceGenome:
    root_path = tmp_path_factory.mktemp("acgt_genome")
    return setup_genome(
        root_path / "allChr.fa",
        f"""
        >chr1
        {25 * "ACGT"}
        >chr2
        {25 * "ACGT"}
        >chr3
        {25 * "ACGT"}
        """,
    )


@pytest.fixture(scope="session")
def acgt_genome_19(
    tmp_path_factory: pytest.TempPathFactory,
) -> ReferenceGenome:
    root_path = tmp_path_factory.mktemp("acgt_genome_19")
    return setup_genome(
        root_path / "allChr.fa",
        f"""
        >1
        {25 * "ACGT"}
        >2
        {25 * "ACGT"}
        >3
        {25 * "ACGT"}
        """,
    )


@pytest.fixture(scope="session")
def t4c8_grr(tmp_path_factory: pytest.TempPathFactory) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("t4c8_grr")
    setup_t4c8_grr(root_path)
    root_path2 = root_path / "2"
    t4c8_genome(root_path2)
    t4c8_genes(root_path2)

    setup_genome(root_path / "normalize_genome_1/all.fa", textwrap.dedent("""
        >1
        GGGGCATGGGG
    """))
    setup_genome(root_path / "normalize_genome_2/all.fa", textwrap.dedent("""
        >1
        GGGCACACACAGGG
    """))

    setup_genome(root_path / "tr_genome/all.fa", textwrap.dedent("""
        >1
        ATTTTTTTTTTTTTTTTTTTTTTTTTTT
    """))

    return build_genomic_resource_repository({
        "id": "t4c8_grr",
        "type": "directory",
        "directory": str(root_path),
    })


@pytest.fixture(scope="session")
def normalize_genome_1(t4c8_grr: GenomicResourceRepo) -> ReferenceGenome:
    return build_reference_genome_from_resource_id(
        "normalize_genome_1", t4c8_grr)


@pytest.fixture(scope="session")
def normalize_genome_2(t4c8_grr: GenomicResourceRepo) -> ReferenceGenome:
    return build_reference_genome_from_resource_id(
        "normalize_genome_2", t4c8_grr)


@pytest.fixture(scope="session")
def t4c8_reference_genome(
    t4c8_grr: GenomicResourceRepo,
) -> ReferenceGenome:
    return build_reference_genome_from_resource_id(
        "t4c8_genome", t4c8_grr)


@pytest.fixture(scope="session")
def t4c8_gene_models(
    t4c8_grr: GenomicResourceRepo,
) -> GeneModels:
    return build_gene_models_from_resource_id(
        "t4c8_genes", t4c8_grr)

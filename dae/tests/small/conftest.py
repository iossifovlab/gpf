# pylint: disable=W0621,C0114,C0116,W0212,W0613
import logging
import pathlib
import textwrap

import pytest
from dae.genomic_resources.gene_models.gene_models import (
    GeneModels,
)
from dae.genomic_resources.gene_models.gene_models_factory import (
    build_gene_models_from_resource_id,
)
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource_id,
)
from dae.genomic_resources.repository import (
    GenomicResourceRepo,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    convert_to_tab_separated,
    setup_directories,
    setup_genome,
    setup_gzip,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pheno.pheno_data import PhenotypeData
from dae.studies.study import GenotypeData
from dae.testing.t4c8_import import t4c8_genes, t4c8_genome
from dae.utils.testing import (
    _t4c8_study_1_ped,
    _t4c8_study_1_vcf,
    setup_t4c8_grr,
    setup_t4c8_instance,
)

logger = logging.getLogger(__name__)


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
    #
    # The initial header line starts with the keyword chain, followed
    # by 11 required attribute values, and ends with a blank line.
    #
    # The attributes include:
    #
    # score -- chain score
    # tName -- chromosome (reference/target sequence); source contig;
    # tSize -- chromosome size (reference/target sequence); full length of the
    #          source chromosome;
    # tStrand -- strand (reference/target sequence); must be +
    # tStart -- alignment start position (reference/target sequence);
    #           Start of source region
    # tEnd -- alignment end position (reference/target sequence);
    #         End of source region
    # qName -- chromosome (query sequence); target chromosome name;
    # qSize -- chromosome size (query sequence); Full length of the chromosome
    # qStrand -- strand (query sequence); + or -
    # qStart -- alignment start position (query sequence); target start;
    # qEnd -- alignment end position (query sequence); target end;
    # id -- chain ID
    #
    # Block format:
    # Alignment data lines contain three required attribute values:

    # size dt dq
    # size -- the size of the ungapped alignment
    # dt -- the difference between the end of this block and the beginning
    #       of the next block (reference/target sequence)
    # dq -- the difference between the end of this block and the beginning
    #       of the next block (query sequence)
    #
    # The last line of the alignment section contains only one number: the
    # ungapped alignment size of the last block.
    #
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
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_gpf_instance")
    return setup_t4c8_instance(root_path)


@pytest.fixture
def t4c8_study_1_ped(
    tmp_path: pathlib.Path,
) -> pathlib.Path:
    return _t4c8_study_1_ped(tmp_path)


@pytest.fixture
def t4c8_study_1_data(
    tmp_path: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path]:
    return _t4c8_study_1_ped(tmp_path), _t4c8_study_1_vcf(tmp_path)


@pytest.fixture(scope="session")
def t4c8_study_1(t4c8_instance: GPFInstance) -> GenotypeData:
    return t4c8_instance.get_genotype_data("t4c8_study_1")


@pytest.fixture(scope="session")
def t4c8_study_2(t4c8_instance: GPFInstance) -> GenotypeData:
    return t4c8_instance.get_genotype_data("t4c8_study_2")


@pytest.fixture(scope="session")
def t4c8_study_3(t4c8_instance: GPFInstance) -> GenotypeData:
    return t4c8_instance.get_genotype_data("t4c8_study_3")


@pytest.fixture(scope="session")
def t4c8_study_4(t4c8_instance: GPFInstance) -> GenotypeData:
    return t4c8_instance.get_genotype_data("t4c8_study_4")


@pytest.fixture(scope="session")
def t4c8_dataset(t4c8_instance: GPFInstance) -> GenotypeData:
    return t4c8_instance.get_genotype_data("t4c8_dataset")


@pytest.fixture(scope="session")
def t4c8_study_1_pheno(t4c8_instance: GPFInstance) -> PhenotypeData:
    return t4c8_instance.get_phenotype_data("study_1_pheno")


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

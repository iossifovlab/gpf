# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from typing import Callable

import pytest
import pytest_mock

from dae.genomic_resources.genomic_context import (
    GenomicContext,
    get_genomic_context,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    convert_to_tab_separated,
    setup_directories,
    setup_genome,
    setup_gzip,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.gpf_instance_plugin.gpf_instance_context_plugin import (
    init_test_gpf_instance_genomic_context_plugin,
)


@pytest.fixture()
def gpf_instance_genomic_context_fixture(
    mocker: pytest_mock.MockerFixture,
) -> Callable[[GPFInstance], GenomicContext]:

    def builder(gpf_instance: GPFInstance) -> GenomicContext:
        mocker.patch(
            "dae.genomic_resources.genomic_context."
            "_REGISTERED_CONTEXT_PROVIDERS",
            [])
        mocker.patch(
            "dae.genomic_resources.genomic_context._REGISTERED_CONTEXTS",
            [])

        init_test_gpf_instance_genomic_context_plugin(gpf_instance)
        context = get_genomic_context()
        assert context is not None

        return context

    return builder


@pytest.fixture()
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

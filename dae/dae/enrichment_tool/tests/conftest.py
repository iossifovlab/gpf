# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from collections.abc import Generator
from typing import cast

import pytest
from box import Box

from dae.enrichment_tool.build_coding_length_enrichment_background import (
    cli as build_coding_len_background_cli,
)
from dae.enrichment_tool.enrichment_builder import EnrichmentBuilder
from dae.enrichment_tool.enrichment_helper import EnrichmentHelper
from dae.enrichment_tool.enrichment_serializer import EnrichmentSerializer
from dae.enrichment_tool.gene_weights_background import (
    GeneScoreEnrichmentBackground,
)
from dae.enrichment_tool.samocha_background import SamochaEnrichmentBackground
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    build_inmemory_test_repository,
    convert_to_tab_separated,
    setup_directories,
)
from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing import setup_gpf_instance
from dae.testing.t4c8_import import t4c8_genes, t4c8_genome


@pytest.fixture(scope="session")
def gpf_fixture(
    fixtures_gpf_instance: GPFInstance,
    grr: GenomicResourceRepo,
) -> Generator[GPFInstance, None, None]:
    original_grr = fixtures_gpf_instance.grr
    fixtures_gpf_instance.grr = GenomicResourceGroupRepo(
        [grr, original_grr], "enrichment_testing_repo",
    )

    yield fixtures_gpf_instance

    fixtures_gpf_instance.grr = original_grr


@pytest.fixture(scope="session")
def f1_trio_enrichment_config(gpf_fixture: GPFInstance) -> Box:
    config = gpf_fixture.get_genotype_data_config("f1_trio")
    assert config is not None

    return cast(Box, config["enrichment"])


@pytest.fixture(scope="session")
def f1_trio(gpf_fixture: GPFInstance) -> GenotypeData:
    return gpf_fixture.get_genotype_data("f1_trio")


@pytest.fixture(scope="session")
def coding_len_background(
    grr: GenomicResourceRepo,
) -> GeneScoreEnrichmentBackground:
    res = grr.get_resource("enrichment/coding_len_testing")
    assert res.get_type() == "gene_score"

    background = GeneScoreEnrichmentBackground(res)
    assert background is not None
    assert background.name == "CodingLenBackground"

    background.load()
    return background


@pytest.fixture(scope="session")
def samocha_background(
    grr: GenomicResourceRepo,
) -> SamochaEnrichmentBackground:
    res = grr.get_resource("enrichment/samocha_testing")
    assert res.get_type() == "samocha_enrichment_background"

    background = SamochaEnrichmentBackground(res)
    assert background is not None
    assert background.name == "Samocha's enrichment background model"
    assert background.background_type == "samocha_enrichment_background"

    background.load()
    return background


@pytest.fixture(scope="session")
def grr() -> GenomicResourceRepo:
    return build_inmemory_test_repository({
        "enrichment": {
            "coding_len_testing_deprecated": {
                GR_CONF_FILE_NAME: """
                    type: gene_weights_enrichment_background
                    filename: data.mem
                    name: CodingLenBackground
                """,
                "data.mem": convert_to_tab_separated("""
                    gene     gene_weight
                    SAMD11   3
                    PLEKHN1  7
                    POGZ     13
                """),
            },
            "coding_len_testing": {
                GR_CONF_FILE_NAME: """
                    type: gene_score
                    filename: data.mem
                    separator: "\t"
                    scores:
                    - id: gene_weight
                      name: CodingLenBackground
                      desc: Gene coding length enrichment background model
                      histogram:
                        type: number
                        number_of_bins: 10
                        view_range:
                          min: 0
                          max: 20

                """,
                "data.mem": convert_to_tab_separated("""
                    gene     gene_weight
                    SAMD11   3
                    PLEKHN1  7
                    POGZ     13
                """),
            },
            "samocha_testing": {
                GR_CONF_FILE_NAME: """
                    type: samocha_enrichment_background
                    filename: data.mem
                """,
                "data.mem": convert_to_tab_separated("""
"transcript","gene","bp","all","synonymous","missense","nonsense","splice-site","frame-shift","F","M","P_LGDS","P_MISSENSE","P_SYNONYMOUS"
"NM_017582","SAMD11",3,-1,-5,-4,-6,-6,-6,2,2,1.1,1.4,5.7
"NM_017582","PLEKHN1",7,-2,-5,-4,-6,-6,-6,2,2,1.2,1.5,5.8
"NM_014372","POGZ",11,-3,-5,-5,-6,-7,-6,2,2,6.3,4.6,2.9
                """),
            },
        },
    })


@pytest.fixture()
def t4c8_fixture(tmp_path: pathlib.Path) -> GPFInstance:
    root_path = tmp_path

    t4c8_genes(root_path / "grr")
    t4c8_genome(root_path / "grr")
    setup_directories(root_path, {
        "grr_definition.yaml": textwrap.dedent(f"""
        id: t4c8_genes_testing
        type: dir
        directory: {root_path / "grr"}
        """),
    })

    coding_len_background_path = root_path / "grr" / "coding_len_background"
    coding_len_background_path.mkdir(parents=True, exist_ok=True)

    build_coding_len_background_cli([
        "--grr", str(root_path / "grr_definition.yaml"),
        "-o", str(coding_len_background_path / "coding_len_background.tsv"),
        "t4c8_genes",
    ])
    setup_directories(coding_len_background_path, {
        "genomic_resource.yaml": textwrap.dedent("""
        type: gene_score
        filename: coding_len_background.tsv
        separator: "\t"
        scores:
        - id: gene_weight
          name: t4c8CodingLenBackground
          desc: Gene coding length enrichment background model
          histogram:
            type: number
            number_of_bins: 10
            view_range:
              min: 0
              max: 20
        """),
    })

    grr = build_filesystem_test_repository(root_path / "grr")
    return setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="t4c8_genome",
        gene_models_id="t4c8_genes",
        grr=grr)


@pytest.fixture(scope="session")
def enrichment_helper(grr: GenomicResourceRepo) -> EnrichmentHelper:
    return EnrichmentHelper(grr)


@pytest.fixture(scope="session")
def enrichment_builder(
    f1_trio: GenotypeData,
    enrichment_helper: EnrichmentHelper,
) -> EnrichmentBuilder:
    return EnrichmentBuilder(enrichment_helper, f1_trio)


@pytest.fixture(scope="session")
def enrichment_serializer(
    f1_trio: GenotypeData,
    enrichment_helper: EnrichmentHelper,
    enrichment_builder: EnrichmentBuilder,
) -> EnrichmentSerializer:
    enrichment_config = enrichment_helper.get_enrichment_config(f1_trio)
    assert enrichment_config is not None

    build = enrichment_builder.build_results(
        gene_syms=["SAMD11", "PLEKHN1", "POGZ"],
        background_id="enrichment/coding_len_testing",
        counting_id="enrichment_events_counting",
    )
    return EnrichmentSerializer(enrichment_config, build)

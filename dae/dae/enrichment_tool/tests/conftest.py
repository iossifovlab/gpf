# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import shutil
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
    setup_pedigree,
    setup_vcf,
)
from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing import setup_gpf_instance
from dae.testing.import_helpers import vcf_study
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


@pytest.fixture
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
def study_data(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[pathlib.Path, pathlib.Path]:
    root_path = tmp_path_factory.mktemp("test_study_data")
    ped_path = setup_pedigree(
        root_path / "test_study" / "in.ped",
        """
        familyId	personId	dadId	momId	sex	status	role	phenotype
        f1	mom1	0	0	2	1	mom	unaffected
        f1	dad1	0	0	1	1	dad	unaffected
        f1	ch1	dad1	mom1	2	2	prb	phenotype1
        f2	mom2	0	0	2	1	mom	unaffected
        f2	dad2	0	0	1	1	dad	unaffected
        f2	ch2	dad2	mom2	1	2	prb	phenotype1
        f2	ch2.1	dad2	mom2	2	1	sib	unaffected
        """,
    )
    vcf_path = setup_vcf(
        root_path / "test_study" / "in.vcf",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
        ##contig=<ID=1>
        #CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	mom1	dad1	ch1	mom2	dad2	ch2	ch2.1
        1	865583	.	G	A	.	.	EFF=SYN:SAMD11	GT	0/0	0/1	0/0	0/0	0/1	0/0	0/0
        1	865624	.	G	A	.	.	EFF=MIS:SAMD11	GT	0/0	0/0	0/1	0/0	0/0	0/1	0/0
        1	865664	.	G	A	.	.	EFF=SYN:SAMD11	GT	0/0	0/0	0/1	0/0	0/0	0/1	0/0
        1	901923	.	C	A	.	.	EFF=MIS:PLEKHN1	GT	0/1	0/0	0/0	0/1	0/0	0/0	0/0
        1	905957	.	C	T	.	.	EFF=SYN:PLEKHN1	GT	0/0	0/0	0/0	0/0	0/0	0/0	0/1
        """,  # noqa: E501
    )
    return ped_path, vcf_path


@pytest.fixture
def create_test_study(
    tmp_path_factory: pytest.TempPathFactory,
    study_data: tuple[pathlib.Path, pathlib.Path],
    t4c8_instance: GPFInstance,
):
    study_path = tmp_path_factory.mktemp("test_study")
    ped_path, vcf_path = study_data

    def _create_study(study_config: dict) -> GenotypeData:
        return vcf_study(
            study_path, "test_study", ped_path, [vcf_path], t4c8_instance,
            study_config_update=study_config)

    yield _create_study
    shutil.rmtree(
        str(pathlib.Path(t4c8_instance.dae_dir, "studies", "test_study")),
    )


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

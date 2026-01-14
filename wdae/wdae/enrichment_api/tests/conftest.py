# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import pathlib
import shutil
import textwrap
from collections.abc import Callable, Generator

import numpy as np
import pytest
import pytest_mock
from dae.enrichment_tool.build_coding_length_enrichment_background import (
    cli as build_coding_len_background_cli,
)
from dae.enrichment_tool.enrichment_utils import (
    get_enrichment_config,
)
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
from dae.pedigrees.families_data import FamiliesData
from dae.studies.study import GenotypeData
from dae.testing.import_helpers import vcf_study
from dae.testing.setup_helpers import (
    setup_gpf_instance,
)
from dae.testing.t4c8_import import t4c8_genes, t4c8_genome
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariantFactory
from studies.study_wrapper import WDAEStudy

from enrichment_api.enrichment_builder import EnrichmentBuilder
from enrichment_api.enrichment_helper import EnrichmentHelper
from enrichment_api.enrichment_serializer import EnrichmentSerializer


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
                    - id: CodingLenBackground
                      name: gene_weight
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
def t4c8_fixture(
    tmp_path: pathlib.Path,
    grr: GenomicResourceRepo,
) -> GPFInstance:
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
        - id: t4c8CodingLenBackground
          name: gene_weight
          desc: Gene coding length enrichment background model
          histogram:
            type: number
            number_of_bins: 10
            view_range:
              min: 0
              max: 20
        """),
    })

    local_grr = build_filesystem_test_repository(root_path / "grr")
    grr = GenomicResourceGroupRepo(
        [grr, local_grr], "enrichment_testing_repo",
    )
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
        familyId  personId  dadId  momId  sex  status  role  phenotype
        f1        mom1      0      0      2    1       mom   unaffected
        f1        dad1      0      0      1    1       dad   unaffected
        f1        ch1       dad1   mom1   2    2       prb   phenotype1
        f2        mom2      0      0      2    1       mom   unaffected
        f2        dad2      0      0      1    1       dad   unaffected
        f2        ch2       dad2   mom2   1    2       prb   phenotype1
        f2        ch2.1     dad2   mom2   2    1       sib   unaffected
        """,
    )
    vcf_path = setup_vcf(
        root_path / "test_study" / "in.vcf",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
        ##contig=<ID=1>
        #CHROM POS    ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom2 dad2 ch2  ch2.1
        1      865583 .  G   A   .    .      .    GT     0/0  0/1  0/0 0/0  0/1  0/0  0/0
        1      865624 .  G   A   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/1  0/0
        1      865664 .  G   A   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/1  0/0
        1      901923 .  C   A   .    .      .    GT     0/1  0/0  0/0 0/1  0/0  0/0  0/0
        1      905957 .  C   T   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/0  0/1
        """,  # noqa: E501
    )
    return ped_path, vcf_path


@pytest.fixture
def create_test_study(
    tmp_path_factory: pytest.TempPathFactory,
    study_data: tuple[pathlib.Path, pathlib.Path],
    t4c8_fixture: GPFInstance,
) -> Generator[Callable[[dict], GenotypeData], None, None]:
    study_path = tmp_path_factory.mktemp("f1_trio")
    ped_path, vcf_path = study_data

    def _create_study(study_config: dict) -> GenotypeData:
        return vcf_study(
            study_path, "f1_trio", ped_path, [vcf_path],
            gpf_instance=t4c8_fixture,
            study_config_update=study_config)

    yield _create_study
    shutil.rmtree(
        str(pathlib.Path(t4c8_fixture.dae_dir, "studies", "f1_trio")),
    )


@pytest.fixture
def enrichment_helper(
    grr: GenomicResourceRepo,
    f1_trio: GenotypeData,
    t4c8_fixture: GPFInstance,
) -> EnrichmentHelper:
    return EnrichmentHelper(
        grr, WDAEStudy(t4c8_fixture.genotype_storages, f1_trio, None))


@pytest.fixture
def enrichment_builder(
    f1_trio: GenotypeData,
    enrichment_helper: EnrichmentHelper,
    t4c8_fixture: GPFInstance,
) -> EnrichmentBuilder:
    return EnrichmentBuilder(
        enrichment_helper,
        t4c8_fixture.gene_scores_db,
        WDAEStudy(t4c8_fixture.genotype_storages, f1_trio, None),
    )


@pytest.fixture
def enrichment_serializer(
    f1_trio: GenotypeData,
    enrichment_builder: EnrichmentBuilder,
) -> EnrichmentSerializer:
    enrichment_config = get_enrichment_config(f1_trio)
    assert enrichment_config is not None

    build = enrichment_builder.build_results(
        gene_syms=["SAMD11", "PLEKHN1", "POGZ"],
        background_id="enrichment/coding_len_testing",
        counting_id="enrichment_events_counting",
    )
    return EnrichmentSerializer(enrichment_config, build)


@pytest.fixture
def psc_config(
) -> dict:
    return {
        "person_set_collections": {

            "phenotype": {
                "id": "phenotype",
                "name": "Phenotype",
                "sources": [
                    {
                        "from": "pedigree",
                        "source": "phenotype",
                    },
                ],
                "default": {
                    "color": "#aaaaaa",
                    "id": "unknown",
                    "name": "unknown",
                },
                "domain": [
                    {
                        "color": "#111111",
                        "id": "phenotype1",
                        "name": "phenotype 1",
                        "values": [
                            "phenotype1",
                        ],
                    },
                    {
                        "color": "#222222",
                        "id": "phenotype2",
                        "name": "phenotype 2",
                        "values": [
                            "phenotype2",
                        ],
                    },
                    {
                        "color": "#333333",
                        "id": "phenotype3",
                        "name": "phenotype 3",
                        "values": [
                            "phenotype3",
                        ],
                    },
                    {
                        "color": "#aaaaaa",
                        "id": "unaffected",
                        "name": "unaffected",
                        "values": [
                            "unaffected",
                        ],
                    },
                ],
            },
            "selected_person_set_collections": [
                "phenotype",
            ],
        },
    }


def f1_trio_variants(
    f1_trio_families: FamiliesData,
) -> list:
    content = (
        pathlib.Path(__file__).parent /
        "fixtures" /
        "f1_trio_variants.json") .read_text()
    records = json.loads(content)
    result = []
    for sv_record, fv_record in records:
        sv = SummaryVariantFactory.summary_variant_from_records(sv_record)
        inheritance_in_members = {
            int(k): [Inheritance.from_value(inh) for inh in v]
            for k, v in fv_record["inheritance_in_members"].items()
        }
        fattributes = fv_record.get("family_variant_attributes")
        fv = FamilyVariant(
            sv,
            f1_trio_families[fv_record["family_id"]],
            genotype=np.array(fv_record["genotype"]),
            best_state=np.array(fv_record["best_state"]),
            inheritance_in_members=inheritance_in_members,
        )
        if fattributes:
            for fa, fattr in zip(
                    fv.family_alt_alleles, fattributes, strict=True):
                fa.update_attributes(fattr)
        result.append(fv)
    return result


@pytest.fixture
def f1_trio(
    tmp_path: pathlib.Path,
    study_data: tuple[pathlib.Path, pathlib.Path],
    psc_config: dict,
    t4c8_fixture: GPFInstance,
    mocker: pytest_mock.MockerFixture,
) -> GenotypeData:

    ped_path, vcf_path = study_data
    study = vcf_study(
        tmp_path / "f1_trio",
        "f1_trio",
        ped_path,
        vcf_paths=[vcf_path],
        gpf_instance=t4c8_fixture,
        study_config_update=psc_config,
    )

    mocker.patch.object(
        study,
        "query_variants",
        return_value=f1_trio_variants(study.families),
    )
    return study

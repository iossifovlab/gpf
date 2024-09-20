# noqa: INP001
# pylint: disable=W0621,C0114,C0116,W0212,W0613

import logging
import os
import pathlib
import textwrap
from collections.abc import Callable, Generator, Iterator
from datetime import timedelta

import pytest
import pytest_mock
from box import Box
from datasets_api.models import Dataset
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.utils import timezone
from gpf_instance.gpf_instance import (
    WGPFInstance,
    get_wgpf_instance,
    reload_datasets,
)
from oauth2_provider.models import (
    AccessToken,
    Application,
    get_access_token_model,
    get_application_model,
)
from studies.study_wrapper import (
    StudyWrapper,
)
from users_api.models import WdaeUser

from dae.common_reports import generate_common_report
from dae.gene_profile.db import GeneProfileDB
from dae.gene_profile.statistic import GPStatistic
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from dae.genomic_resources.testing import (
    build_inmemory_test_repository,
    convert_to_tab_separated,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing import (
    setup_directories,
    setup_gpf_instance,
    setup_pedigree,
    setup_vcf,
    vcf_study,
)
from dae.testing.import_helpers import setup_dataset_config
from dae.testing.t4c8_import import t4c8_genes, t4c8_genome
from dae.tools.pheno_import import main as pheno_import

logger = logging.getLogger(__name__)

pytest_plugins = ["dae_conftests.dae_conftests"]


@pytest.fixture()
def user(
    db: None,  # noqa: ARG001
) -> WdaeUser:
    user_model = get_user_model()
    new_user = user_model.objects.create(
        email="user@example.com",
        name="User",
        is_staff=False,
        is_active=True,
        is_superuser=False,
    )
    new_user.set_password("secret")
    new_user.save()

    return new_user


@pytest.fixture()
def hundred_users(
    db: None,  # noqa: ARG001
    user: WdaeUser,  # noqa: ARG001
) -> list[WdaeUser]:
    user_model = get_user_model()
    users_data = [
        user_model(
            email=f"user{i + 1}@example.com",
            name=f"User{i + 1}",
            is_staff=False,
            is_active=True,
            is_superuser=False,
        ) for i in range(100)
    ]
    return user_model.objects.bulk_create(users_data)


@pytest.fixture()
def user_without_password(
    db: None,  # noqa: ARG001
) -> WdaeUser:
    user_model = get_user_model()
    new_user = user_model.objects.create(
        email="user_without_password@example.com",
        name="User",
        is_staff=False,
        is_active=True,
        is_superuser=False,
    )
    new_user.save()

    return new_user


@pytest.fixture()
def admin(
    db: None,  # noqa: ARG001
) -> WdaeUser:
    user_model = get_user_model()
    new_user = user_model.objects.create(
        email="admin@example.com",
        name="Admin",
        is_staff=True,
        is_active=True,
        is_superuser=True,
    )
    new_user.set_password("secret")
    new_user.save()

    admin_group, _ = Group.objects.get_or_create(name=WdaeUser.SUPERUSER_GROUP)
    new_user.groups.add(admin_group)

    return new_user


@pytest.fixture()
def oauth_app(admin: WdaeUser) -> Application:
    application = get_application_model()
    new_application = application(
        name="testing client app",
        user_id=admin.id,
        client_type="confidential",
        authorization_grant_type="authorization-code",
        redirect_uris="http://localhost:4200/datasets",
        client_id="admin",
        client_secret="secret",  # noqa: S106
    )
    new_application.save()
    return new_application


@pytest.fixture()
def tokens(
    admin: WdaeUser, user: WdaeUser, oauth_app: Application,
) -> tuple[AccessToken, AccessToken]:
    access_token = get_access_token_model()
    user_access_token = access_token(
        user=user,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token="user-token",  # noqa: S106
        application=oauth_app,
    )
    admin_access_token = access_token(
        user=admin,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token="admin-token",  # noqa: S106
        application=oauth_app,
    )
    user_access_token.save()
    admin_access_token.save()
    return user_access_token, admin_access_token


@pytest.fixture()
def user_client(
    user: WdaeUser,  # noqa: ARG001
    tokens: tuple[AccessToken, AccessToken],  # noqa: ARG001
) -> Client:
    return Client(HTTP_AUTHORIZATION="Bearer user-token")


@pytest.fixture()
def anonymous_client(
    client: Client,
    db: None,  # noqa: ARG001
) -> Client:
    client.logout()
    return client


@pytest.fixture()
def admin_client(
    admin: WdaeUser,  # noqa: ARG001
    tokens: tuple[AccessToken, AccessToken],  # noqa: ARG001
) -> Client:
    return Client(HTTP_AUTHORIZATION="Bearer admin-token")


@pytest.fixture()
def datasets(  # noqa: PT004
    db: None,  # noqa: ARG001
) -> None:
    reload_datasets(get_wgpf_instance())


@pytest.fixture(scope="session")
def enrichment_grr() -> GenomicResourceRepo:
    return build_inmemory_test_repository({
        "enrichment": {
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


@pytest.fixture(scope="session")
def wgpf_instance(
    default_dae_config: Box,  # noqa: ARG001
    fixture_dirname: Callable,
    enrichment_grr: GenomicResourceRepo,
) -> Callable[[str | None], WGPFInstance]:

    def build(
        config_filename: str | None = None,
    ) -> WGPFInstance:
        repositories = [
            build_genomic_resource_repository(
                {
                    "id": "grr_test_repo",
                    "type": "directory",
                    "directory": fixture_dirname("test_repo"),
                },
            ),
            build_genomic_resource_repository(
                {
                    "id": "fixtures",
                    "type": "directory",
                    "directory": fixture_dirname("genomic_resources"),
                }),
            enrichment_grr,
            build_genomic_resource_repository(),
        ]
        grr = GenomicResourceGroupRepo(repositories)

        return WGPFInstance.build(config_filename, grr=grr)

    return build


@pytest.fixture(scope="session")
def fixtures_wgpf_instance(
    wgpf_instance: Callable[[str | None], WGPFInstance],
    global_dae_fixtures_dir: str,
) -> WGPFInstance:
    return wgpf_instance(
        os.path.join(global_dae_fixtures_dir, "gpf_instance.yaml"))


@pytest.fixture()
def wdae_gpf_instance(
    db: None,  # noqa: ARG001
    mocker: pytest_mock.MockerFixture,
    admin_client: Client,  # noqa: ARG001
    fixtures_wgpf_instance: WGPFInstance,
    fixture_dirname: Callable,  # noqa: ARG001
) -> WGPFInstance:
    reload_datasets(fixtures_wgpf_instance)
    mocker.patch(
        "query_base.query_base.get_wgpf_instance",
        return_value=fixtures_wgpf_instance,
    )
    mocker.patch(
        "gpf_instance.gpf_instance.get_wgpf_instance",
        return_value=fixtures_wgpf_instance,
    )
    mocker.patch(
        "utils.expand_gene_set.get_wgpf_instance",
        return_value=fixtures_wgpf_instance,
    )
    mocker.patch(
        "datasets_api.permissions.get_wgpf_instance",
        return_value=fixtures_wgpf_instance,
    )
    fixtures_wgpf_instance._gene_profile_config = None  # noqa: SLF001
    fixtures_wgpf_instance.prepare_gp_configuration()

    return fixtures_wgpf_instance


@pytest.fixture()
def gp_wgpf_instance(  # pylint: disable=too-many-arguments
    db: None,  # noqa: ARG001
    mocker: pytest_mock.MockerFixture,
    admin_client: Client,  # noqa: ARG001
    wgpf_instance: Callable,
    sample_gp: GPStatistic,
    gp_config: Box,
    tmp_path: pathlib.Path,
) -> Iterator[WGPFInstance]:

    wdae_gpf_instance = wgpf_instance(
        os.path.join(
            os.path.dirname(__file__),
            "../../data/data-hg19-local/gpf_instance.yaml"))

    reload_datasets(wdae_gpf_instance)

    mocker.patch(
        "query_base.query_base.get_wgpf_instance",
        return_value=wdae_gpf_instance,
    )
    mocker.patch(
        "gpf_instance.gpf_instance.get_wgpf_instance",
        return_value=wdae_gpf_instance,
    )
    mocker.patch(
        "utils.expand_gene_set.get_wgpf_instance",
        return_value=wdae_gpf_instance,
    )
    mocker.patch(
        "datasets_api.permissions.get_wgpf_instance",
        return_value=wdae_gpf_instance,
    )

    wdae_gpf_instance._gene_profile_config = gp_config  # noqa: SLF001
    main_gene_sets = {
        "CHD8 target genes",
        "FMRP Darnell",
        "FMRP Tuschl",
        "PSD",
        "autism candidates from Iossifov PNAS 2015",
        "autism candidates from Sanders Neuron 2015",
        "brain critical genes",
        "brain embryonically expressed",
        "chromatin modifiers",
        "essential genes",
        "non-essential genes",
        "postsynaptic inhibition",
        "synaptic clefts excitatory",
        "synaptic clefts inhibitory",
        "topotecan downreg genes",
    }
    mocker.patch.object(
        wdae_gpf_instance.gene_sets_db,
        "get_gene_set_ids",
        return_value=main_gene_sets,
    )
    wdae_gpf_instance._gene_profile_db = GeneProfileDB(  # noqa: SLF001
        gp_config,
        str(tmp_path / "gpdb"),
        clear=True,
    )
    wdae_gpf_instance._gene_profile_db.insert_gp(sample_gp)  # noqa: SLF001
    wdae_gpf_instance.prepare_gp_configuration()

    yield wdae_gpf_instance

    wdae_gpf_instance._gp_configuration = {}  # noqa: SLF001
    wdae_gpf_instance._gp_table_configuration = {}  # noqa: SLF001

    wdae_gpf_instance.__gene_profile_config = None  # noqa: SLF001
    wdae_gpf_instance.__gene_profile_db = None  # noqa: SLF001


@pytest.fixture()
def gp_config() -> Box:
    return Box({
        "default_dataset": "iossifov_2014",
        "gene_links": [
            {
                "name": "Link with prefix",
                "url": "{gpf_prefix}/datasets/{gene}",
            },
            {
                "name": "Link with gene info",
                "url": (
                    "https://site.com/{gene}?db={genome}&"
                    "position={chromosome_prefix}{chromosome}/"
                    "{gene_start_position}-{gene_stop_position}"
                ),
            },
        ],
        "gene_sets": [
            {
                "category": "relevant_gene_sets",
                "display_name": "Relevant Gene Sets",
                "sets": [
                    {"set_id": "CHD8 target genes", "collection_id": "main"},
                    {
                        "set_id": "FMRP Darnell",
                        "collection_id": "main",
                    },
                ],
            },
        ],
        "genomic_scores": [
            {
                "category": "protection_scores",
                "display_name": "Protection scores",
                "scores": [
                    {"score_name": "SFARI_gene_score", "format": "%s"},
                    {"score_name": "RVIS_rank", "format": "%s"},
                    {"score_name": "RVIS", "format": "%s"},
                ],
            },
            {
                "category": "autism_scores",
                "display_name": "Autism scores",
                "scores": [
                    {"score_name": "SFARI_gene_score", "format": "%s"},
                    {"score_name": "RVIS_rank", "format": "%s"},
                    {"score_name": "RVIS", "format": "%s"},
                ],
            },
        ],
        "datasets": Box({
            "iossifov_2014": Box({
                "statistics": [
                    {
                        "id": "denovo_noncoding",
                        "display_name": "Noncoding",
                        "effects": ["noncoding"],
                        "category": "denovo",
                    },
                    {
                        "id": "denovo_missense",
                        "display_name": "Missense",
                        "effects": ["missense"],
                        "category": "denovo",
                    },
                ],
                "person_sets": [
                    {
                        "set_name": "autism",
                        "collection_name": "phenotype",
                    },
                    {
                        "set_name": "unaffected",
                        "collection_name": "phenotype",
                    },
                ],
            }),
        }),
    })


@pytest.fixture()
def sample_gp() -> GPStatistic:
    gene_sets = ["main_CHD8 target genes"]
    genomic_scores = {
        "protection_scores": {
            "SFARI_gene_score": 1, "RVIS_rank": 193.0, "RVIS": -2.34,
        },
        "autism_scores": {
            "SFARI_gene_score": 1, "RVIS_rank": 193.0, "RVIS": -2.34,
        },
    }
    variant_counts = {
        "iossifov_2014": {
            "autism": {
                "denovo_noncoding": {"count": 53, "rate": 1},
                "denovo_missense": {"count": 21, "rate": 2},
            },
            "unaffected": {
                "denovo_noncoding": {"count": 43, "rate": 3},
                "denovo_missense": {"count": 51, "rate": 4},
            },
        },
    }
    return GPStatistic(
        "CHD8", gene_sets, genomic_scores, variant_counts,
    )


@pytest.fixture()
def use_common_reports(  # noqa: PT004
    wdae_gpf_instance: WGPFInstance,
) -> Generator[None, None, None]:
    all_configs = wdae_gpf_instance.get_all_common_report_configs()
    temp_files = [config.file_path for config in all_configs]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    args = ["--studies", "Study1,study4"]

    generate_common_report.main(args, wdae_gpf_instance)

    yield

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)


@pytest.fixture()
def sample_dataset(
    db: None,  # noqa: ARG001
    wdae_gpf_instance: WGPFInstance,  # noqa: ARG001
) -> Dataset:
    return Dataset.objects.get(dataset_id="Dataset1")


@pytest.fixture()
def hundred_groups(
    db: None,  # noqa: ARG001
    sample_dataset: Dataset, user: WdaeUser,
) -> list[Group]:
    groups_data = [
        Group(
            name=f"Group{i + 1}",
        ) for i in range(100)
    ]
    groups = Group.objects.bulk_create(groups_data)
    for group in groups:
        sample_dataset.groups.add(group)
        user.groups.add(group)
    print(groups)
    return groups


###############################################################################
# New style fixtures
###############################################################################

def setup_t4c8_grr(
    root_path: pathlib.Path,
) -> GenomicResourceRepo:
    repo_path = root_path / "t4c8_grr"
    t4c8_genome(repo_path)
    t4c8_genes(repo_path)

    setup_directories(
        repo_path / "gene_scores" / "t4c8_score",
        {
            GR_CONF_FILE_NAME:
            """
                type: gene_score
                filename: t4c8_gene_score.csv
                scores:
                - id: t4c8_score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                meta:
                  description: t4c8 gene score
                """,
            "t4c8_gene_score.csv": textwrap.dedent("""
                gene,t4c8_score
                t4,10.123456789
                c8,20.0
            """),
        },
    )

    setup_directories(
        repo_path / "genomic_scores" / "score_one",
        {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: position_score
                table:
                  filename: data.txt
                scores:
                - id: score_one
                  type: float
                  name: score
            """),
            "data.txt": textwrap.dedent("""
                chrom\tpos_begin\tscore
                chr1\t4\t0.01
                chr1\t54\t0.02
                chr1\t90\t0.03
                chr1\t100\t0.04
                chr1\t119\t0.05
                chr1\t122\t0.06
            """),
        },
    )

    cli_manage([
        "repo-repair", "-R", str(repo_path), "-j", "1"])

    return build_genomic_resource_repository({
        "id": "t4c8_local",
        "type": "directory",
        "directory": str(repo_path),
    })


def setup_t4c8_instance(
    root_path: pathlib.Path,
) -> GPFInstance:
    t4c8_grr = setup_t4c8_grr(root_path)

    instance_path = root_path / "gpf_instance"

    _t4c8_default_study_config(instance_path)

    setup_directories(
        instance_path, {
            "gpf_instance.yaml": textwrap.dedent("""
                instance_id: t4c8_instance
                annotation:
                  conf_file: annotation.yaml
                reference_genome:
                    resource_id: t4c8_genome
                gene_models:
                    resource_id: t4c8_genes
                gene_scores_db:
                    gene_scores:
                    - "gene_scores/t4c8_score"
                default_study_config:
                  conf_file: default_study_configuration.yaml
                genotype_storage:
                  default: duckdb_wgpf_test
                  storages:
                  - id: duckdb_wgpf_test
                    storage_type: duckdb_parquet
                    memory_limit: 16GB
                    base_dir: '%(wd)s/duckdb_storage'
                gpfjs:
                  visible_datasets:
                    - t4c8_dataset
                    - t4c8_study_1
                    - nonexistend_dataset
            """),
            "annotation.yaml": textwrap.dedent("""
               - position_score: genomic_scores/score_one
            """),
        },
    )

    _study_1_pheno(
        root_path,
        instance_path,
    )

    gpf_instance = setup_gpf_instance(
        instance_path,
        grr=t4c8_grr,
    )

    _t4c8_study_1(root_path, gpf_instance)
    _t4c8_study_2(root_path, gpf_instance)
    _t4c8_dataset(gpf_instance)

    gpf_instance.reload()

    return gpf_instance


@pytest.fixture(scope="session")
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_wgpf_instance")
    return setup_t4c8_instance(root_path)


def _t4c8_study_1(
    root_path: pathlib.Path,
    t4c8_instance: GPFInstance,
) -> None:
    ped_path = setup_pedigree(
        root_path / "t4c8_study_1" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role phenotype
f1.1     mom1     0     0     2   1      mom  unaffected
f1.1     dad1     0     0     1   1      dad  unaffected
f1.1     p1       dad1  mom1  2   2      prb  autism
f1.1     s1       dad1  mom1  1   1      sib  unaffected
f1.3     mom3     0     0     2   1      mom  unaffected
f1.3     dad3     0     0     1   1      dad  unaffected
f1.3     p3       dad3  mom3  2   2      prb  autism
f1.3     s3       dad3  mom3  2   1      sib  unaffected
        """)
    vcf_path1 = setup_vcf(
        root_path / "t4c8_study_1" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT mom1 dad1 p1  s1  mom3 dad3 p3  s3
chr1   4   .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/0 0/1  0/2  0/2 0/0
chr1   54  .  T   C    .    .      .    GT     0/1  0/1  0/1 0/1 0/0  0/0  0/1 0/1
chr1   90  .  G   C,GA .    .      .    GT     0/1  0/2  0/2 0/2 0/1  0/2  0/1 0/2
chr1   100 .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/0 0/2  0/0  0/0 0/0
chr1   119 .  A   G,C  .    .      .    GT     0/0  0/0  0/2 0/2 0/1  0/2  0/1 0/2
chr1   122 .  A   C,AC .    .      .    GT     0/1  0/1  0/1 0/1 0/2  0/2  0/2 0/1
        """)  # noqa: E501

    vcf_study(
        root_path,
        "t4c8_study_1", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update={
            "input": {
                "vcf": {
                    "denovo_mode": "denovo",
                    "omission_mode": "omission",
                },
            },
        },
        study_config_update={
            "phenotype_data": "study_1_pheno",
        },
    )


def _t4c8_study_2(
    root_path: pathlib.Path,
    t4c8_instance: GPFInstance,
) -> GenotypeData:
    ped_path = setup_pedigree(
        root_path / "t4c8_study_2" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f2.1     mom1     0     0     2   1      mom
f2.1     dad1     0     0     1   1      dad
f2.1     ch1      dad1  mom1  2   2      prb
f2.3     mom3     0     0     2   1      mom
f2.3     dad3     0     0     1   1      dad
f2.3     ch3      dad3  mom3  2   2      prb
f2.3     ch4      dad3  mom3  2   0      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "t4c8_study_2" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3 ch4
chr1   5   .  A   C   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0 0/1
chr1   6   .  C   G   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/1 0/0
chr1   7   .  G   T   .    .      .    GT     0/0  1/0  0/1 0/0  0/0  0/0 0/1
        """)

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            },
        },
    }
    return vcf_study(
        root_path,
        "t4c8_study_2", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
        study_config_update={
            "conf_dir": str(root_path / "t4c8_study_2"),
            "person_set_collections": {
                "phenotype": {
                    "id": "phenotype",
                    "name": "Phenotype",
                    "sources": [
                        {
                            "from": "pedigree",
                            "source": "status",
                        },
                    ],
                    "default": {
                        "color": "#aaaaaa",
                        "id": "unspecified",
                        "name": "unspecified",
                    },
                    "domain": [
                        {
                            "color": "#bbbbbb",
                            "id": "epilepsy",
                            "name": "epilepsy",
                            "values": [
                                "affected",
                            ],
                        },
                        {
                            "color": "#00ff00",
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
        })


def _t4c8_dataset(
    t4c8_instance: GPFInstance,
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    (root_path / "datasets").mkdir(exist_ok=True)

    setup_dataset_config(
        t4c8_instance,
        "t4c8_dataset",
        ["t4c8_study_1", "t4c8_study_2"],
        dataset_config_update=textwrap.dedent(f"""
            conf_dir: { root_path / "dataset "}
            person_set_collections:
                phenotype:
                  id: phenotype
                  name: Phenotype
                  sources:
                  - from: pedigree
                    source: status
                  domain:
                  - color: '#4b2626'
                    id: developmental_disorder
                    name: developmental disorder
                    values:
                    - affected
                  - color: '#ffffff'
                    id: unaffected
                    name: unaffected
                    values:
                    - unaffected
                  default:
                    color: '#aaaaaa'
                    id: unspecified
                    name: unspecified
                selected_person_set_collections:
                - phenotype"""))


@pytest.fixture(scope="session")
def t4c8_study_1(t4c8_instance: GPFInstance) -> GenotypeData:
    return t4c8_instance.get_genotype_data("t4c8_study_1")


@pytest.fixture(scope="session")
def t4c8_study_2(t4c8_instance: GPFInstance) -> GenotypeData:
    return t4c8_instance.get_genotype_data("t4c8_study_2")


@pytest.fixture(scope="session")
def t4c8_dataset(t4c8_instance: GPFInstance) -> GenotypeData:
    return t4c8_instance.get_genotype_data("t4c8_dataset")


@pytest.fixture(scope="session")
def t4c8_study_1_wrapper(
    t4c8_instance: GPFInstance,
) -> StudyWrapper:

    data_study = t4c8_instance.get_genotype_data("t4c8_study_1")

    return StudyWrapper(
        data_study,
        t4c8_instance._pheno_registry,  # noqa: SLF001
        t4c8_instance.gene_scores_db,
        t4c8_instance,
    )


def setup_wgpf_intance(root_path: pathlib.Path) -> WGPFInstance:
    t4c8_instance = setup_t4c8_instance(root_path)
    t4c8_grr = t4c8_instance.grr
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    instance_filename = str(root_path / "gpf_instance.yaml")
    return WGPFInstance.build(instance_filename, grr=t4c8_grr)


@pytest.fixture(scope="session")
def session_t4c8_wgpf_instance(
    tmp_path_factory: pytest.TempPathFactory,
) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("session_t4c8_wgpf_instance")
    return setup_wgpf_intance(root_path)


@pytest.fixture()
def t4c8_wgpf_instance(
    session_t4c8_wgpf_instance: WGPFInstance,
    db: None,  # noqa: ARG001
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:
    reload_datasets(session_t4c8_wgpf_instance)
    mocker.patch(
        "gpf_instance.gpf_instance.get_wgpf_instance",
        return_value=session_t4c8_wgpf_instance,
    )
    mocker.patch(
        "datasets_api.permissions.get_wgpf_instance",
        return_value=session_t4c8_wgpf_instance,
    )
    mocker.patch(
        "query_base.query_base.get_wgpf_instance",
        return_value=session_t4c8_wgpf_instance,
    )

    return session_t4c8_wgpf_instance


@pytest.fixture()
def t4c8_wgpf(
    tmp_path: pathlib.Path,
    db: None,  # noqa: ARG001
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:
    wgpf_instance = setup_wgpf_intance(tmp_path)

    reload_datasets(wgpf_instance)
    mocker.patch(
        "gpf_instance.gpf_instance.get_wgpf_instance",
        return_value=wgpf_instance,
    )
    mocker.patch(
        "datasets_api.permissions.get_wgpf_instance",
        return_value=wgpf_instance,
    )
    mocker.patch(
        "query_base.query_base.get_wgpf_instance",
        return_value=wgpf_instance,
    )

    return wgpf_instance


def _t4c8_default_study_config(instance_path: pathlib.Path) -> None:
    setup_directories(
        instance_path, {
            "default_study_configuration.yaml": textwrap.dedent("""
phenotype_browser: false
phenotype_tool: false
study_type:
- WE
study_phenotype: autism
has_transmitted: true
has_denovo: true
has_complex: true
has_cnv: false
genome: hg38
chr_prefix: true

person_set_collections:
  selected_person_set_collections:
  - phenotype
  phenotype:
    id: phenotype
    name: Phenotype
    sources:
    - from: pedigree
      source: status
    domain:
    - id: autism
      name: autism
      values:
      - affected
      color: '#ff2121'
    - id: unaffected
      name: unaffected
      values:
      - unaffected
      color: '#ffffff'
    default:
      id: unspecified
      name: unspecified
      values:
      - unspecified
      color: '#aaaaaa'
genotype_browser:
  enabled: true
  has_family_filters: true
  has_person_filters: true
  has_study_filters: false
  has_present_in_child: true
  has_present_in_parent: true
  has_pedigree_selector: true
  preview_columns:
  - family
  - variant
  - genotype
  - effect
  - gene_scores
  - freq
  - pheno_measures
  download_columns:
  - family
  - study_phenotype
  - variant
  - variant_extra
  - family_person_ids
  - family_structure
  - best
  - family_genotype
  - carriers
  - inheritance
  - phenotypes
  - par_called
  - allele_freq
  - effect
  - geneeffect
  - effectdetails
  - gene_scores
  - pheno_measures

  summary_preview_columns:
  - variant
  - seen_as_denovo
  - seen_in_affected
  - seen_in_unaffected
  - par_called
  - allele_freq
  - effect
  - count
  - geneeffect
  - effectdetails
  - gene_scores
  summary_download_columns:
  - variant
  - seen_as_denovo
  - seen_in_affected
  - seen_in_unaffected
  - par_called
  - allele_freq
  - effect
  - count
  - geneeffect
  - effectdetails
  - gene_scores
  column_groups:
    genotype:
      name: genotype
      columns:
      - pedigree
      - carrier_person_attributes
      - family_person_attributes
    effect:
      name: effect
      columns:
      - worst_effect
      - genes
    gene_scores:
      name: vulnerability/intolerance
      columns:
      - t4c8_score
    family:
      name: family
      columns:
      - family_id
      - study
    variant:
      name: variant
      columns:
      - location
      - variant
    variant_extra:
      name: variant
      columns:
      - chrom
      - position
      - reference
      - alternative
    carriers:
      name: carriers
      columns:
      - carrier_person_ids
      - carrier_person_attributes
    phenotypes:
      name: phenotypes
      columns:
      - family_phenotypes
      - carrier_phenotypes
    freq:
      name: Frequency
      columns:
      - freq_ssc
      - freq_exome_gnomad
      - freq_genome_gnomad
    pheno_measures:
      name: pheno measures
      columns:
      - pheno_age
      - pheno_iq

  columns:
    genotype:
      pedigree:
        name: pedigree
        source: pedigree
      worst_effect:
        name: worst effect
        source: worst_effect
      genes:
        name: genes
        source: genes
      t4c8_score:
        name: t4c8 score
        source: t4c8_score
        format: '%%f'
      family_id:
        name: family id
        source: family
      study:
        name: study
        source: study_name
      family_person_ids:
        name: family person ids
        source: family_person_ids
      location:
        name: location
        source: location
      variant:
        name: variant
        source: variant
      chrom:
        name: CHROM
        source: chrom
      position:
        name: POS
        source: position
      reference:
        name: REF
        source: reference
      alternative:
        name: ALT
        source: alternative
      carrier_person_ids:
        name: carrier person ids
        source: carrier_person_ids
      carrier_person_attributes:
        name: carrier person attributes
        source: carrier_person_attributes
      family_person_attributes:
        name: family person attributes
        source: family_person_attributes
      family_phenotypes:
        name: family phenotypes
        source: family_phenotypes
      carrier_phenotypes:
        name: carrier phenotypes
        source: carrier_phenotypes
      inheritance:
        name: inheritance type
        source: inheritance_type
      study_phenotype:
        name: study phenotype
        source: study_phenotype
      best:
        name: family best state
        source: best_st
      family_genotype:
        name: family genotype
        source: genotype
      family_structure:
        name: family structure
        source: family_structure
      geneeffect:
        name: all effects
        source: effects
      effectdetails:
        name: effect details
        source: effect_details
      alt_alleles:
        name: alt alleles
        source: af_allele_count
      par_called:
        name: parents called
        source: af_parents_called_count
      allele_freq:
        name: allele frequency
        source: af_allele_freq
      seen_as_denovo:
        name: seen_as_denovo
        source: seen_as_denovo
      seen_in_affected:
        name: seen_in_affected
        source: seen_in_affected
      seen_in_unaffected:
        name: seen_in_unaffected
        source: seen_in_unaffected

    phenotype:
      pheno_age:
        role: prb
        source: "i1.age"
        format: "%%.3f"
        name: Age
      pheno_iq:
        role: prb
        source: "i1.iq"
        format: "%%.3f"
        name: IQ

common_report:
  enabled: true
  effect_groups:
  - LGDs
  - nonsynonymous
  - UTRs
  - CNV
  effect_types:
  - Nonsense
  - Frame-shift
  - Splice-site
  - Missense
  - No-frame-shift
  - noStart
  - noEnd
  - Synonymous
  - Non coding
  - Intron
  - Intergenic
  - 3'-UTR
  - 5'-UTR
denovo_gene_sets:
  enabled: true
  selected_person_set_collections:
  - phenotype
  standard_criterias:
    effect_types:
      segments:
        LGDs: LGDs
        Missense: missense
        Synonymous: synonymous
    sexes:
      segments:
        Female: F
        Male: M
        Unspecified: U
  recurrency_criteria:
    segments:
      Single:
          start: 1
          end: 2
      Triple:
          start: 3
          end: -1
      Recurrent:
          start: 2
          end: -1
  gene_sets_names:
  - LGDs
  - LGDs.Male
  - LGDs.Female
  - LGDs.Recurrent
  - LGDs.Single
  - LGDs.Triple
  - Missense
  - Missense.Male
  - Missense.Female
  - Missense.Recurrent
  - Missense.Triple
  - Synonymous
  - Synonymous.Male
  - Synonymous.Female
  - Synonymous.Recurrent
  - Synonymous.Triple
enrichment:
  enabled: false
gene_browser:
  enabled: true
  frequency_column: "score_one"
  effect_column: "effect.worst effect type"
  location_column: "variant.location"
  domain_min: 0.01
  domain_max: 100
            """),
        },
    )


def _study_1_pheno(
    root_path: pathlib.Path,
    instance_path: pathlib.Path,
) -> None:
    pheno_path = root_path / "study_1_pheno_import"
    ped_path = setup_pedigree(
        pheno_path / "pedigree" / "study_1_pheno.ped", textwrap.dedent("""
familyId personId dadId momId sex status role phenotype
f1.1     mom1     0     0     2   1      mom  unaffected
f1.1     dad1     0     0     1   1      dad  unaffected
f1.1     p1       dad1  mom1  2   2      prb  autism
f1.1     s1       dad1  mom1  1   1      sib  unaffected
f1.2     mom2     0     0     2   1      mom  unaffected
f1.2     dad2     0     0     1   1      dad  unaffected
f1.2     p2       dad2  mom2  2   2      prb  autism
f1.2     s2       dad2  mom2  1   1      sib  unaffected
f1.3     mom3     0     0     2   1      mom  unaffected
f1.3     dad3     0     0     1   1      dad  unaffected
f1.3     p3       dad3  mom3  2   2      prb  autism
f1.3     s3       dad3  mom3  2   1      sib  unaffected
f1.4     mom4     0     0     2   1      mom  unaffected
f1.4     dad4     0     0     1   1      dad  unaffected
f1.4     p4       dad4  mom4  2   2      prb  autism
f1.4     s4       dad4  mom4  2   1      sib  unaffected
        """),
    )
    setup_directories(
        pheno_path / "instruments", {
        "i1.csv": textwrap.dedent("""
personId,age,iq,m1,m2,m3,m4,m5
mom1,495.85101568044115,97.50432405604393,52.81283557677513,30.02770124013255,71.37577329050546,7,val3
dad1,455.7415088310677,95.69209763066596,30.17069676417365,46.09107120958192,80.80918132613797,6,val5
p1,166.33975600961486,104.91189182223437,110.71113119414974,28.525899172698242,35.91763476048754,0,val3
s1,171.7517126432528,38.666056616173776,89.98648478019244,45.48364527683189,36.402944728465634,1,val2
mom2,538.9804553566523,77.21819916001459,54.140552015763305,46.634514570013124,57.885493130264315,5,val3
dad2,565.9100943623504,74.26681832043354,63.03565166617398,36.205901443513405,88.42665767730243,8,val4
p2,111.53800328766471,66.69411560428445,75.83138674585497,43.482874849182046,42.4619179257155,0,val2
s2,112.55713299362333,103.40031120687064,81.23597041806396,26.159521971641645,34.43553369099789,0,val3
mom3,484.44595137123844,65.76732558306583,91.03624223708377,60.66214100006954,82.3034749091715,6,val3
dad3,529.0340708815538,102.32942897750618,102.99152655929812,49.50549744685827,74.83036326691582,2,val1
p3,68.00148724003327,69.33300891928155,96.6345202846831,39.854725276645524,41.07164247649136,2,val1
s3,82.79666720433862,14.497397082398294,70.28387304358455,36.733060149749015,32.979273050187054,0,val3
mom4,413.46229185729595,100.18402999912475,80.87413378193011,56.58170217214086,52.756604936750776,2,val4
dad4,519.696209236225,95.17277547237524,50.73287772082178,34.58584942696778,63.241999271724694,2,val3
p4,157.61834502034586,103.07449426952655,99.54884909890457,37.31662520714209,50.87487739184816,2,val1
s4,121.0199895975403,39.74107684421966,77.32212831797972,51.37116746952451,36.558215318085175,1,val4
        """),
    })

    setup_directories(
        pheno_path, {
        "regressions.yaml": textwrap.dedent("""
        regression:
          age:
            instrument_name: "i1"
            measure_name: "age"
            display_name: "Age"
            jitter: 0.1
          iq:
            instrument_name: "i1"
            measure_name: "iq"
            display_name: "Non verbal IQ"
            jitter: 0.1
        """),
    })

    pheno_import([
        "--pheno-id", "study_1_pheno",
        "-p", str(ped_path),
        "-i", str(pheno_path / "instruments"),
        "--force",
        "-j", "1",
        "--person-column", "personId",
        "-o", str(instance_path / "pheno" / "study_1_pheno"),
        "--task-status-dir", str(pheno_path / "status"),
        "--regression", str(pheno_path / "regressions.yaml"),
    ])

# ruff: ignore[implicit-namespace-package]
# pylint: disable=W0621,C0114,C0116,W0212,W0613

import logging
import pathlib
import textwrap
from collections.abc import Iterator, Sequence
from datetime import timedelta
from typing import cast

import pytest
import pytest_mock
from datasets_api.models import Dataset
from datasets_api.permissions import add_group_perm_to_user
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, Group, User
from django.test import Client
from django.utils import timezone
from gain.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from gain.genomic_resources.testing import (
    build_inmemory_test_repository,
    convert_to_tab_separated,
    setup_directories,
    setup_pedigree,
    setup_vcf,
)
from gpf_instance.feature_flags import reset_feature_flags
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
from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer
from studies.study_wrapper import WDAEStudy
from users_api.models import WdaeUser
from utils.testing import setup_t4c8_instance, setup_wgpf_instance

from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.pheno.build_pheno_browser import main as build_browser
from gpf.pheno.pheno_import import main as pheno_import
from gpf.studies.study import GenotypeData
from gpf.testing.import_helpers import setup_dataset_config, vcf_study

logger = logging.getLogger(__name__)


@pytest.fixture
def reset_flags() -> Iterator[None]:
    """Drop the cached feature-flags singleton around a test.

    Reset before and after so ``override_settings(FEATURE_FLAGS=...)`` takes
    effect and no toggled state leaks into other tests.
    """
    reset_feature_flags()
    yield
    reset_feature_flags()


@pytest.fixture
def hundred_users(
    db: None,  # ruff: ignore[unused-function-argument]
    user: WdaeUser,  # ruff: ignore[unused-function-argument]
) -> Sequence[WdaeUser]:
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
    return cast(Sequence[WdaeUser], user_model.objects.bulk_create(users_data))


@pytest.fixture
def user_without_password(
    db: None,  # ruff: ignore[unused-function-argument]
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

    return cast(WdaeUser, new_user)  # type: ignore


@pytest.fixture
def admin(
    db: None,  # ruff: ignore[unused-function-argument]
) -> WdaeUser:
    user_model = get_user_model()
    new_user = user_model.objects.create(
        email="admin@example.com",
        name="Admin",
        is_staff=True,
        is_active=True,
        is_superuser=True,
    )
    new_user = cast(WdaeUser, new_user)  # type: ignore
    new_user.set_password("secret")
    new_user.save()

    admin_group, _ = Group.objects.get_or_create(name=WdaeUser.SUPERUSER_GROUP)
    new_user.groups.add(admin_group)

    return new_user


@pytest.fixture
def oauth_app(admin: AbstractUser) -> Application:
    application = get_application_model()
    new_application = application(
        name="testing client app",
        user_id=admin.id,  # type: ignore
        client_type="confidential",
        authorization_grant_type="authorization-code",
        redirect_uris="http://localhost:4200/datasets",
        client_id="admin",
        client_secret="secret",  # ruff: ignore[hardcoded-password-func-arg]
    )
    new_application.save()
    return cast(Application, new_application)


@pytest.fixture
def tokens(
    admin: WdaeUser, user: WdaeUser, oauth_app: Application,
) -> tuple[AccessToken, AccessToken]:
    access_token = get_access_token_model()
    user_access_token = access_token(
        user=user,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token="user-token",  # ruff: ignore[hardcoded-password-func-arg]
        application=oauth_app,
    )
    admin_access_token = access_token(
        user=admin,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token="admin-token",  # ruff: ignore[hardcoded-password-func-arg]
        application=oauth_app,
    )
    user_access_token.save()
    admin_access_token.save()
    return (
        cast(AccessToken, user_access_token),
        cast(AccessToken, admin_access_token),
    )


@pytest.fixture
def datasets(
    db: None,  # ruff: ignore[unused-function-argument]
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


@pytest.fixture
def sample_dataset(
    db: None,  # ruff: ignore[unused-function-argument]
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> Dataset:
    return Dataset.objects.get(dataset_id="t4c8_dataset")


@pytest.fixture
def hundred_groups(
    db: None,  # ruff: ignore[unused-function-argument]
    sample_dataset: Dataset,
    user: WdaeUser,
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

@pytest.fixture
def user(
    db: None,  # ruff: ignore[unused-function-argument]
) -> WdaeUser:
    user_model = get_user_model()
    new_user = user_model.objects.create(
        email="user@example.com",
        name="User",
        is_staff=False,
        is_active=True,
        is_superuser=False,
    )
    new_user = cast(WdaeUser, new_user)  # type: ignore
    new_user.set_password("secret")
    new_user.groups.add(Group.objects.create(name="user@example.com"))
    new_user.save()

    return new_user


@pytest.fixture
def partial_grant(user: User) -> User:
    """Grant the user one of the two child studies of t4c8_dataset."""
    add_group_perm_to_user("t4c8_study_2", user)
    return user


@pytest.fixture
def all_children_grant(user: User) -> User:
    """Grant the user both child studies of t4c8_dataset."""
    add_group_perm_to_user("t4c8_study_1", user)
    add_group_perm_to_user("t4c8_study_2", user)
    return user


@pytest.fixture
def full_grant(user: User) -> User:
    """Grant the user t4c8_dataset itself."""
    add_group_perm_to_user("t4c8_dataset", user)
    return user


@pytest.fixture
def admin_client(
    admin: AbstractUser,  # ruff: ignore[unused-function-argument]
    tokens: tuple[AccessToken, AccessToken],  # ruff: ignore[unused-function-argument]
) -> Client:
    return Client(HTTP_AUTHORIZATION="Bearer admin-token")


@pytest.fixture
def user_client(
    user: AbstractUser,  # ruff: ignore[unused-function-argument]
    tokens: tuple[AccessToken, AccessToken],  # ruff: ignore[unused-function-argument]
) -> Client:
    return Client(HTTP_AUTHORIZATION="Bearer user-token")


@pytest.fixture
def anonymous_client(
    client: Client,
    db: None,  # ruff: ignore[unused-function-argument]
) -> Client:
    client.logout()
    return client


@pytest.fixture(scope="session")
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_wgpf_instance")
    return setup_t4c8_instance(root_path)


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
) -> WDAEStudy:

    data_study = t4c8_instance.get_genotype_data("t4c8_study_1")
    pheno_data = t4c8_instance.get_phenotype_data("study_1_pheno")
    registry = t4c8_instance.genotype_storages

    return WDAEStudy(
        registry,
        data_study,
        pheno_data,
    )


@pytest.fixture(scope="session")
def t4c8_study_2_wrapper(
    t4c8_instance: GPFInstance,
) -> WDAEStudy:

    data_study = t4c8_instance.get_genotype_data("t4c8_study_2")
    registry = t4c8_instance.genotype_storages

    return WDAEStudy(registry, data_study, None)


@pytest.fixture(scope="session")
def session_t4c8_wgpf_instance(
    t4c8_instance: GPFInstance,
) -> WGPFInstance:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    return setup_wgpf_instance(root_path)


@pytest.fixture
def t4c8_wgpf_instance(
    session_t4c8_wgpf_instance: WGPFInstance,
    db: None,  # ruff: ignore[unused-function-argument]
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:

    query_transformer = QueryTransformer(
        session_t4c8_wgpf_instance.gene_scores_db,
        session_t4c8_wgpf_instance.reference_genome.chromosomes,
        session_t4c8_wgpf_instance.reference_genome.chrom_prefix,
    )

    response_transformer = ResponseTransformer(
        session_t4c8_wgpf_instance.gene_scores_db,
    )

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
    mocker.patch(
        "query_base.query_base.get_or_create_query_transformer",
        return_value=query_transformer,
    )
    mocker.patch(
        "query_base.query_base.get_or_create_response_transformer",
        return_value=response_transformer,
    )
    mocker.patch(
        "utils.expand_gene_set.get_wgpf_instance",
        return_value=session_t4c8_wgpf_instance,
    )

    return session_t4c8_wgpf_instance


@pytest.fixture
def t4c8_query_transformer(
    t4c8_wgpf_instance: WGPFInstance,
) -> QueryTransformer:
    return QueryTransformer(
        t4c8_wgpf_instance.gene_scores_db,
        t4c8_wgpf_instance.reference_genome.chromosomes,
        t4c8_wgpf_instance.reference_genome.chrom_prefix,
    )


@pytest.fixture
def t4c8_response_transformer(
    t4c8_wgpf_instance: WGPFInstance,
) -> ResponseTransformer:
    return ResponseTransformer(
        t4c8_wgpf_instance.gene_scores_db,
    )


@pytest.fixture
def t4c8_wgpf(
    tmp_path: pathlib.Path,
    db: None,  # ruff: ignore[unused-function-argument]
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:
    wgpf_instance = setup_wgpf_instance(tmp_path)

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


###############################################################################
# A phenotype group and a genotype dataset that names it
###############################################################################

def _import_pheno_leaf(
    root_path: pathlib.Path,
    pheno_dir: pathlib.Path,
    pheno_id: str,
    pedigree: str,
    instruments: dict[str, str],
) -> None:
    ped_path = setup_pedigree(root_path / pheno_id / "in.ped", pedigree)
    instruments_dir = root_path / pheno_id / "instruments"
    setup_directories(instruments_dir, instruments)
    pheno_import([
        "--pheno-id", pheno_id,
        "-p", str(ped_path),
        "-i", str(instruments_dir),
        "--force",
        "-j", "1",
        "--person-column", "personId",
        "-o", str(pheno_dir / pheno_id),
        "--task-status-dir", str(root_path / pheno_id / "status"),
        "--task-log-dir", str(root_path / pheno_id / "log"),
    ])


def _import_genotype_leaf(
    root_path: pathlib.Path,
    instance: WGPFInstance,
    study_id: str,
    pedigree: str,
    vcf: str,
    pheno_id: str,
) -> None:
    ped_path = setup_pedigree(
        root_path / study_id / "pedigree" / "in.ped", pedigree)
    vcf_path = setup_vcf(root_path / study_id / "vcf" / "in.vcf.gz", vcf)
    vcf_study(
        root_path, study_id, ped_path, [vcf_path],
        gpf_instance=instance,
        study_config_update={
            "phenotype_data": pheno_id,
            # The phenotype columns of the default study configuration
            # name the measures of ``study_1_pheno``.
            "genotype_browser": {"enabled": False},
        },
    )


@pytest.fixture(scope="module")
def pheno_group_module(
    tmp_path_factory: pytest.TempPathFactory,
) -> WGPFInstance:
    """Build a phenotype group of three leaves and a dataset that names it.

    The phenotype group ``pheno_group`` has the leaves ``study_1_pheno``,
    ``sibling_pheno`` and ``third_pheno``. The genotype dataset
    ``pheno_parent`` names ``pheno_group`` under ``phenotype_data``. Its
    child studies ``t4c8_study_1``, ``sibling_study`` and ``third_study``
    each name one leaf. Its child study ``t4c8_study_2`` names none.
    """
    root_path = tmp_path_factory.mktemp("pheno_group")
    instance = setup_wgpf_instance(root_path)
    pheno_dir = pathlib.Path(instance.dae_dir) / "pheno"
    _import_pheno_leaf(
        root_path, pheno_dir, "sibling_pheno", """
familyId personId dadId momId sex status role
fx.1     momx     0     0     2   1      mom
fx.1     dadx     0     0     1   1      dad
fx.1     px       dadx  momx  2   2      prb
        """, {"sib.csv": "personId,age\nmomx,40\ndadx,42\npx,7\n"})
    _import_pheno_leaf(
        root_path, pheno_dir, "third_pheno", """
familyId personId dadId momId sex status role
fy.1     momy     0     0     2   1      mom
fy.1     dady     0     0     1   1      dad
fy.1     py       dady  momy  1   2      prb
        """, {"thr.csv": "personId,score\nmomy,13\ndady,17\npy,19\n"})
    setup_directories(pheno_dir / "pheno_group", {
        "pheno_group.yaml": textwrap.dedent("""
            id: pheno_group
            name: Pheno Group
            type: group
            children:
              - study_1_pheno
              - sibling_pheno
              - third_pheno
        """),
    })
    for pheno_id in ("sibling_pheno", "third_pheno", "pheno_group"):
        build_browser([
            pheno_id,
            "--gpf-instance", str(pathlib.Path(instance.dae_dir)
                                  / "gpf_instance.yaml"),
            "-j", "1",
            "--force",
            "--task-status-dir", str(root_path / pheno_id / "status"),
            "--task-log-dir", str(root_path / pheno_id / "log"),
        ])
    _import_genotype_leaf(
        root_path, instance, "sibling_study", """
familyId personId dadId momId sex status role
fx.1     momx     0     0     2   1      mom
fx.1     dadx     0     0     1   1      dad
fx.1     px       dadx  momx  2   2      prb
        """, """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT momx dadx px
chr1   5   .  A   C   .    .      .    GT     0/0  0/0  0/1
        """, "sibling_pheno")
    _import_genotype_leaf(
        root_path, instance, "third_study", """
familyId personId dadId momId sex status role
fy.1     momy     0     0     2   1      mom
fy.1     dady     0     0     1   1      dad
fy.1     py       dady  momy  1   2      prb
        """, """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT momy dady py
chr1   5   .  A   C   .    .      .    GT     0/0  0/0  0/1
        """, "third_pheno")
    setup_dataset_config(
        instance, "pheno_parent",
        ["t4c8_study_1", "sibling_study", "third_study", "t4c8_study_2"],
        dataset_config_update="phenotype_data: pheno_group",
    )
    instance.reload()
    return instance


@pytest.fixture
def pheno_group_instance(
    pheno_group_module: WGPFInstance,
    db: None,  # ruff: ignore[unused-function-argument]
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:
    reload_datasets(pheno_group_module)
    for target in (
        "gpf_instance.gpf_instance.get_wgpf_instance",
        "datasets_api.permissions.get_wgpf_instance",
        "query_base.query_base.get_wgpf_instance",
        "utils.expand_gene_set.get_wgpf_instance",
    ):
        mocker.patch(target, return_value=pheno_group_module)
    return pheno_group_module


@pytest.fixture
def grant_on_study_1_pheno(user: User) -> User:
    add_group_perm_to_user("study_1_pheno", user)
    return user


@pytest.fixture
def grant_on_t4c8_study_1(user: User) -> User:
    """Grant the genotype child of ``pheno_parent`` that names study_1_pheno."""
    add_group_perm_to_user("t4c8_study_1", user)
    return user

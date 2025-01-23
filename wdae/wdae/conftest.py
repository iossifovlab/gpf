# noqa: INP001
# pylint: disable=W0621,C0114,C0116,W0212,W0613

import logging
import os
import pathlib
from collections.abc import Generator
from datetime import timedelta
from typing import cast

import pytest
import pytest_mock
from datasets_api.models import Dataset
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, Group
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
from utils.testing import setup_t4c8_instance, setup_wgpf_instance

from dae.common_reports import generate_common_report
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

logger = logging.getLogger(__name__)

pytest_plugins = ["dae_conftests.dae_conftests"]


@pytest.fixture
def hundred_users(
    db: None,  # noqa: ARG001
    user: WdaeUser,  # noqa: ARG001
) -> list[AbstractUser]:
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


@pytest.fixture
def user_without_password(
    db: None,  # noqa: ARG001
) -> AbstractUser:
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


@pytest.fixture
def admin(
    db: None,  # noqa: ARG001
) -> AbstractUser:
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
        client_secret="secret",  # noqa: S106
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
    return (
        cast(AccessToken, user_access_token),
        cast(AccessToken, admin_access_token),
    )


@pytest.fixture
def datasets(
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


@pytest.fixture
def use_common_reports(
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


@pytest.fixture
def sample_dataset(
    db: None,  # noqa: ARG001
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> Dataset:
    return Dataset.objects.get(dataset_id="t4c8_dataset")


@pytest.fixture
def hundred_groups(
    db: None,  # noqa: ARG001
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
    db: None,  # noqa: ARG001
) -> AbstractUser:
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


@pytest.fixture
def admin_client(
    admin: AbstractUser,  # noqa: ARG001
    tokens: tuple[AccessToken, AccessToken],  # noqa: ARG001
) -> Client:
    return Client(HTTP_AUTHORIZATION="Bearer admin-token")


@pytest.fixture
def user_client(
    user: AbstractUser,  # noqa: ARG001
    tokens: tuple[AccessToken, AccessToken],  # noqa: ARG001
) -> Client:
    return Client(HTTP_AUTHORIZATION="Bearer user-token")


@pytest.fixture
def anonymous_client(
    client: Client,
    db: None,  # noqa: ARG001
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
) -> StudyWrapper:

    data_study = t4c8_instance.get_genotype_data("t4c8_study_1")

    return StudyWrapper(
        data_study,
        t4c8_instance._pheno_registry,  # noqa: SLF001
        t4c8_instance.gene_scores_db,
        t4c8_instance,
    )


@pytest.fixture(scope="session")
def t4c8_study_2_wrapper(
    t4c8_instance: GPFInstance,
) -> StudyWrapper:

    data_study = t4c8_instance.get_genotype_data("t4c8_study_2")

    return StudyWrapper(
        data_study,
        t4c8_instance._pheno_registry,  # noqa: SLF001
        t4c8_instance.gene_scores_db,
        t4c8_instance,
    )


@pytest.fixture(scope="session")
def session_t4c8_wgpf_instance(
    tmp_path_factory: pytest.TempPathFactory,
) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("session_t4c8_wgpf_instance")
    return setup_wgpf_instance(root_path)


@pytest.fixture
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
    mocker.patch(
        "utils.expand_gene_set.get_wgpf_instance",
        return_value=session_t4c8_wgpf_instance,
    )

    return session_t4c8_wgpf_instance


@pytest.fixture
def t4c8_wgpf(
    tmp_path: pathlib.Path,
    db: None,  # noqa: ARG001
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

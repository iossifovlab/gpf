# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,

import os
import sys
import contextlib
import pathlib
from typing import Any, Callable, Generator, ContextManager

import pytest
import pytest_mock

from gpf_instance.gpf_instance import WGPFInstance
from wdae_tests.integration.testing import LiveServer


def _module_cleaner(root_module: str) -> None:
    modules_to_remove = []
    for module_name in sys.modules:
        if module_name == root_module or \
                module_name.startswith(f"{root_module}."):
            modules_to_remove.append(module_name)

    modules_to_remove = sorted(
        modules_to_remove, key=lambda mn: -mn.count("."))

    to_remove = {}
    for module_name in modules_to_remove:
        module = sys.modules[module_name]
        to_remove[module_name] = module

    for module_name, module in to_remove.items():
        del sys.modules[module_name]
        del module


@pytest.fixture
def wdae_django_setup(
    mocker: pytest_mock.MockerFixture,
    tmp_path: pathlib.Path
) -> Callable[[WGPFInstance, str], ContextManager[Any]]:

    @contextlib.contextmanager
    def builder(
        gpf: WGPFInstance, test_settings: str
    ) -> Generator[None, None, None]:
        from gpf_instance import gpf_instance

        mocker.patch.object(
            gpf_instance,
            "_GPF_INSTANCE",
            gpf)
        mocker.patch(
            "gpf_instance.gpf_instance.get_wgpf_instance",
            return_value=gpf)
        mocker.patch.dict(
            os.environ, {
                "DJANGO_SETTINGS_MODULE": test_settings,
            })

        import django.conf
        mocker.patch.object(
            django.conf.settings,
            "GPF_INSTANCE_CONFIG",
            gpf.instance_config)  # type: ignore

        import django
        django.setup()

        yield

        for app_name in [
                "utils",
                "gene_scores",
                "gene_sets",
                "datasets_api",
                "genotype_browser",
                "enrichment_api",
                "measures_api",
                "pheno_browser_api",
                "common_reports_api",
                "pheno_tool_api",
                "query_base",
                "users_api",
                "groups_api",
                "gpfjs",
                "query_state_save",
                "user_queries",
                "wdae.urls", ]:
            _module_cleaner(app_name)

        _module_cleaner(test_settings)
        _module_cleaner("oauth2_provider")
        _module_cleaner("gpf_instance")
        _module_cleaner("corsheaders")
        _module_cleaner("rest_framework")
        _module_cleaner("django")

    return builder


@pytest.fixture
def wdae_django_server(
    mocker: pytest_mock.MockerFixture,
    wdae_django_setup: Callable[[WGPFInstance, str], ContextManager[Any]]
) -> Callable[[WGPFInstance, str], ContextManager[LiveServer]]:

    @contextlib.contextmanager
    def builder(
        gpf: WGPFInstance, test_settings: str
    ) -> Generator[LiveServer, None, None]:

        with wdae_django_setup(gpf, test_settings):
            from django.core.management import execute_from_command_line
            execute_from_command_line(["wgpf", "migrate", "--skip-checks"])

            from gpf_instance import gpf_instance
            gpf_instance.reload_datasets(gpf)
            server = LiveServer("localhost:0")

            yield server

            server.stop()

    return builder

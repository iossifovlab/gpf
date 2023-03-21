# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
# type: ignore

import os
import sys
import contextlib

import pytest


class LiveServer:
    """The liveserver fixture.

    Copied from `pytest_django`: https://github.com/pytest-dev/pytest-django/

    This class is an exact copy of the one from the `pytest-django` plugin.
    The problem with using this class directly from the `pytest_django` package
    is that when I import the `pytest_django.live_server_helpers.LiveServer`
    class, it triggers the initialization of the `pytest_django` plugin,
    which initializes our Django application. And there is no way
    (or at least I was unable to find one) to control how the Django
    application is initialized.
    """

    def __init__(self, addr: str) -> None:
        from django.db import connections
        from django.test.testcases import LiveServerThread
        from django.test.utils import modify_settings

        liveserver_kwargs = {}

        connections_override = {}
        for conn in connections.all():
            # If using in-memory sqlite databases, pass the connections to
            # the server thread.
            if conn.vendor == "sqlite" and conn.is_in_memory_db():
                # Explicitly enable thread-shareability for this connection.
                conn.inc_thread_sharing()
                connections_override[conn.alias] = conn

        liveserver_kwargs["connections_override"] = connections_override
        from django.conf import settings

        if "django.contrib.staticfiles" in settings.INSTALLED_APPS:
            from django.contrib.staticfiles.handlers import StaticFilesHandler

            liveserver_kwargs["static_handler"] = StaticFilesHandler
        else:
            from django.test.testcases import _StaticFilesHandler

            liveserver_kwargs["static_handler"] = _StaticFilesHandler

        try:
            host, port = addr.split(":")
        except ValueError:
            host = addr
        else:
            liveserver_kwargs["port"] = int(port)
        self.thread = LiveServerThread(host, **liveserver_kwargs)

        self._live_server_modified_settings = modify_settings(
            ALLOWED_HOSTS={"append": host}
        )

        self.thread.daemon = True
        self.thread.start()
        self.thread.is_ready.wait()

        if self.thread.error:
            error = self.thread.error
            self.stop()
            raise error

    def stop(self) -> None:
        """Stop the server."""
        # Terminate the live server's thread.
        self.thread.terminate()
        # Restore shared connections' non-shareability.
        for conn in self.thread.connections_override.values():
            conn.dec_thread_sharing()

    @property
    def url(self) -> str:
        return f"http://{self.thread.host}:{self.thread.port}"

    def __str__(self) -> str:
        return self.url

    def __add__(self, other) -> str:
        return f"{self}{other}"

    def __repr__(self) -> str:
        return f"<LiveServer listening at {self.url}>"


def _module_cleaner(root_module):
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
def wdae_django_setup(mocker, tmp_path):

    @contextlib.contextmanager
    def builder(gpf, test_settings):
        from gpf_instance import gpf_instance

        mocker.patch.object(
            gpf_instance,
            "_GPF_INSTANCE",
            gpf)
        mocker.patch(
            "gpf_instance.gpf_instance.build_wgpf_instance",
            return_value=gpf)
        mocker.patch.dict(
            os.environ, {
                "DJANGO_SETTINGS_MODULE": test_settings,
            })

        import django.conf
        mocker.patch.object(
            django.conf.settings,
            "GPF_INSTANCE_CONFIG",
            gpf.instance_config)

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
                "user_queries", ]:
            _module_cleaner(app_name)

        _module_cleaner("django")
        _module_cleaner(test_settings)
        _module_cleaner("wdae.test_settings")
        _module_cleaner("wdae.settings")
        _module_cleaner("wdae.default_settings")
        _module_cleaner("oauth2_provider")
        _module_cleaner("gpf_instance")
        _module_cleaner("django")
        _module_cleaner("wdae_tests.integration")
        _module_cleaner("pytest_django")
    return builder


@pytest.fixture
def wdae_django_server(mocker, wdae_django_setup):

    @contextlib.contextmanager
    def builder(gpf, test_settings):

        with wdae_django_setup(gpf, test_settings):
            from django.core.management import execute_from_command_line
            execute_from_command_line(["wgpf", "migrate", "--skip-checks"])

            from gpf_instance import gpf_instance
            gpf_instance.reload_datasets(gpf)
            server = LiveServer("localhost:0")

            yield server

            server.stop()

    return builder

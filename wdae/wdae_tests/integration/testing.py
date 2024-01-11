
import pathlib
from typing import Optional, Any

from gpf_instance.gpf_instance import WGPFInstance

from dae.testing import setup_directories
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource, ReferenceGenome
from dae.genomic_resources.gene_models import \
    build_gene_models_from_resource, GeneModels
from dae.genomic_resources.repository import GenomicResourceRepo


def setup_wgpf_instance(
    out_path: pathlib.Path,
    reference_genome: Optional[ReferenceGenome] = None,
    reference_genome_id: Optional[str] = None,
    gene_models: Optional[GeneModels] = None,
    gene_models_id: Optional[str] = None,
    grr: Optional[GenomicResourceRepo] = None
) -> WGPFInstance:
    """Set up a GPF instance using prebuild genome, gene models, etc."""
    print(out_path)
    if not (out_path / "gpf_instance.yaml").exists():
        setup_directories(out_path, {"gpf_instance.yaml": "instance_id: test"})
    if reference_genome is None:
        if reference_genome_id is not None:
            assert grr is not None
            res = grr.get_resource(reference_genome_id)
            reference_genome = build_reference_genome_from_resource(res)
            reference_genome.open()
    if gene_models is None:
        if gene_models_id is not None:
            assert grr is not None
            res = grr.get_resource(gene_models_id)
            gene_models = build_gene_models_from_resource(res)
            gene_models.load()

    gpf = WGPFInstance.build(
        out_path / "gpf_instance.yaml",
        reference_genome=reference_genome, gene_models=gene_models,
        grr=grr)

    gpf.instance_dir = out_path  # type: ignore
    gpf.instance_config = out_path / "gpf_instance.yaml"  # type: ignore

    return gpf


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
        # pylint: disable=import-outside-toplevel
        from django.db import connections
        from django.test.testcases import LiveServerThread
        from django.test.utils import modify_settings

        liveserver_kwargs: dict[str, Any] = {}

        connections_override = {}
        for conn in connections.all():
            # If using in-memory sqlite databases, pass the connections to
            # the server thread.
            if conn.vendor == "sqlite" and \
                    conn.is_in_memory_db():  # type: ignore
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

    def __add__(self, other: Any) -> str:
        return f"{self}{other}"

    def __repr__(self) -> str:
        return f"<LiveServer listening at {self.url}>"

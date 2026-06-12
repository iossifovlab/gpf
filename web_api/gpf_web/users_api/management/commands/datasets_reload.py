"""Out-of-band rebuild of the dataset-permission hierarchy.

This command rebuilds the dataset-permission rows and the
``DatasetHierarchy`` relations by calling ``reload_datasets``.  It exists so
the rebuild runs *off* the request hot path (iossifovlab/gpf#925): the
gpf-web deploy runs it as a pre-start step, alongside DB migrations, instead
of paying the rebuild cost on the first request a fresh worker serves.
"""
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from gpf_instance.gpf_instance import (
    WGPFInstance,
    get_wgpf_instance,
    reload_datasets,
)


class Command(BaseCommand):
    """Rebuild the dataset-permission hierarchy out-of-band."""

    help = "Rebuild the dataset-permission hierarchy"

    def __init__(self, **kwargs: Any) -> None:
        self.gpf_instance: WGPFInstance = kwargs.pop("gpf_instance", None)
        BaseCommand.__init__(self, **kwargs)

    def handle(
        self, *args: Any, **options: Any,  # noqa: ARG002
    ) -> None:
        if self.gpf_instance is None:
            try:
                self.gpf_instance = get_wgpf_instance()
            except ValueError as exc:
                # Make a failed deploy pre-start step actionable instead of a
                # bare traceback (iossifovlab/gpf#925).
                self.stderr.write(
                    "could not load a GPF instance; "
                    "the dataset-permission hierarchy was NOT rebuilt",
                )
                raise CommandError(str(exc)) from exc
        reload_datasets(self.gpf_instance)

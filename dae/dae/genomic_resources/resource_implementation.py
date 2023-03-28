from __future__ import annotations
import logging
from typing import Optional, Callable, cast, Any
from abc import abstractmethod, ABC
from jinja2 import Template
from cerberus import Validator
from dae.task_graph.graph import Task

from .repository import GenomicResource

logger = logging.getLogger(__name__)


def get_base_resource_schema():
    return {
        "type": {"type": "string"},
        "meta": {
            "type": "dict",
            "allow_unknown": True,
            "schema": {
                "description": {"type": "string"},
                "labels": {"type": "dict", "nullable": True}
            }
        }
    }


class ResourceStatistics:
    """
    Base class for statistics.

    Subclasses should be created using mixins defined for each statistic type
    that the resource contains.
    """

    def __init__(self, resource_id: str):
        self.resource_id = resource_id

    @staticmethod
    def get_statistics_folder():
        return "statistics"

    @staticmethod
    @abstractmethod
    def build_statistics(
        genomic_resource: GenomicResource
    ) -> ResourceStatistics:
        raise NotImplementedError()


class GenomicResourceImplementation(ABC):
    """
    Base class used by resource implementations.

    Resources are just a folder on a repository. Resource implementations
    are classes that know how to use the contents of the resource.
    """

    config_validator: Optional[Callable[[dict], Any]] = None

    def __init__(self, genomic_resource: GenomicResource):
        self.resource = genomic_resource
        self.config: dict = self.resource.config
        self._statistics: Optional[ResourceStatistics] = None

    @property
    def resource_id(self):
        return self.resource.resource_id

    def get_config(self) -> dict:
        return self.config

    @property
    def files(self) -> set[str]:
        """Return a list of resource files the implementation utilises."""
        return set()

    @abstractmethod
    def calc_statistics_hash(self) -> bytes:
        """
        Compute the statistics hash.

        This hash is used to decide whether the resource statistics should be
        recomputed.
        """
        raise NotImplementedError()

    @abstractmethod
    def add_statistics_build_tasks(self, task_graph, **kwargs) -> list[Task]:
        """Add tasks for calculating resource statistics to a task graph."""
        raise NotImplementedError()

    @abstractmethod
    def calc_info_hash(self):
        """Compute and return the info hash."""
        raise NotImplementedError()

    @abstractmethod
    def get_info(self) -> str:
        """Construct the contents of the implementation's HTML info page."""
        raise NotImplementedError()

    def get_label(self, label):
        """Return a metadata label value."""
        metadata = self.config.get("meta")
        if metadata is None:
            return None

        labels = metadata.get("labels")
        if labels is None:
            return None

        return labels.get(label)

    def get_statistics(self) -> Optional[ResourceStatistics]:
        """Try and load resource statistics."""
        return None

    def reload_statistics(self):
        self._statistics = None
        return self.get_statistics()


class InfoImplementationMixin:
    """Mixin that provides generic template info page generation interface."""

    @abstractmethod
    def get_template(self) -> Template:
        raise NotImplementedError()

    @abstractmethod
    def _get_template_data(self):
        raise NotImplementedError()

    def get_info(self) -> str:
        """Construct the contents of the implementation's HTML info page."""
        template_data = self._get_template_data()
        return self.get_template().render(
            resource_id=self.resource.resource_id,  # type: ignore
            data=template_data,
            base=resource_template
        )


class ResourceConfigValidationMixin:
    """Mixin that provides validation of resource configuration."""

    @staticmethod
    @abstractmethod
    def get_schema():
        """Return schema to be used for config validation."""
        raise NotImplementedError()

    @classmethod
    def validate_and_normalize_schema(cls, config, resource) -> dict:
        """Validate the resource schema and return the normalized version."""
        # pylint: disable=not-callable
        validator = Validator(cls.get_schema())
        if not validator.validate(config):
            logger.error(
                "Resource %s of type %s has an invalid configuration. %s",
                resource.resource_id,
                resource.get_type(),
                validator.errors)
            raise ValueError("Invalid configuration")
        return cast(dict, validator.document)


resource_template = Template("""
<html>
<head>
<style>
h3,h4 {
    margin-top:0.5em;
    margin-bottom:0.5em;
}

{% block extra_styles %}{% endblock %}

</style>
</head>
<body>
<h1>{{ resource_id }}</h3>

{% block content %}
N/A
{% endblock %}

<div>
<span class="description">
{{ data["meta"] if data["meta"] else "N/A" }}
</span>
</div>


</body>
</html>
""")

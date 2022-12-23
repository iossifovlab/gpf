import logging
import textwrap
from typing import Optional, Callable, cast, Any
from abc import abstractmethod, ABC
from jinja2 import Template
from cerberus import Validator

from .repository import GenomicResource

logger = logging.getLogger(__name__)


def get_base_resource_schema():
    return {
        "type": {"type": "string"},
        "meta": {"type": "string"}
    }


class GenomicResourceImplementation(ABC):
    """
    Base class used by resource implementations.

    Resources are just a folder on a repository. Resource implementations
    are classes that know how to use the contents of the resource.
    """

    config_validator: Optional[Callable[[dict], Any]] = None
    STATISTICS_FOLDER = "statistics"

    def __init__(self, genomic_resource: GenomicResource):
        self.resource = genomic_resource
        self.config = self.resource.config

    def get_config(self) -> dict:
        return self.config

    @property
    @abstractmethod
    def files(self):
        """Return a list of resource files the implementation utilises."""

    @abstractmethod
    def calc_statistics_hash(self) -> str:
        """
        Compute the statistics hash.

        This hash is used to decide whether the resource statistics should be
        recomputed.
        """
        raise NotImplementedError()

    def add_statistics_build_tasks(self, task_graph) -> None:
        """Add tasks for calculating resource statistics to a task graph."""
        return None

    @abstractmethod
    def calc_info_hash(self):
        """Compute and return the info hash."""
        return None

    @abstractmethod
    def get_info(self) -> str:
        """Construct the contents of the implementation's HTML info page."""
        raise NotImplementedError()


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
            resource_id=self.resource.resource_id,
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
        return cast(Dict, validator.document)


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

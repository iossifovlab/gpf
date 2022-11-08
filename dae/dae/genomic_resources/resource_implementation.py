import logging
import textwrap
from typing import Dict, Optional, Callable, cast, Any
from abc import abstractmethod, ABC
from jinja2 import Template

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
    config_validator: Optional[Callable[[Dict], Any]] = None

    def __init__(self, genomic_resource: GenomicResource):
        self.resource = genomic_resource
        self.config = self.validate_and_normalize_schema(self.resource.config)

    def get_config(self) -> Dict:
        return cast(Dict, self.config)

    @staticmethod
    def get_template() -> Template:
        """
        Return a jinja2 template for GRR information page generation.

        The template must extend a template, which will be passed into
        the context as a variable named "base" and it must define a block
        named "content". The template must access it's passed info through
        a context variable named "data".
        """
        return Template(textwrap.dedent("""
            {% extends base %}
            {% block content %}
            No template defined
            {% endblock %}
        """))

    @staticmethod
    @abstractmethod
    def get_schema():
        """Return schema to be used for config validation."""
        raise NotImplementedError()

    def validate_and_normalize_schema(self, config) -> Dict:
        """Validate the resource schema and return the normalized version."""
        # pylint: disable=not-callable
        if self.config_validator is None:
            raise ValueError("No defined validator for class")
        validator = self.config_validator(self.get_schema())
        if not validator.validate(config):
            logger.error(
                "Resource %s of type %s has an invalid configuration. %s",
                self.resource.resource_id,
                self.resource.get_type(),
                validator.errors)
            raise ValueError(
                f"Resource {self.resource.resource_id} "
                f"of type {self.resource.get_type()} "
                f"has an invalid configuration: {validator.errors}"
            )
        return cast(Dict, validator.document)

    @abstractmethod
    def get_info(self):
        """Return dictionary to use as data in the template."""
        raise NotImplementedError()

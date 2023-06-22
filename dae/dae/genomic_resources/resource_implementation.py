from __future__ import annotations
import logging
from typing import Optional, cast
from abc import abstractmethod, ABC
from dataclasses import dataclass

from jinja2 import Template
from cerberus import Validator
from markdown2 import markdown

from dae.task_graph.graph import Task
from dae.utils.helpers import convert_size

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


class GenomicResourceImplementation(ABC):
    """
    Base class used by resource implementations.

    Resources are just a folder on a repository. Resource implementations
    are classes that know how to use the contents of the resource.
    """

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
    def calc_statistics_hash(self) -> str:
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

    def get_template_data(self):
        """
        Return a data dictionary to be used by the template.

        Will transform the description in the meta section using markdown.
        """
        template_data = self._get_template_data()

        @dataclass
        class FileEntry:
            """Provides an entry into manifest object."""

            name: str
            size: str
            md5: Optional[str]

        template_data["resource_files"] = [
            FileEntry(entry.name, convert_size(entry.size), entry.md5)
            for entry in
            self.resource.get_manifest().entries.values()]  # type: ignore
        return template_data

    def get_info(self) -> str:
        """Construct the contents of the implementation's HTML info page."""
        template_data = self.get_template_data()
        return self.get_template().render(
            resource=self.resource,  # type: ignore
            markdown=markdown,
            data=template_data,
            base=RESOURCE_TEMPLATE
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


RESOURCE_TEMPLATE = Template("""
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

<h1>Resource</h1>
<div>
<table border="1">
<tr><td><b>Id:</b></td><td>{{ resource.resource_id }}</td></tr>
<tr><td><b>Type:</b></td><td>{{ resource.get_type() }}</td></tr>
<tr>
<td><b>Summary:</b></td>
<td>
{%- set summary = resource.get_summary() -%}
{{
    summary if summary else "N/A"
}}</td>
</tr>
<tr>
<td><b>Description:</b></td>
<td>
{%- set description = resource.get_description() -%}
{{
    markdown(description) if description else "N/A"
}}</td>
</tr>
<tr>
<td><b>Labels:</b></td>
<td>
{% if resource.get_labels() %}
    <ul>
    {% for label, value in resource.get_labels().items() %}
        <li>{{ label }}: {{ value }}</li>
    {% endfor %}
    </ul>
{% endif %}
</td>
</tr>
</table>
</div>


{% block content %}
N/A
{% endblock %}


<h1>Files</h1>
<table>
<thead>
    <tr>
        <th>Filename</th>
        <th>Size</th>
        <th>md5</th>
    </tr>
</thead>
<tbody>
    {%- for entry in data["resource_files"] %}
    <tr>
        <td class="nowrap">
            <a href='{{entry.name}}'>{{entry.name}}</a>
        </td>
        <td class="nowrap">{{entry.size}}</td>
        <td class="nowrap">{{entry.md5}}</td>
    </tr>
    {%- endfor %}
</tbody>
</table>


</body>
</html>
""")

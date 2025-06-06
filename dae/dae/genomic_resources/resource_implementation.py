from __future__ import annotations

import logging
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, cast

from cerberus import Validator
from jinja2 import Template
from markdown2 import markdown

from dae.task_graph.graph import Task, TaskGraph
from dae.utils.helpers import convert_size

from .repository import GenomicResource

logger = logging.getLogger(__name__)


def get_base_resource_schema() -> dict[str, Any]:
    return {
        "type": {"type": "string"},
        "meta": {
            "type": "dict",
            "allow_unknown": True,
            "schema": {
                "description": {"type": "string"},
                "labels": {"type": "dict", "nullable": True},
            },
        },
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
    def get_statistics_folder() -> str:
        return "statistics"


class GenomicResourceImplementation(ABC):
    """
    Base class used by resource implementations.

    Resources are just a folder on a repository. Resource implementations
    are classes that know how to use the contents of the resource.
    """

    def __init__(self, genomic_resource: GenomicResource):
        self.resource = genomic_resource
        self.config: dict = self.resource.get_config()
        self._statistics: ResourceStatistics | None = None

    @property
    def resource_id(self) -> str:
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
        raise NotImplementedError

    @abstractmethod
    def add_statistics_build_tasks(self, task_graph: TaskGraph,
                                   **kwargs: Any) -> list[Task]:
        """Add tasks for calculating resource statistics to a task graph."""
        raise NotImplementedError

    @abstractmethod
    def calc_info_hash(self) -> bytes:
        """Compute and return the info hash."""
        raise NotImplementedError

    @abstractmethod
    def get_info(self, **kwargs: Any) -> str:
        """Construct the contents of the implementation's HTML info page."""
        raise NotImplementedError

    @abstractmethod
    def get_statistics_info(self, **kwargs: Any) -> str:
        """Construct the contents of the implementation's HTML
        statistics info page.
        """
        raise NotImplementedError

    def get_statistics(self) -> ResourceStatistics | None:
        """Try and load resource statistics."""
        return None

    def reload_statistics(self) -> ResourceStatistics | None:
        self._statistics = None
        return self.get_statistics()


class InfoImplementationMixin:
    """Mixin that provides generic template info page generation interface."""

    @dataclass
    class FileEntry:
        """Provides an entry into manifest object."""

        name: str
        size: str
        md5: str | None

    resource: GenomicResource

    def get_template(self) -> Template:
        return Template(textwrap.dedent("""
                {% extends base %}
                {% block content %}

                {% endblock %}
            """))

    def _get_template_data(self) -> dict:
        return {}

    def get_template_data(self) -> dict:
        """
        Return a data dictionary to be used by the template.

        Will transform the description in the meta section using markdown.
        """
        template_data = self._get_template_data()

        template_data["resource_files"] = [
            self.FileEntry(entry.name, convert_size(entry.size), entry.md5)
            for entry in self.resource.get_manifest().entries.values()
            if not entry.name.startswith("statistics")
            and entry.name != "index.html"]
        template_data["resource_files"].append(
            self.FileEntry("statistics/", "", ""))
        return template_data

    def get_statistics_template_data(self) -> dict:
        """
        Return a data dictionary to be used by the statistics template.

        Will transform the description in the meta section using markdown.
        """
        template_data = self._get_template_data()

        template_data["statistic_files"] = [
            self.FileEntry(
                entry.name.removeprefix("statistics/"),
                convert_size(entry.size),
                entry.md5,
            )
            for entry in self.resource.get_manifest().entries.values()
            if entry.name.startswith("statistics")]
        return template_data

    def get_info(self) -> str:
        """Construct the contents of the implementation's HTML info page."""
        template_data = self.get_template_data()
        return self.get_template().render(
            resource=self.resource,
            markdown=markdown,
            data=template_data,
            base=RESOURCE_TEMPLATE,
        )

    def get_statistics_info(self) -> str:
        """Construct the contents of the implementation's HTML info page."""
        template_data = self.get_statistics_template_data()
        return self.get_template().render(
            resource=self.resource,
            markdown=markdown,
            data=template_data,
            base=STATISTICS_TEMPLATE,
        )


class ResourceConfigValidationMixin:
    """Mixin that provides validation of resource configuration."""

    @staticmethod
    @abstractmethod
    def get_schema() -> dict:
        """Return schema to be used for config validation."""
        raise NotImplementedError

    @classmethod
    def validate_and_normalize_schema(
            cls, config: dict, resource: GenomicResource) -> dict:
        """Validate the resource schema and return the normalized version."""
        # pylint: disable=not-callable
        validator = Validator(cls.get_schema())
        if not validator.validate(config):
            logger.error(
                "Resource %s of type %s has an invalid configuration. %s",
                resource.resource_id,
                resource.get_type(),
                validator.errors)
            raise ValueError(f"Invalid configuration: {resource.resource_id}")
        return cast(dict, validator.document)


RESOURCE_TEMPLATE = Template("""
<html>
<head>
<style>
h3,h4 {
    margin-top:0.5em;
    margin-bottom:0.5em;
}
table {
    border-collapse: collapse;
}
th, td {
    padding: 10px;
}
th {
    font-size: 20px;
}
td {
    font-size: 18px;
}

.modal {
    display: none;
    position: fixed;
    z-index: 1;
    padding-top: 100px;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.5);
    justify-content: center;
}
.modal-content {
    margin: auto;
    display: block;
    width: 80%;
    max-width: 700px;
}
.close {
    float: right;
    font-size: 40px;
    font-weight: bold;
}
.close:hover,
.close:focus {
    color: #bbb;
    text-decoration: none;
    cursor: pointer;
}
{% block extra_styles %}{% endblock %}
</style>

<script>
    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("[data-modal-trigger]").forEach(function (trigger) {
            trigger.addEventListener("click", function () {
                var modalId = this.getAttribute("data-modal-trigger");
                var modal = document.getElementById(modalId);
                if (modal) {
                    modal.style.display = "block";
                    document.currentOpenModal = modal;
                }
            });
        });

        document.querySelectorAll(".close").forEach(function (closeButton) {
            closeButton.addEventListener("click", function () {
                this.closest(".modal").style.display = "none";
                document.currentOpenModal = null;
            });
        });

        window.addEventListener("click", function (event) {
            if (event.target.classList.contains("modal")) {
                event.target.style.display = "none";
                document.currentOpenModal = null;
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && document.currentOpenModal) {
                document.currentOpenModal.style.display = "none";
                document.currentOpenModal = null;
            }
        });
    });
</script>
</head>
    <body>
    <h1>Resource</h1>
    <div>
        <table border="1">
            <tr>
                <td>
                    <b>Id:</b>
                </td>
                <td>{{ resource.resource_id }}</td>
            </tr>
            <tr>
                <td>
                    <b>Type:</b>
                </td>
                <td>{{ resource.get_type() }}</td>
            </tr>
            <tr>
                <td>
                    <b>Version:</b>
                </td>
                <td>{{ resource.get_version_str() }}</td>
            </tr>
            <tr>
                <td><b>Summary:</b></td>
                <td>
                    <div>
                        <template shadowrootmode="open">
                            {%- set summary = resource.get_summary() -%}
                            {{
                                markdown(summary, extras=["tables"]) if summary else "N/A"
                            }}
                        </template>
                    </div>
                </td>
            </tr>
            <tr>
                <td>
                    <b>Description:</b>
                </td>
                <td>
                    <div>
                        <template shadowrootmode="open">
                            {%- set description = resource.get_description() -%}
                            {{
                                markdown(description, extras=["tables"]) if description else "N/A"
                            }}
                        </template>
                    </div>
                </td>
            </tr>
            <tr>
                <td>
                    <b>Labels:</b>
                </td>
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
                {% if entry.name == "statistics/" %}
                    <td class="nowrap">
                        <a href='statistics/index.html'>{{entry.name}}</a>
                    </td>
                {% else %}
                    <td class="nowrap">
                        <a href='{{entry.name}}'>{{entry.name}}</a>
                    </td>
                {% endif %}
                <td class="nowrap">{{entry.size}}</td>
                <td class="nowrap">{{entry.md5}}</td>
            </tr>
        {%- endfor %}
    </tbody>
    </table>
    </body>
</html>
""")  # noqa: E501

STATISTICS_TEMPLATE = Template(
"""
<html>
<head>
<style>
h3,h4 {
    margin-top:0.5em;
    margin-bottom:0.5em;
}
table {
    border-collapse: collapse;
}
th, td {
    padding: 10px;
}
th {
    font-size: 20px;
}
td {
    font-size: 18px;
}
{% block extra_styles %}{% endblock %}
</style>
</head>
<body>
    <table>
        <thead>
            <tr>
                <th>Filename</th>
                <th>Size</th>
                <th>md5</th>
            </tr>
        </thead>
        <tbody>
            {%- for entry in data["statistic_files"] %}
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

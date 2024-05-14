import logging
import textwrap
from typing import Any, Optional

from jinja2 import Environment, PackageLoader, Template
from markdown2 import markdown

from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.resource_implementation import (
    GenomicResourceImplementation,
    InfoImplementationMixin,
)
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class AnnotationPipelineImplementation(
    GenomicResourceImplementation,
    InfoImplementationMixin,
):
    """Resource implementation for annotation pipeline."""

    def __init__(self, resource: GenomicResource):
        if resource.get_type() != "annotation_pipeline":
            logger.error(
                "trying to open a resource %s of type "
                "%s as reference genome",
                resource.resource_id, resource.get_type())
            raise ValueError(f"wrong resource type: {resource.resource_id}")

        super().__init__(resource)

        self.raw: str = self.resource.get_file_content(
            self.resource.get_config()["filename"])
        self.pipeline: Optional[AnnotationPipeline] = None

    def get_info(self, **kwargs: Any) -> str:
        grr = kwargs["repo"]
        self.pipeline = build_annotation_pipeline(
            pipeline_config_str=self.raw,
            grr_repository=grr,
        )
        return InfoImplementationMixin.get_info(self)

    def get_template(self) -> Template:
        return Template(textwrap.dedent("""
            {% extends base %}
            {% block content %}
            {{data["content"]}}
            {% endblock %}
        """))

    def _get_template_data(self) -> dict[str, Any]:
        if self.pipeline is None:
            raise ValueError
        env = Environment(loader=PackageLoader("dae.annotation", "templates"))  # noqa
        doc_template = env.get_template("annotate_doc_pipeline_template.jinja")
        return {
            "content": doc_template.render(
                annotation_pipeline_info=self.pipeline.get_info(),
                preambule=self.pipeline.preambule,
                markdown=markdown,
            ),
        }

    @property
    def files(self) -> set[str]:
        return {self.resource.get_config()["filename"]}

    def calc_statistics_hash(self) -> bytes:
        return b"placeholder"

    def calc_info_hash(self) -> bytes:
        return b"placeholder"

    def add_statistics_build_tasks(self, task_graph: TaskGraph,   # noqa: ARG002
                                   **kwargs: Any) -> list[Task]:  # noqa: ARG002
        return []

import logging
import textwrap
from typing import Any
from urllib.parse import quote

from jinja2 import Environment, PackageLoader, Template
from markdown2 import markdown

from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.genomic_scores import GenomicScore
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
        self.pipeline: AnnotationPipeline | None = None

    def get_info(self, **kwargs: Any) -> str:
        grr = kwargs["repo"]
        self.pipeline = load_pipeline_from_yaml(self.raw, grr)
        return InfoImplementationMixin.get_info(self)

    def get_statistics_info(self, **kwargs: Any) -> str:
        grr = kwargs["repo"]
        self.pipeline = load_pipeline_from_yaml(self.raw, grr)
        return InfoImplementationMixin.get_statistics_info(self)

    def get_template(self) -> Template:
        return Template(textwrap.dedent("""
            {% extends base %}
            {% block content %}
            {{data["content"]}}
            {% endblock %}
        """))

    @property
    def _relative_prefix_to_root_dir(self) -> str:
        return "/".join([".."] * len(self.resource.resource_id.split("/")))

    def _make_resource_url(self, resource: GenomicResource) -> str:
        repo_url = self.resource.get_repo_url()
        res_url = resource.get_url()
        if repo_url in res_url:
            res_url = "/".join([
                self._relative_prefix_to_root_dir,
                resource.resource_id,
            ])
        else:
            logger.warning(
                "Referencing resource outside managed GRR %s",
                resource.get_id(),
            )
        return res_url

    def _make_histogram_url(
        self, score: GenomicScore, score_id: str,
    ) -> str | None:
        repo_url = self.resource.get_repo_url()
        hist_url = score.get_histogram_image_url(score_id)
        if hist_url is None:
            return None
        if repo_url in hist_url:
            hist_url = "/".join([
                self._relative_prefix_to_root_dir,
                score.resource.resource_id,
                quote(score.get_histogram_image_filename(score_id)),
            ])
        else:
            logger.warning(
                "Referencing resource outside managed GRR %s",
                score.resource.get_id(),
            )
        return hist_url

    def _get_template_data(self) -> dict[str, Any]:
        if self.pipeline is None:
            raise ValueError
        env = Environment(loader=PackageLoader("dae.annotation", "templates"))  # noqa
        doc_template = env.get_template("annotate_doc_pipeline_template.jinja")
        return {
            "content": doc_template.render(
                pipeline=self.pipeline,
                markdown=markdown,
                res_url=self._make_resource_url,
                hist_url=self._make_histogram_url,
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

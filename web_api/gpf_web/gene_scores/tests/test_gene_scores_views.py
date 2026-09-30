# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import pathlib
import textwrap
from collections.abc import Callable

import pytest
import pytest_mock
from django.test.client import Client
from gain.gene_scores.gene_scores import build_gene_score_from_resource
from gain.genomic_resources.cli import cli_manage
from gain.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from gain.genomic_resources.testing.builders import a_gene_score
from gpf_instance.gpf_instance import WGPFInstance
from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer
from utils.testing import setup_t4c8_instance


def _wgpf_instance_with_gene_score(
    root_path: pathlib.Path,
    mocker: pytest_mock.MockFixture,
    resource_name: str,
    realize: Callable[[pathlib.Path], None],
) -> WGPFInstance:
    """Build the t4c8 WGPF instance with one extra gene score wired in.

    ``realize`` writes the extra gene-score resource into the directory it
    is given; the resource is then added to the GRR and to
    ``gene_scores_db`` next to the t4c8 instance's own ``t4c8_score``, so
    both surface through the gene-scores endpoints.
    """
    t4c8_instance = setup_t4c8_instance(root_path)
    grr_dir = root_path / "t4c8_grr"

    realize(grr_dir / "gene_scores" / resource_name)
    cli_manage(["repo-repair", "-R", str(grr_dir), "-j", "1"])

    instance_filename = (
        pathlib.Path(t4c8_instance.dae_dir) / "gpf_instance.yaml"
    )
    instance_filename.write_text(
        instance_filename.read_text().replace(
            '  - "gene_scores/t4c8_score"',
            '  - "gene_scores/t4c8_score"\n'
            f'  - "gene_scores/{resource_name}"',
        ),
    )

    grr = build_genomic_resource_repository({
        "id": "t4c8_local",
        "type": "directory",
        "directory": str(grr_dir),
    })
    wgpf_instance = WGPFInstance.build(str(instance_filename), grr=grr)

    query_transformer = QueryTransformer(
        wgpf_instance.gene_scores_db,
        wgpf_instance.reference_genome.chromosomes,
        wgpf_instance.reference_genome.chrom_prefix,
    )
    response_transformer = ResponseTransformer(wgpf_instance.gene_scores_db)

    for target in (
        "gpf_instance.gpf_instance.get_wgpf_instance",
        "datasets_api.permissions.get_wgpf_instance",
        "query_base.query_base.get_wgpf_instance",
    ):
        mocker.patch(target, return_value=wgpf_instance)
    mocker.patch(
        "query_base.query_base.get_or_create_query_transformer",
        return_value=query_transformer,
    )
    mocker.patch(
        "query_base.query_base.get_or_create_response_transformer",
        return_value=response_transformer,
    )

    return wgpf_instance


@pytest.fixture
def categorical_wgpf_instance(
    tmp_path: pathlib.Path,
    db: None,  # ruff: ignore[unused-function-argument] ; enable the Django test database
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:
    """A WGPF instance carrying a number and a categorical gene score.

    The categorical gene score ``cat_score`` sits next to the t4c8
    instance's number score ``t4c8_score``.
    """
    def realize(resource_dir: pathlib.Path) -> None:
        (
            a_gene_score()
            .with_score(
                "cat_score", column_name="score", desc="categorical score")
            .with_histogram({"type": "categorical", "value_order": [1, 2, 3]})
            .with_data("""
                gene score
                t4    1
                c8    2
            """)
            .realize_into(resource_dir)
        )

    return _wgpf_instance_with_gene_score(
        tmp_path, mocker, "cat_score", realize)


@pytest.fixture
def described_wgpf_instance(
    tmp_path: pathlib.Path,
    db: None,  # ruff: ignore[unused-function-argument] ; enable the Django test database
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:
    """A WGPF instance with a gene score declaring every description field.

    ``desc_score`` carries a description and distinct small- and
    large-values descriptions, so a serializer that drops, swaps or
    substitutes any of them is caught.
    """
    def realize(resource_dir: pathlib.Path) -> None:
        resource_dir.mkdir(parents=True)
        (resource_dir / "genomic_resource.yaml").write_text(textwrap.dedent("""
            type: gene_score
            filename: scores.csv
            scores:
            - id: desc_score
              desc: a described score
              small_values_desc: low values are benign
              large_values_desc: high values are damaging
              histogram:
                type: number
                number_of_bins: 3
                x_log_scale: false
                y_log_scale: false
        """))
        (resource_dir / "scores.csv").write_text(textwrap.dedent("""\
            gene,desc_score
            t4,1
            c8,2
        """))

    return _wgpf_instance_with_gene_score(
        tmp_path, mocker, "desc_score", realize)


@pytest.mark.parametrize("url", [
    "/api/v3/gene_scores",
    "/api/v3/gene_scores/histograms",
])
def test_gene_scores_views_serialize_the_score_descriptions(
    user_client: Client,
    described_wgpf_instance: WGPFInstance,
    url: str,
) -> None:
    response = user_client.get(url)
    assert response.status_code == 200

    record = {d["score"]: d for d in response.json()}["desc_score"]
    gene_score = build_gene_score_from_resource(
        described_wgpf_instance.grr.get_resource("gene_scores/desc_score"))

    assert record["desc"] == "desc_score - a described score"
    assert record["small_values_desc"] == "low values are benign"
    assert record["large_values_desc"] == "high values are damaging"
    assert record["help"] == gene_score.build_score_help("desc_score")


def test_gene_scores_list_view_categorical(
    user_client: Client,
    categorical_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup instance
) -> None:
    url = "/api/v3/gene_scores"
    response = user_client.get(url)
    assert response.status_code == 200

    data = response.json()
    by_score = {d["score"]: d for d in data}
    assert set(by_score) == {"t4c8_score", "cat_score"}

    number_score = by_score["t4c8_score"]
    assert "bars" in number_score
    assert "bins" in number_score

    categorical_score = by_score["cat_score"]
    assert "bars" not in categorical_score
    assert "bins" not in categorical_score
    assert categorical_score["histogram"]["config"]["type"] == "categorical"


def test_gene_scores_histograms_view_categorical(
    user_client: Client,
    categorical_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup instance
) -> None:
    url = "/api/v3/gene_scores/histograms"
    response = user_client.get(url)
    assert response.status_code == 200

    data = response.json()
    by_score = {d["score"]: d for d in data}
    assert set(by_score) == {"t4c8_score", "cat_score"}

    assert (
        by_score["cat_score"]["histogram"]["config"]["type"] == "categorical"
    )


def test_gene_scores_list_view(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_scores"
    response = user_client.get(url)
    assert response.status_code == 200

    data = response.json()
    print([d["score"] for d in data])
    assert len(data) == 1

    for score in data:
        assert "desc" in score
        assert "score" in score
        assert "bars" in score
        assert "bins" in score


def test_gene_scores_partitions(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_scores/partitions"
    data = {
        "score": "t4c8_score",
        "min": 1.5,
        "max": 5.0,
    }

    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 3
    assert data["left"]["count"] == 0  # type: ignore
    assert data["right"]["count"] == 2  # type: ignore


@pytest.mark.parametrize("data", [
    {
        "score": "t4c8_score",
        "min": 1.5,
    },
    {
        "score": "t4c8_score",
        "max": 5.0,
    },
    {
        "score": "t4c8_score",
        "min": "non-float-value",
        "max": 5.0,
    },
    {
        "score": "t4c8_score",
        "min": 1.5,
        "max": "non-float-value",
    },
    {
        "score": "t4c8_score",
        "min": None,
        "max": 5.0,
    },
    {
        "score": "t4c8_score",
        "min": 1.5,
        "max": None,
    },
])
def test_gene_scores_partitions_bad_request(
    user_client: Client,
    data: dict[str, str | float | None],
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_scores/partitions"
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == 400


def test_gene_score_download(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_scores/download/t4c8_score"

    response = user_client.get(url)
    assert response.status_code == 200
    content = list(response.streaming_content)  # type: ignore
    assert len(content) > 0
    assert len(content[0].decode().split("\t")) == 2

    # This is due to a bug that downloaded empty list
    # the second time that request has been made

    response = user_client.get(url)
    assert response.status_code == 200
    assert len(list(response.streaming_content)) > 0  # type: ignore

# pylint: disable=W0621,C0114,C0116

import textwrap

import pytest

from dae.annotation.annotatable import Annotatable, Position, Region

# VCFAllele
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_inmemory_test_repository,
    convert_to_tab_separated,
)


@pytest.fixture(scope="module")
def grr() -> GenomicResourceRepo:
    return build_inmemory_test_repository({
        "cnvs": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: cnv_collection
                table:
                  filename: data.mem
                scores:
                - id: frequency
                  name: frequency
                  type: float
                  desc: some populaton frequency
                - id: collection
                  name: collection
                  type: str
                  desc: SSC or AGRE
                - id: affected_status
                  name: affected_status
                  type: str
                  allele_aggregator: join(,)
                  desc: |
                        shows if the child that has the de novo is
                        affected or unaffected
            """),
            "data.mem": convert_to_tab_separated("""
               chrom  pos_begin  pos_end  frequency  collection affected_status
               1      10         20       0.02       SSC        affected
               1      50         100      0.1        AGRE       affected
               2      1          2        0.00001    AGRE       unaffected
               2      16         20       0.3        SSC        affected
               2      200        203      0.0002     AGRE       unaffected
               15     16         20       0.2        AGRE       affected
            """)},
    })


@pytest.mark.parametrize("annotatable, cnv_count", [
    (Position("1", 15), 1),
    (Region("1", 15, 60), 2),
    (Region("1", 30, 40), 0),
])
def test_basic(
        annotatable: Annotatable,
        cnv_count: int, grr: GenomicResourceRepo) -> None:
    pipeline = load_pipeline_from_yaml(
        textwrap.dedent("""
            - cnv_collection: cnvs
            """),
        grr)

    atts = pipeline.annotate(annotatable)
    assert atts["count"] == cnv_count


@pytest.mark.parametrize("annotatable, cnv_count", [
    (Position("1", 15), 1),
    (Region("1", 15, 60), 1),
    (Region("1", 30, 40), 0),
])
def test_cnv_filter(
        annotatable: Annotatable, cnv_count: int,
        grr: GenomicResourceRepo) -> None:
    pipeline = load_pipeline_from_yaml(
        textwrap.dedent("""
            - cnv_collection:
                resource_id: cnvs
                cnv_filter: >
                  (cnv.attributes["frequency"] < 0.05 or
                  cnv.attributes["collection"] == "SSC") and
                  cnv.size > 2
            """),
        grr)

    atts = pipeline.annotate(annotatable)
    assert atts["count"] == cnv_count


@pytest.mark.parametrize(
    "annotatable, cnv_count, status, status2, collection", [
        (Position("1", 15), 1, "affected", "affected", "SSC"),
        (Region("1", 15, 60), 2,
         "affected,affected", "affected", "SSCAGRE"),
        (Region("1", 30, 40), 0, None, None, None),
    ])
def test_cnv_filter_and_attribute(
    annotatable: Annotatable, cnv_count: int,
    status: str, status2: str, collection: str,
    grr: GenomicResourceRepo,
) -> None:
    pipeline = load_pipeline_from_yaml(
        textwrap.dedent("""
            - cnv_collection:
                resource_id: cnvs
                cnv_filter: >
                  cnv.attributes["frequency"] < 0.05 or
                  cnv.attributes["collection"] == "AGRE"
                attributes:
                - count
                - name: status
                  source: "attribute.affected_status"
                - name: status2
                  source: "attribute.affected_status"
                  aggregator: max
                - source: "attribute.collection"
            """),
        grr)

    atts = pipeline.annotate(annotatable)
    assert "status" in atts
    assert "status2" in atts
    assert "attribute.collection" in atts

    assert atts["count"] == cnv_count
    assert atts["status"] == status
    assert atts["status2"] == status2
    assert atts["attribute.collection"] == collection

    status_info = pipeline.get_attribute_info("status")
    status2_info = pipeline.get_attribute_info("status2")
    collection_info = pipeline.get_attribute_info("attribute.collection")
    assert status_info is not None
    assert status2_info is not None
    assert collection_info is not None

    assert "aggregator: join(,)" in status_info.documentation
    assert "aggregator: max" in status2_info.documentation
    assert "aggregator: concatenate" in collection_info.documentation

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


@pytest.fixture(scope="module")
def larger_grr() -> GenomicResourceRepo:
    return build_inmemory_test_repository({
        "cnvs": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: cnv_collection
                table:
                  filename: data.mem
                scores:
                - id: frequency
                  name: frequency
                  type: int
                  desc: some populaton frequency
                - id: collection
                  name: collection
                  type: str
                  desc: SSC or AGRE
                - id: affected_status
                  name: "affected_status"
                  type: str
                  desc: |
                        shows if the child that has the de novo is
                        affected or unaffected
                - id: size
                  name: size
                  type: int
                  desc: size
            """),
            "data.mem": convert_to_tab_separated("""
chrom  pos_begin  pos_end  frequency  collection  affected_status  size
chr1   10         20       1          SSC         affected         100
chr1   50         100      1          AGRE        affected         130
chr1   1          2        1          AGRE        unaffected       250
chr1   16         20       3          SSC         affected         360
chr1   32         65       2          AGRE        unaffected       560
chr1   15         60       2          AGRE        affected         670
chr1   12         78       3          SSC        unaffected       550
chr1   16         35       4          AGRE        unaffected       300
chr1   25         67       5          SSc        affected         50
chr1   24         35       2          AGRE        affected         900
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


def test_cnv_aggregators(
    larger_grr: GenomicResourceRepo,
) -> None:
    pipeline = load_pipeline_from_yaml(
        textwrap.dedent("""
            - cnv_collection:
                resource_id: cnvs
                attributes:
                - count
                - name: size_max
                  source: "attribute.size"
                  aggregator: max
                - name: affected_status_count
                  source: "attribute.affected_status"
                  aggregator: count
                - name: size_median
                  source: "attribute.size"
                  aggregator: median
                - name: frequency_median
                  source: "attribute.frequency"
                  aggregator: median
                - name: frequency_list
                  source: "attribute.frequency"
                  aggregator: list
                - name: size_mode
                  source: "attribute.size"
                  aggregator: mode
                - name: collection_join
                  source: "attribute.collection"
                  aggregator: join(;)
            """),
        larger_grr)
    annotatable = Region("chr1", 1, 100)
    atts = pipeline.annotate(annotatable)

    assert "count" in atts
    assert "size_max" in atts
    assert "affected_status_count" in atts
    assert "size_median" in atts
    assert "frequency_median" in atts
    assert "frequency_list" in atts
    assert "size_mode" in atts
    assert "collection_join" in atts

    assert atts["count"] == 10
    assert atts["size_max"] == 900
    assert atts["affected_status_count"] == 10
    assert atts["size_median"] == 330.0
    assert atts["frequency_median"] == 2.0
    assert atts["frequency_list"] == [1, 1, 3, 2, 3, 4, 2, 5, 2, 1]
    assert atts["size_mode"] == 50
    assert atts["collection_join"] == \
        "AGRE;SSC;SSC;AGRE;SSC;AGRE;AGRE;SSc;AGRE;AGRE"

# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import Any

import pytest
import pyzstd

from dae.variants.variant import SummaryVariant, SummaryVariantFactory


@pytest.fixture
def sv_schema_f(summary_schema: dict[str, str]) -> dict:
    return {key: index for index, key in enumerate(summary_schema)}


@pytest.fixture
def sv_schema_b(summary_schema: dict[str, str]) -> dict:
    return dict(enumerate(summary_schema))


def test_summary_variant_from_record(
    sv1_records: list[dict[str, Any]],
) -> None:
    sv = SummaryVariantFactory.summary_variant_from_records(sv1_records)
    assert sv.summary_index == 12
    assert sv.chromosome == "chr1"
    assert sv.position == 213094429
    assert sv.end_position == 213094434

    assert sv.allele_count == 2
    assert len(sv.alt_alleles) == 1

    sa = sv.alt_alleles[0]
    assert sa.alternative == "T"
    assert sa.reference == "TTAATC"
    assert sa.get_attribute("af_allele_count") == 137
    assert sa.get_attribute("af_allele_freq") == 4.07
    assert sa.get_attribute("af_parents_called_count") == 1684
    assert sa.get_attribute("af_parents_called_percent") == 98.02
    assert sa.get_attribute("seen_as_denovo") is False
    assert sa.get_attribute("seen_in_status") == 3
    assert sa.get_attribute("family_variants_count") == 134

    assert {str(eg) for eg in sa.effect_genes} == {
        "RPS6KC1:intron", "RPS6KC1:5'UTR-intron",
        "RPS6KC1:non-coding-intron",
    }


def test_json_serialization_deserialization(sv: SummaryVariant) -> None:
    record = sv.to_record()
    data = json.dumps(record)

    record2 = json.loads(data)
    sv2 = SummaryVariantFactory.summary_variant_from_records(record2)
    assert sv == sv2

    assert len(data) == 4070  # 4075  # 4107, initially: 5909


def test_json_with_schema_serialization_deserialization(
    sv: SummaryVariant,
    sv_schema_f: dict,
    sv_schema_b: dict,
) -> None:
    record = sv.to_record()
    data = json.dumps([
        [
            [sv_schema_f.get(key, key), val]
            for key, val in r.items()
        ]
        for r in record
    ])

    record2 = json.loads(data)
    sv2 = SummaryVariantFactory.summary_variant_from_records([
        {
            sv_schema_b.get(p[0], p[0]): p[1]
            for p in r
        }
        for r in record2
    ])
    assert sv == sv2
    assert sv.effects == sv2.effects

    assert len(data) == 2930  # 2993  # 2999  # 3033


def test_json_zstd_serialization_deserialization(sv: SummaryVariant) -> None:
    record = sv.to_record()
    data = pyzstd.compress(json.dumps(record).encode("utf-8"), 10)

    record2 = json.loads(pyzstd.decompress(data))
    sv2 = SummaryVariantFactory.summary_variant_from_records(record2)
    assert sv == sv2

    assert len(data) == 979  # 980  # 985


def test_json_zstd_with_schema_serialization_deserialization(
    sv: SummaryVariant,
    sv_schema_f: dict,
    sv_schema_b: dict,
) -> None:
    record = sv.to_record()
    sdata = json.dumps([
        [
            [sv_schema_f.get(key, key), val]
            for key, val in r.items()
        ]
        for r in record
    ])
    data = pyzstd.compress(sdata.encode("utf-8"), 10)

    record2 = json.loads(pyzstd.decompress(data))
    sv2 = SummaryVariantFactory.summary_variant_from_records([
        {
            sv_schema_b.get(p[0], p[0]): p[1]
            for p in r
        }
        for r in record2
    ])
    assert sv == sv2

    assert len(data) == 721  # 773  # 794


ANNOTATION_FIELDS = [
    "phylop100way",
    "phylop30way",
    "phylop20way",
    "phylop7way",
    "phastcons100way",
    "phastcons30way",
    "phastcons20way",
    "phastcons7way",
    "cadd_raw",
    "cadd_phred",
    "fitcons_i6_merged",
    "linsight",
    "fitcons2_e067",
    "fitcons2_e068",
    "fitcons2_e069",
    "fitcons2_e070",
    "fitcons2_e071",
    "fitcons2_e072",
    "fitcons2_e073",
    "fitcons2_e074",
    "fitcons2_e081",
    "fitcons2_e082",
    "mpc",
    "ssc_freq",
    "exome_gnomad_v2_1_1_af_percent",
    "exome_gnomad_v2_1_1_ac",
    "exome_gnomad_v2_1_1_af",
    "exome_gnomad_v2_1_1_an",
    "exome_gnomad_v2_1_1_controls_ac",
    "exome_gnomad_v2_1_1_controls_an",
    "exome_gnomad_v2_1_1_non_neuro_ac",
    "exome_gnomad_v2_1_1_non_neuro_an",
    "exome_gnomad_v2_1_1_controls_af_percent",
    "exome_gnomad_v2_1_1_non_neuro_af_percent",
    "genome_gnomad_v2_1_1_af_percent",
    "genome_gnomad_v2_1_1_ac",
    "genome_gnomad_v2_1_1_af",
    "genome_gnomad_v2_1_1_an",
    "genome_gnomad_v2_1_1_controls_ac",
    "genome_gnomad_v2_1_1_controls_an",
    "genome_gnomad_v2_1_1_non_neuro_ac",
    "genome_gnomad_v2_1_1_non_neuro_an",
    "genome_gnomad_v2_1_1_controls_af_percent",
    "genome_gnomad_v2_1_1_non_neuro_af_percent",
    "genome_gnomad_v3_af_percent",
    "genome_gnomad_v3_ac",
    "genome_gnomad_v3_an",
]

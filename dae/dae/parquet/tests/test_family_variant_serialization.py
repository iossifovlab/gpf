# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from typing import Any

import numpy as np
import pytest

from dae.parquet.schema2.variant_serializers import (
    ZstdIndexedVariantsDataSerializer,
)
from dae.pedigrees.family import Family
from dae.pedigrees.loader import FamiliesLoader
from dae.testing import setup_pedigree
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant, SummaryVariantFactory

from .test_summary_variant_serialization import ANNOTATION_FIELDS, SV1


@pytest.fixture()
def meta() -> dict[str, Any]:
    return ZstdIndexedVariantsDataSerializer.build_serialization_meta(
        ANNOTATION_FIELDS,
    )


@pytest.fixture()
def fam1(tmp_path: pathlib.Path) -> Family:
    ped_path = setup_pedigree(tmp_path / "fam1.ped",
        textwrap.dedent("""
        familyId  personId  dadId   momId   sex  status      role
        f1        f1.mom    0       0       F    unaffected  mom
        f1        f1.dad    0       0       M    unaffected  dad
        f1        f1.p1     f1.mom  f1.dad  M    affected    prb
        f1        f1.p2     f1.mom  f1.dad  F    affected    prb
        f1        f1.p3     f1.mom  f1.dad  M    affected    prb
        f1        f1.p4     f1.mom  f1.dad  F    affected    prb
        """))
    return FamiliesLoader(str(ped_path)).load()["f1"]


FV1: dict[str, Any] = {
    "best_state": [[2, 2, 2, 2, 1], [0, 0, 0, 0, 1]],
    "family_id": "f1",
    "family_index": 13,
    "genotype": [[0, 0, 0, 0, 1], [0, 0, 0, 0, 0]],
    "inheritance_in_members": {
        "0": [256, 256, 2, 2, 2],
        "1": [256, 256, 128, 128, 4],
    },
    "summary_index": 12,
}


FAMILY_FIELDS = [
    "summary_index",
    "family_index",
    "family_id",
    "genotype",
    "best_state",
    "inheritance_in_members",
]


@pytest.fixture()
def sv() -> SummaryVariant:
    return SummaryVariantFactory.summary_variant_from_records(SV1)


@pytest.fixture()
def fv1(sv: SummaryVariant, fam1: Family) -> FamilyVariant:
    inheritance_in_members = {
        int(k): [Inheritance.from_value(inh) for inh in v]
        for k, v in FV1["inheritance_in_members"].items()
    }
    fv = FamilyVariant(
        sv,
        fam1,
        np.array(FV1["genotype"]),
        np.array(FV1["best_state"]),
        inheritance_in_members=inheritance_in_members,
    )
    fv.family_index = FV1["family_index"]
    return fv


def test_family_variant_serialization(
    meta: dict[str, Any],
    fv1: FamilyVariant,
) -> None:
    serializer = ZstdIndexedVariantsDataSerializer(meta)
    data = serializer.serialize_family(fv1)

    record = serializer.deserialize_family_record(data)
    assert record is not None
    assert record["family_id"] == "f1"
    assert record["summary_index"] == 12
    assert record["family_index"] == 13
    assert record["genotype"] == [[0, 0, 0, 0, 1], [0, 0, 0, 0, 0]]
    assert record["best_state"] == [[2, 2, 2, 2, 1], [0, 0, 0, 0, 1]]

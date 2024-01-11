# pylint: disable=W0621,C0114,C0116,W0212,W0613
from collections import Counter
from typing import Iterator, Any

import pytest
import pytest_mock

from box import Box
from dae.pheno_tool.tool import PhenoToolHelper
from dae.variants.attributes import Role


def mock_allele(
    effect: str, in_members: list[str]
) -> dict[str, Any]:
    return {"effects": {"types": {effect}}, "variant_in_members": in_members}


def mocked_query_variants(**kwargs: Any) -> Iterator[Box]:
    variants = [
        {
            "matched_alleles": [
                mock_allele("splice-site", ["fam2.prb", "fam3.prb"]),
                mock_allele("frame-shift", ["fam2.prb"]),
                mock_allele("nonsense", ["fam2.prb"]),
                mock_allele("no-frame-shift-newStop", ["fam2.prb"]),
                mock_allele("missense", ["fam1.prb"]),
                mock_allele("synonymous", ["fam1.prb", "fam3.prb"]),
            ]
        },
    ]

    for v in variants:
        yield Box(v)


def mocked_filter_transform(pheno_filters: list[str]) -> tuple:
    return None, None


mocked_study = Box(
    {
        "families": {
            "fam1": {
                "family_id": "fam1",
                "members_in_order": [
                    {"person_id": "fam1.dad", "role": Role.dad},
                    {"person_id": "fam1.mom", "role": Role.mom},
                    {"person_id": "fam1.prb", "role": Role.prb},
                    {"person_id": "fam1.sib", "role": Role.sib},
                ],
            },
            "fam2": {
                "family_id": "fam2",
                "members_in_order": [
                    {"person_id": "fam2.dad", "role": Role.dad},
                    {"person_id": "fam2.mom", "role": Role.mom},
                    {"person_id": "fam2.prb", "role": Role.prb},
                    {"person_id": "fam2.sib", "role": Role.sib},
                ],
            },
            "fam3": {
                "family_id": "fam3",
                "members_in_order": [
                    {"person_id": "fam3.dad", "role": Role.dad},
                    {"person_id": "fam3.mom", "role": Role.mom},
                    {"person_id": "fam3.prb", "role": Role.prb},
                    {"person_id": "fam3.sib", "role": Role.sib},
                ],
            },
        },
        "query_variants": mocked_query_variants,
        "query_transformer": {
            "_transform_filters_to_ids": mocked_filter_transform,
        }
    }
)

mocked_pheno = Box()


def test_genotype_data_persons() -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    assert helper.genotype_data_persons() == {
        "fam1.prb",
        "fam2.prb",
        "fam3.prb",
    }


def test_genotype_data_persons_family_filters() -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    assert helper.genotype_data_persons(family_ids=["fam2"]) == {"fam2.prb"}


def test_genotype_data_persons_roles() -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    assert helper.genotype_data_persons(roles=[Role.prb, Role.sib]) == {
        "fam1.prb",
        "fam2.prb",
        "fam3.prb",
        "fam1.sib",
        "fam2.sib",
        "fam3.sib",
    }


def test_genotype_data_persons_invalid_roles() -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    with pytest.raises(AssertionError):
        helper.genotype_data_persons(roles=Role.prb)  # type: ignore


def test_genotype_data_persons_invalid_family_ids() -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    with pytest.raises(AssertionError):
        helper.genotype_data_persons(family_ids="fam1")  # type: ignore


# def test_pheno_filter_persons(mocker):
#     mocker.spy(mocked_study.query_transformer, "_transform_filters_to_ids")
#     helper = PhenoToolHelper(mocked_study, mocked_pheno)
#     helper.pheno_filter_persons([1])
#     mocked_study.query_transformer._transform_filters_to_ids \
#         .assert_called_once_with([1])


# def test_pheno_filter_persons_none_or_empty():
#     helper = PhenoToolHelper(mocked_study, mocked_pheno)
#     assert helper.pheno_filter_persons(None) is None
#     assert helper.pheno_filter_persons(list()) is None


# def test_pheno_filter_persons_invalid_input_type():
#     helper = PhenoToolHelper(mocked_study, mocked_pheno)
#     with pytest.raises(AssertionError):
#         helper.pheno_filter_persons(dict)
#     with pytest.raises(AssertionError):
#         helper.pheno_filter_persons(tuple)


def test_genotype_data_variants() -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    variants = helper.genotype_data_variants(
        {
            "effect_types": [
                "splice-site",
                "frame-shift",
                "nonsense",
                "missense",
                "synonymous",
            ]
        },
        [
            "splice-site",
            "frame-shift",
            "nonsense",
            "missense",
            "synonymous",
        ]
    )

    assert variants.get("missense") == Counter({"fam1.prb": 1})
    assert variants.get("synonymous") == Counter(
        {"fam1.prb": 1, "fam3.prb": 1}
    )
    assert variants.get("splice-site") == Counter(
        {"fam2.prb": 1, "fam3.prb": 1}
    )
    assert variants.get("frame-shift") == Counter({"fam2.prb": 1})
    assert variants.get("nonsense") == Counter({"fam2.prb": 1})
    # assert variants.get("no-frame-shift-newStop") == Counter({"fam2.prb": 1})


def test_genotype_data_variants_invalid_data() -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    with pytest.raises(AssertionError):
        helper.genotype_data_variants(
            {"effectTypes": ["splice-site", "frame-shift"]},
            ["splice-site", "frame-shift", ]
        )


def test_genotype_data_variants_specific_effects() -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    variants = helper.genotype_data_variants(
        {"effect_types": ["missense", "synonymous"]},
        ["missense", "synonymous", ]
    )

    assert variants.get("missense") == Counter({"fam1.prb": 1})
    assert variants.get("synonymous") == Counter(
        {"fam1.prb": 1, "fam3.prb": 1}
    )


def test_genotype_data_variants_lgds() -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    variants = helper.genotype_data_variants(
        {"effect_types": ["LGDs"]}, ["LGDs", ])
    assert variants.get("LGDs") == Counter({"fam2.prb": 1, "fam3.prb": 1}), \
        variants


def test_genotype_data_variants_nonsynonymous() -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    variants = helper.genotype_data_variants(
        {"effect_types": ["nonsynonymous"]},
        ["nonsynonymous", ]
    )

    assert variants.get("nonsynonymous") == Counter(
        {"fam1.prb": 1, "fam2.prb": 1, "fam3.prb": 1}
    ), variants


def test_genotype_data_variants_lgds_mixed() -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    variants = helper.genotype_data_variants(
        {"effect_types": ["LGDs", "frame-shift", "splice-site"]},
        ["LGDs", "frame-shift", "splice-site", ]
    )

    assert variants.get("LGDs") == Counter({"fam2.prb": 1, "fam3.prb": 1})
    assert variants.get("frame-shift") == Counter({"fam2.prb": 1})
    assert variants.get("splice-site") == Counter(
        {"fam2.prb": 1, "fam3.prb": 1}
    )


def test_genotype_data_variants_family_filters(
    mocker: pytest_mock.MockerFixture
) -> None:
    helper = PhenoToolHelper(mocked_study, mocked_pheno)  # type: ignore
    mocker.spy(mocked_study, "query_variants")
    helper.genotype_data_variants(
        {"effect_types": ["LGDs"], "familyIds": {0: "fam1", 1: "fam2"}},
        ["LGDs", ]
    )

    mocked_study.query_variants.assert_called_once_with(
        effect_types=["LGDs"], familyIds={0: "fam1", 1: "fam2"}
    )

# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "fixture_name,person_ids,count",
    [
        ("backends/trios2_11600", None, 1),
        ("backends/trios2_11600", ["dad2"], 1),
        ("backends/trios2_11600", ["dad1"], 0),
        ("backends/trios2_11600", ["ch2"], 1),
        ("backends/trios2_11600", ["ch1"], 0),
        ("backends/trios2", ["mom1"], 8),
        ("backends/trios2", ["dad1"], 7),
        ("backends/trios2", ["mom2"], 7),
        ("backends/trios2", ["ch1"], 2),
        ("backends/trios2", ["ch2"], 2),
        ("backends/trios2", ["mom2", "ch2"], 8),
        ("backends/trios2", ["mom1", "dad1"], 9),
        ("backends/trios2", ["mom1"] * 10101 + ["dad1"], 9),
        ("backends/generated_people", None, 2),
        ("backends/generated_people", ["prb1"], 1),
        ("backends/generated_people", ["prb2"], 1),
        ("backends/generated_people", ["prb1", "prb2"], 2),
    ],
)
def test_fixture_query_by_person_ids(
    variants_impl, variants, fixture_name, person_ids, count
):
    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    actual_variants = vvars.query_variants(
        person_ids=person_ids, return_reference=False, return_unknown=False
    )
    actual_variants = list(actual_variants)
    print(actual_variants)
    assert len(actual_variants) == count

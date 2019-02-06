from __future__ import print_function, unicode_literals, absolute_import

import pytest


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_thrift",
])
@pytest.mark.parametrize("fixture_name,person_ids,count", [

    ("fixtures/generated_people", None, 2),
    ("fixtures/generated_people", ['prb1'], 1),
    ("fixtures/generated_people", ['prb2'], 1),
    ("fixtures/generated_people", ['prb1', 'prb2'], 2),
])
def test_fixture_query_by_person_ids(
        variants_impl, variants, fixture_name, person_ids, count):
    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        person_ids=person_ids,
        return_reference=True,
        return_unknown=True
    )
    vs = list(vs)
    print(vs)
    assert len(vs) == count

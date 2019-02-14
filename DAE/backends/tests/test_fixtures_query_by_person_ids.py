'''
Created on Jul 5, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_thrift",
])
@pytest.mark.parametrize("fixture_name,person_ids,count", [

    ("fixtures/trios2_11600", None, 2),
    ("fixtures/trios2_11600", ['dad2'], 1),
    ("fixtures/trios2_11600", ['dad1'], 0),
    ("fixtures/trios2_11600", ['ch2'], 1),
    ("fixtures/trios2_11600", ['ch1'], 0),
    ("fixtures/trios2", ['mom1'], 8),
    ("fixtures/trios2", ['dad1'], 7),
    ("fixtures/trios2", ['mom2'], 7),
    ("fixtures/trios2", ['ch1'], 2),
    ("fixtures/trios2", ['ch2'], 2),
    ("fixtures/trios2", ['mom2', 'ch2'], 8),
    ("fixtures/trios2", ['mom1', 'dad1'], 9),
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

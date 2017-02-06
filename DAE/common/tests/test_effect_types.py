'''
Created on Feb 6, 2017

@author: lubo
'''

import pytest
from common.query_base import EffectTypesBase


@pytest.fixture(scope='session')
def query_base(request):
    query = EffectTypesBase()
    return query


def test_build_effect_types(query_base):
    effect_types = "Frame-shift,Nonsense,Splice-site"

    res = query_base.build_effect_types(effect_types)
    assert res is not None
    assert ['frame-shift', 'nonsense', 'splice-site'] == res


def test_build_effect_types_lgds(query_base):
    effect_types = "LGDs"

    res = query_base.build_effect_types(effect_types)
    assert res is not None
    assert set(['frame-shift', 'nonsense', 'splice-site']) == set(res)


def test_build_effect_types_mixed(query_base):
    effect_types = "LGDs,CNV, noStart"

    res = query_base.build_effect_types(effect_types)
    assert res is not None
    assert set([
        'frame-shift', 'nonsense', 'splice-site',
        'CNV+', 'CNV-', 'noStart']) == set(res)


def test_build_effect_types_bad(query_base):
    effect_types = "LGDs,CNV, noStart, not-an-effect-type"

    with pytest.raises(AssertionError):
        query_base.build_effect_types(effect_types)

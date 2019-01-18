def test_can_get_test_study(test_study):
    assert test_study is not None


def test_can_get_all_variants(test_study):
    variants = test_study.query_variants()
    variants = list(variants)

    assert len(variants) == 2


def test_inheritance_trio_can_init(inheritance_trio_wrapper):
    assert inheritance_trio_wrapper is not None

def test_can_get_test_study(test_study):
    assert test_study is not None


def test_can_get_all_variants(test_study):
    variants = test_study.query_variants()
    variants = list(variants)

    assert len(variants) == 2

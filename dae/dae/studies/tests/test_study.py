def test_can_get_test_study(quads_f1):
    assert quads_f1 is not None


def test_can_get_all_variants(quads_f1):
    variants = quads_f1.query_variants()
    variants = list(variants)

    assert len(variants) == 3

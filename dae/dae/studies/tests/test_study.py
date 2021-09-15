import time


def test_can_get_test_study(quads_f1):
    assert quads_f1 is not None


def test_can_get_all_variants(quads_f1):
    variants = quads_f1.query_variants()
    variants = list(variants)

    assert len(variants) == 3


def test_can_query_effect_groups(quads_f1):
    variants = quads_f1.query_variants(effect_types=["noncoding"])
    variants = list(variants)

    assert len(variants) == 3

    no_variants = quads_f1.query_variants(effect_types=["lgds"])
    no_variants = list(no_variants)

    assert len(no_variants) == 0


def test_can_close_query(quads_f1):
    variants = quads_f1.query_variants()

    for v in variants:
        print(v)
        break

    variants.close()
    time.sleep(0.1)

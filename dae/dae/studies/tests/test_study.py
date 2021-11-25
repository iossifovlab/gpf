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


def test_can_query_person_sets(
    fixtures_gpf_instance, data_import, variants_impala
):
    genotype_study = fixtures_gpf_instance.get_genotype_data(
        "iossifov_we2014_test"
    )
    ps_collection = ("status", ["affected"])
    variants = genotype_study.query_variants(
        person_set_collection=ps_collection
    )

    variants = list(variants)
    assert len(variants) == 14
    ps_collection = ("status", ["unaffected"])
    variants = genotype_study.query_variants(
        person_set_collection=ps_collection
    )

    variants = list(variants)
    assert len(variants) == 2

    ps_collection = ("status", ["unaffected", "affected"])
    variants = genotype_study.query_variants(
        person_set_collection=ps_collection
    )
    assert len(variants) == 14


def test_can_close_query(quads_f1):
    variants = quads_f1.query_variants()

    for v in variants:
        print(v)
        break

    variants.close()
    time.sleep(0.1)

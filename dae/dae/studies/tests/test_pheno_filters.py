import pytest

FILTER_QUERY_CATEGORICAL = {
    "id": "Categorical",
    "measureType": "categorical",
    "role": "prb",
    "measure": "instrument1.categorical",
    "selection": {"selection": ["option2"]},
}

FILTER_QUERY_CONTINUOUS = {
    "id": "Continuous",
    "measureType": "continuous",
    "role": "prb",
    "measure": "instrument1.continuous",
    "selection": {"min": 3, "max": 4},
}

FILTER_QUERY_BOGUS = {
    "id": "some nonexistant measure",
    "measureType": "continuous",
    "role": "prb",
    "measure": "wrontinstrument.wrongmeasure",
    "selection": {"min": 3, "max": 4},
}

FILTER_QUERY_ORDINAL = {
    "id": "Ordinal",
    "measureType": "ordinal",
    "role": "prb",
    "measure": "instrument1.ordinal",
    "selection": {"min": 1, "max": 5},
}


@pytest.mark.parametrize(
    "pheno_query,variants_count",
    [
        ([FILTER_QUERY_CATEGORICAL], 3),
        ([FILTER_QUERY_CONTINUOUS], 3),
        ([FILTER_QUERY_CATEGORICAL, FILTER_QUERY_CONTINUOUS], 3),
    ],
)
def test_query_with_pheno_filters_work(
    quads_f1_genotype_data_group_wrapper, pheno_query, variants_count
):
    variants = quads_f1_genotype_data_group_wrapper.query_variants(
        phenoFilters=pheno_query
    )
    variants = list(variants)

    assert len(variants) == variants_count
    for variant in variants:
        for ph in pheno_query:
            assert variant[ph["measure"]] is not None


def test_query_with_pheno_filters_and_people_ids_filter(
    quads_f1_genotype_data_group_wrapper,
):
    pheno_query = [FILTER_QUERY_CONTINUOUS]

    variants = quads_f1_genotype_data_group_wrapper.query_variants(
        phenoFilters=pheno_query, person_ids=["mom1"]
    )

    variants = list(variants)
    assert len(variants) == 1


def test_query_with_bogus_pheno_filters_is_ignored(
    quads_f1_genotype_data_group_wrapper,
):
    pheno_query = [FILTER_QUERY_BOGUS]

    variants = quads_f1_genotype_data_group_wrapper.query_variants(
        phenoFilters=pheno_query
    )
    variants = list(variants)
    assert len(variants) == 0


def test_query_with_query_not_in_config_passes(
    quads_f1_genotype_data_group_wrapper,
):
    pheno_query = [FILTER_QUERY_ORDINAL]
    variants = quads_f1_genotype_data_group_wrapper.query_variants(
        phenoFilters=pheno_query
    )
    variants = list(variants)

    assert len(variants) == 3


def test_query_with_categorical_filter_opposing_roles(fake_study_wrapper):
    """If the filters are implemented properly, family "f1"
    whose dad and mom match the filters below should be
    used in the query, returning at least one variant belonging to "f1.prb"
    """

    categorical_filters = [
        {
            "id": "Categorical",
            "measureType": "categorical",
            "role": "dad",
            "measure": "i1.m5",
            "selection": {"selection": ["catB"]},
        },
        {
            "id": "Categorical",
            "measureType": "categorical",
            "role": "mom",
            "measure": "i1.m5",
            "selection": {"selection": ["catA"]},
        }
    ]
    variants = list(
        fake_study_wrapper.query_variants(phenoFilters=categorical_filters)
    )
    assert len(variants)

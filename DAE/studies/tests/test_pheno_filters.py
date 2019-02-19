from __future__ import unicode_literals

import pytest

pytestmark = pytest.mark.usefixtures("pheno_conf_path")

FILTER_QUERY_CATEGORICAL = {
    "id": "Categorical",
    "measureType": "categorical",
    "role": "prb",
    "measure": "instrument1.categorical",
    "selection": {
        "values": ["option2"]
    }
}

FILTER_QUERY_CONTINUOUS = {
    "id": "Continuous",
    "measureType": "continuous",
    "role": "prb",
    "measure": "instrument1.continuous",
    "selection": {
        "min": 3,
        "max": 4
    }
}

FILTER_QUERY_BOGUS = {
    "id": "some nonexistant measure",
    "measureType": "continuous",
    "role": "prb",
    "measure": "wrontinstrument.wrongmeasure",
    "selection": {
        "min": 3,
        "max": 4
    }
}

FILTER_QUERY_ORDINAL = {
    "id": "Ordinal",
    "measureType": "ordinal",
    "role": "prb",
    "measure": "instrument1.ordinal",
    "selection": {
        "min": 1,
        "max": 5
    }
}


@pytest.mark.parametrize("pheno_query", [
    [FILTER_QUERY_CATEGORICAL],
    [FILTER_QUERY_CONTINUOUS],
    [FILTER_QUERY_CATEGORICAL, FILTER_QUERY_CONTINUOUS],
])
def test_query_with_pheno_filters_work(quads_f1_dataset_wrapper, pheno_query):
    variants = quads_f1_dataset_wrapper.query_variants(phenoFilters=pheno_query)
    variants = list(variants)

    assert variants
    for variant in variants:
        for ph in pheno_query:
            assert variant[ph["measure"]] is not None


def test_query_with_pheno_filters_and_people_ids_filter(
        quads_f1_dataset_wrapper):
    pheno_query = [FILTER_QUERY_CONTINUOUS]
    print(type(quads_f1_dataset_wrapper))
    variants = quads_f1_dataset_wrapper\
        .query_variants(phenoFilters=pheno_query, people_ids=['mom1'])
    variants = list(variants)

    assert len(variants) == 0


def test_query_with_bogus_pheno_filters_raises(quads_f1_dataset_wrapper):
    pheno_query = [FILTER_QUERY_BOGUS]

    variants = quads_f1_dataset_wrapper \
        .query_variants(phenoFilters=pheno_query, people_ids=['mom1'])
    variants = list(variants)
    assert len(variants) == 0


def test_query_with_query_not_in_config(quads_f1_dataset_wrapper):
    pheno_query = [FILTER_QUERY_ORDINAL]
    variants = quads_f1_dataset_wrapper \
        .query_variants(phenoFilters=pheno_query)
    variants = list(variants)

    assert len(variants) == 0

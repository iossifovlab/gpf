import pytest

download_columns = [
    "family", "phenotype", "variant", "best", "fromparent", "inchild",
    "effect", "count", "geneeffect", "effectdetails", "weights", "freq",
    "continuous", "categorical", "ordinal", "raw"
]

summary_preview_columns = [
    "variant", "effect", "weights", "freq", "effect",
    "continuous", "categorical", "ordinal", "raw"
]

summary_download_columns = [
    "variant", "effect", "weights", "freq", "effect",
    "geneeffect", "effectdetails", "continuous",
    "categorical", "ordinal", "raw"
]


@pytest.fixture
def quads_f1_columns(wdae_gpf_instance):
    quads_f1 = wdae_gpf_instance.get_wdae_wrapper('quads_f1')
    return (quads_f1.config.genotype_browser.columns, \
        quads_f1.config.genotype_browser.column_groups)


@pytest.fixture
def preview_sources(quads_f1_columns):
    cols, col_groups = quads_f1_columns
    preview_columns = [
        "family", "variant", "genotype", "effect", "weights", "freq", "effect",
        "continuous", "categorical", "ordinal", "raw"
    ]


@pytest.fixture
def download_sources():
    pass


@pytest.fixture
def summary_preview_sources():
    pass


@pytest.fixture
def summary_download_sources():
    pass

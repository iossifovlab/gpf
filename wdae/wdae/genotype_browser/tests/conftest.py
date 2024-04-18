# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

download_columns = [
    "family", "phenotype", "variant", "best", "fromparent", "inchild",
    "effect", "count", "geneeffect", "effectdetails", "weights", "freq",
    "continuous", "categorical", "ordinal", "raw",
]

summary_preview_columns = [
    "variant", "effect", "weights", "freq", "effect",
    "continuous", "categorical", "ordinal", "raw",
]

summary_download_columns = [
    "variant", "effect", "weights", "freq", "effect",
    "geneeffect", "effectdetails", "continuous",
    "categorical", "ordinal", "raw",
]


@pytest.fixture()
def preview_sources():
    return [
        {"source": "family", "format": "%s"},
        {"source": "studyName", "format": "%s"},
        {"source": "location", "format": "%s"},
        {"source": "variant", "format": "%s"},
        {"source": "pedigree", "format": "%s"},
        {"source": "worstEffect", "format": "%s"},
        {"source": "genes", "format": "%s"},
        {"source": "LGD_rank", "format": "LGD %d"},
        {"source": "RVIS_rank", "format": "RVIS %d"},
        {"source": "pLI_rank", "format": "pLI %d"},
        {"source": "SSC-freq", "format": "SSC %.2f %%"},
        {"source": "EVS-freq", "format": "EVS %.2f %%"},
        {"source": "E65-freq", "format": "E65 %.2f %%"},
        {"source": "worstEffect", "format": "%s"},
        {"source": "genes", "format": "%s"},
        {"source": "instrument1.continuous", "role": "prb", "format": "%s"},
        {"source": "instrument1.categorical", "role": "prb", "format": "%s"},
        {"source": "instrument1.ordinal", "role": "prb", "format": "%s"},
        {"source": "instrument1.raw", "role": "prb", "format": "%s"},
    ]


@pytest.fixture()
def download_sources():
    return [
        {"name": "family id", "source": "family", "format": "%s"},
        {"source": "studyName", "format": "%s"},
        {"source": "phenotype", "format": "%s"},
        {"source": "location", "format": "%s"},
        {"source": "variant", "format": "%s"},
        {"source": "bestSt", "format": "%s"},
        {"source": "fromParentS", "format": "%s"},
        {"source": "inChS", "format": "%s"},
        {"source": "worstEffect", "format": "%s"},
        {"source": "genes", "format": "%s"},
        {"source": "counts", "format": "%s"},
        {"source": "geneEffect", "format": "%s"},
        {"source": "effectDetails", "format": "%s"},
        {"source": "LGD_rank", "format": "LGD %d"},
        {"source": "RVIS_rank", "format": "RVIS %d"},
        {"source": "pLI_rank", "format": "pLI %d"},
        {"source": "SSC-freq", "format": "SSC %.2f %%"},
        {"source": "EVS-freq", "format": "EVS %.2f %%"},
        {"source": "E65-freq", "format": "E65 %.2f %%"},
        {"source": "instrument1.continuous", "role": "prb", "format": "%s"},
        {"source": "instrument1.categorical", "role": "prb", "format": "%s"},
        {"source": "instrument1.ordinal", "role": "prb", "format": "%s"},
        {"source": "instrument1.raw", "role": "prb", "format": "%s"},
    ]


@pytest.fixture()
def summary_preview_sources():
    return [
        {"source": "location", "format": "%s"},
        {"source": "variant", "format": "%s"},
        {"source": "worstEffect", "format": "%s"},
        {"source": "genes", "format": "%s"},
        {"source": "LGD_rank", "format": "LGD %d"},
        {"source": "RVIS_rank", "format": "RVIS %d"},
        {"source": "pLI_rank", "format": "pLI %d"},
        {"source": "SSC-freq", "format": "SSC %.2f %%"},
        {"source": "EVS-freq", "format": "EVS %.2f %%"},
        {"source": "E65-freq", "format": "E65 %.2f %%"},
        {"source": "worstEffect", "format": "%s"},
        {"source": "genes", "format": "%s"},
        {"source": "instrument1.continuous", "role": "prb", "format": "%s"},
        {"source": "instrument1.categorical", "role": "prb", "format": "%s"},
        {"source": "instrument1.ordinal", "role": "prb", "format": "%s"},
        {"source": "instrument1.raw", "role": "prb", "format": "%s"},
    ]


@pytest.fixture()
def summary_download_sources():
    return [
        {"source": "location", "format": "%s"},
        {"source": "variant", "format": "%s"},
        {"source": "worstEffect", "format": "%s"},
        {"source": "genes", "format": "%s"},
        {"source": "LGD_rank", "format": "LGD %d"},
        {"source": "RVIS_rank", "format": "RVIS %d"},
        {"source": "pLI_rank", "format": "pLI %d"},
        {"source": "SSC-freq", "format": "SSC %.2f %%"},
        {"source": "EVS-freq", "format": "EVS %.2f %%"},
        {"source": "E65-freq", "format": "E65 %.2f %%"},
        {"source": "worstEffect", "format": "%s"},
        {"source": "genes", "format": "%s"},
        {"source": "geneEffect", "format": "%s"},
        {"source": "effectDetails", "format": "%s"},
        {"source": "instrument1.continuous", "role": "prb", "format": "%s"},
        {"source": "instrument1.categorical", "role": "prb", "format": "%s"},
        {"source": "instrument1.ordinal", "role": "prb", "format": "%s"},
        {"source": "instrument1.raw", "role": "prb", "format": "%s"},
    ]

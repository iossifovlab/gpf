from typing import cast

import pytest

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.effect_annotation.annotator import EffectAnnotator
from dae.genomic_resources.gene_models import Exon

from .mocks import ReferenceGenomeMock
from .mocks import AnnotatorMock


@pytest.fixture(scope="session")
def annotator() -> EffectAnnotator:
    return cast(
        EffectAnnotator,
        AnnotatorMock(
            cast(ReferenceGenome, ReferenceGenomeMock()))
    )


@pytest.fixture(scope="session")
def exons() -> list[Exon]:
    return [Exon(60, 70, 0), Exon(80, 90, 1), Exon(100, 110, 2)]


@pytest.fixture(scope="session")
def coding() -> list[Exon]:
    return [Exon(65, 70, 0), Exon(80, 90, 1), Exon(100, 110, 2)]

# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.variants_loaders.raw.loader import StoredAnnotationDecorator


@pytest.mark.parametrize(
    "filename,annotation",
    [
        ("vcf.vcf", "vcf-vcf-eff.txt"),
        ("vcf", "vcf-eff.txt"),
        ("vcf.vcf.gz", "vcf-vcf-gz-eff.txt"),
    ],
)
def test_build_annotation_filename(filename, annotation):

    assert (
        StoredAnnotationDecorator.build_annotation_filename(filename)
        == annotation
    )

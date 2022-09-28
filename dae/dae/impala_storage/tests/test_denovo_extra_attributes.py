# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.pedigrees.loader import FamiliesLoader
from dae.backends.dae.loader import DenovoLoader
from dae.backends.raw.loader import AnnotationPipelineDecorator


@pytest.fixture
def denovo_extra_attr_loader(
        fixture_dirname, gpf_instance_2013, annotation_pipeline_internal):

    families_filename = fixture_dirname("backends/iossifov_extra_attrs.ped")
    variants_filename = fixture_dirname("backends/iossifov_extra_attrs.tsv")

    families = FamiliesLoader.load_simple_families_file(families_filename)

    variants_loader = DenovoLoader(
        families, variants_filename, gpf_instance_2013.reference_genome)

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )

    return variants_loader


def test_denovo_extra_attributes(denovo_extra_attr_loader):

    loader = denovo_extra_attr_loader
    fvs = list(loader.family_variants_iterator())
    print(fvs)
    for fv in fvs:
        for fa in fv.alt_alleles:
            print(fa.attributes, fa.summary_attributes)
            assert "someAttr" in fa.attributes

    fv = fvs[0]
    for fa in fv.alt_alleles:
        print(fa, fa.attributes, fa.summary_attributes)
        assert "someAttr" in fa.attributes
        assert fa.get_attribute("someAttr") == "asdf"

    fv = fvs[-1]
    for fa in fv.alt_alleles:
        print(fa.attributes, fa.summary_attributes)
        assert "someAttr" in fa.attributes
        assert fa.get_attribute("someAttr") == "adhglsfh"

import textwrap
import pytest
import io

from dae.genomic_resources.testing import convert_to_tab_separated
from dae.pedigrees.loader import FamiliesLoader
from dae.variants.attributes import Sex, Role
from dae.variants.core import Allele

from dae.backends.raw.flexible_variant_loader import \
    flexible_variant_loader, \
    location_variant_to_vcf_transformer, \
    variant_to_variant_type


@pytest.fixture
def families():
    ped_content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
            familyId personId dadId	 momId	sex status role
            f1       f1.m     0      0      2   1      mom
            f1       f1.d     0      0      1   1      dad
            f1       f1.p1    f1.d   f1.m   1   2      prb
            f1       f1.s2    f1.d   f1.m   2   1      sib
            f2       f2.m     0      0      2   1      mom
            f2       f2.d     0      0      1   1      dad
            f2       f2.p1    f2.d   f2.m   2   2      prb
        """)))
    families = FamiliesLoader(ped_content).load()
    assert families is not None
    return families


@pytest.fixture
def denovo_short():
    content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        family_id  location      variant    bestState
        f1         15:80137554   ins(A)     2||2||1||2/0||0||1||0
        f2         3:56627768    del(4)     2||2||1/0||0||1
        f1         4:83276456    sub(C->T)  2||2||1||2/0||0||1||0
        """
    )))
    return content


def test_families_simple(families):
    assert families.persons["f1.m"].sex == Sex.female
    assert families.persons["f1.d"].sex == Sex.male

    assert families.persons["f1.m"].role == Role.mom
    assert families.persons["f1.d"].role == Role.dad


def test_denovo_short_simple(denovo_short):
    next(denovo_short)

    generator = flexible_variant_loader(
        denovo_short,
        in_header=["familyId", "location", "variant", "bestState"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=[],
        filters=[])

    results = list(generator)
    assert len(results) == 3


def test_denovo_short_location_variant_transformation(
        denovo_short, gpf_instance_2013):

    next(denovo_short)

    transformers = [
        location_variant_to_vcf_transformer(gpf_instance_2013.reference_genome)
    ]

    generator = flexible_variant_loader(
        denovo_short,
        in_header=["familyId", "location", "variant", "bestState"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers,
        filters=[])

    results = list(generator)
    assert len(results) == 3

    v = results[0]
    assert v["chrom"] == "15"
    assert v["pos"] == 80137553
    assert v["ref"] == "T"
    assert v["alt"] == "TA"

    v = results[1]
    assert v["chrom"] == "3"
    assert v["pos"] == 56627767
    assert v["ref"] == "AAAGT"
    assert v["alt"] == "A"

    v = results[2]
    assert v["chrom"] == "4"
    assert v["pos"] == 83276456
    assert v["ref"] == "C"
    assert v["alt"] == "T"


def test_denovo_short_variant_type_transformation(denovo_short):

    next(denovo_short)

    transformers = [
        variant_to_variant_type()
    ]

    generator = flexible_variant_loader(
        denovo_short,
        in_header=["familyId", "location", "variant", "bestState"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers,
        filters=[])

    results = list(generator)
    assert len(results) == 3

    v = results[0]
    assert v["variant_type"] == Allele.Type.small_insertion

    v = results[1]
    assert v["variant_type"] == Allele.Type.small_deletion

    v = results[2]
    assert v["variant_type"] == Allele.Type.substitution

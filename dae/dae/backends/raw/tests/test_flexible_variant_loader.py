import textwrap
import pytest
import io

from dae.genomic_resources.test_tools import convert_to_tab_separated
from dae.pedigrees.loader import FamiliesLoader
from dae.variants.attributes import Sex, Role
from dae.variants.core import Allele
from dae.utils.variant_utils import mat2str

from dae.backends.raw.flexible_variant_loader import \
    cnv_location_to_vcf_trasformer, \
    cnv_variant_to_variant_type, \
    cnv_dae_best_state_to_best_state, \
    cnv_person_id_to_best_state, \
    flexible_variant_loader, \
    location_variant_to_vcf_transformer, \
    variant_to_variant_type, \
    cnv_vcf_to_vcf_trasformer


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
    header = next(denovo_short)
    print(header)

    generator = flexible_variant_loader(
        denovo_short,
        in_header=["familyId", "location", "variant", "bestState"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=[])

    results = list(generator)
    assert len(results) == 3


def test_denovo_short_location_variant_transformation(
        denovo_short, gpf_instance_2013):

    header = next(denovo_short)
    print(header)

    transformers = [
        location_variant_to_vcf_transformer(gpf_instance_2013.reference_genome)
    ]

    generator = flexible_variant_loader(
        denovo_short,
        in_header=["familyId", "location", "variant", "bestState"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers)

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

    header = next(denovo_short)
    print(header)

    transformers = [
        variant_to_variant_type()
    ]

    generator = flexible_variant_loader(
        denovo_short,
        in_header=["familyId", "location", "variant", "bestState"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers)

    results = list(generator)
    assert len(results) == 3

    v = results[0]
    assert v["variant_type"] == Allele.Type.small_insertion

    v = results[1]
    assert v["variant_type"] == Allele.Type.small_deletion

    v = results[2]
    assert v["variant_type"] == Allele.Type.substitution


@pytest.fixture
def cnv_dae():
    content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        family_id  location               variant  best_state
        f1         1:1590681-1628197      CNV+     2||2||2||3
        f2         1:28298951-28369279    CNV-     2||2||1
        f1         X:22944530-23302214    CNV-     2||1||1||1
        f1         X:153576690-153779907  CNV+     2||1||2||2
        """
    )))
    return content


def test_cnv_dae_location(cnv_dae):
    next(cnv_dae)

    transformers = [
        cnv_location_to_vcf_trasformer()
    ]

    generator = flexible_variant_loader(
        cnv_dae,
        in_header=["familyId", "location", "variant", "bestState"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers)

    results = list(generator)
    assert len(results) == 4

    v = results[0]
    assert v["chrom"] == "1"
    assert v["pos"] == 1590681
    assert v["pos_end"] == 1628197

    v = results[1]
    assert v["chrom"] == "1"
    assert v["pos"] == 28298951
    assert v["pos_end"] == 28369279


def test_cnv_dae_variant_type(cnv_dae):
    next(cnv_dae)

    transformers = [
        cnv_variant_to_variant_type()
    ]

    generator = flexible_variant_loader(
        cnv_dae,
        in_header=["familyId", "location", "variant", "bestState"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers)

    results = list(generator)
    assert len(results) == 4

    v = results[0]
    assert v["variant_type"] == Allele.Type.large_duplication

    v = results[1]
    assert v["variant_type"] == Allele.Type.large_deletion


@pytest.mark.parametrize(
    "cnv_plus_values,cnv_minus_values,variant,expected", [
        (["CNV+"], ["CNV-"], "CNV+", Allele.Type.large_duplication),
        (["CNV+"], ["CNV-"], "CNV-", Allele.Type.large_deletion),
        (["GAIN"], ["LOSS"], "GAIN", Allele.Type.large_duplication),
        (["GAIN"], ["LOSS"], "LOSS", Allele.Type.large_deletion),
        (["Dup", "Dup_Germline"], ["Del", "Del_Germline"],
         "Dup_Germline", Allele.Type.large_duplication),
        (["Dup", "Dup_Germline"], ["Del", "Del_Germline"],
         "Dup", Allele.Type.large_duplication),
        (["Dup", "Dup_Germline"], ["Del", "Del_Germline"],
         "Del", Allele.Type.large_deletion),
        (["Dup", "Dup_Germline"], ["Del", "Del_Germline"],
         "Del_Germline", Allele.Type.large_deletion),
    ]
)
def test_cnv_variant_to_variant_type(
        cnv_plus_values, cnv_minus_values, variant, expected):

    transformer = cnv_variant_to_variant_type(
        cnv_plus_values, cnv_minus_values)

    result = transformer({"variant": variant})

    assert result["variant_type"] == expected


@pytest.mark.parametrize(
    "cnv_plus_values,cnv_minus_values,variant", [
        (["CNV+"], ["CNV-"], "CNV"),
    ]
)
def test_cnv_unexpeced_variant_to_variant_type(
        cnv_plus_values, cnv_minus_values, variant):

    transformer = cnv_variant_to_variant_type(
        cnv_plus_values, cnv_minus_values)
    with pytest.raises(ValueError):
        transformer({"variant": variant})


@pytest.mark.parametrize(
    "index,expected", [
        (0, "2221/0001"),
        (1, "221/001"),
        (2, "2111/0001"),
        (3, "2102/0010"),
    ]
)
def test_cnv_dae_best_state(
        families, cnv_dae, gpf_instance_2013,
        index, expected):

    genome = gpf_instance_2013.reference_genome
    next(cnv_dae)

    transformers = [
        cnv_location_to_vcf_trasformer(),
        cnv_variant_to_variant_type(),
        cnv_dae_best_state_to_best_state(families, genome)
    ]

    generator = flexible_variant_loader(
        cnv_dae,
        in_header=["family_id", "location", "variant", "best_state"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers)

    results = list(generator)
    assert len(results) == 4

    result = results[index]

    assert mat2str(result["best_state"]) == expected


@pytest.fixture
def cnv_person_id():
    content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        person_id  location               variant
        f1.s2      1:1590681-1628197      CNV+
        f2.p1      1:28298951-28369279    CNV-
        f1.s2      X:22944530-23302214    CNV-
        f1.p1      X:153576690-153779907  CNV+
        """
    )))
    return content


@pytest.mark.parametrize(
    "index,expected", [
        (0, "2221/0001"),
        (1, "221/001"),
        (2, "2111/0001"),
        (3, "2102/0010"),
    ]
)
def test_cnv_person_id_best_state(
        families, cnv_person_id, gpf_instance_2013,
        index, expected):

    genome = gpf_instance_2013.reference_genome
    next(cnv_person_id)

    transformers = [
        cnv_location_to_vcf_trasformer(),
        cnv_variant_to_variant_type(),
        cnv_person_id_to_best_state(families, genome)
    ]

    generator = flexible_variant_loader(
        cnv_person_id,
        in_header=["person_id", "location", "variant"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers)

    results = list(generator)
    assert len(results) == 4

    result = results[index]

    assert mat2str(result["best_state"]) == expected


@pytest.fixture
def cnv_vcf():
    content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        person_id  chr  pos         pos_end      variant
        f1.s2      1    1590681     1628197      CNV+
        f2.p1      1    28298951    28369279     CNV-
        f1.s2      X    22944530    23302214     CNV-
        f1.p1      X    153576690   153779907    CNV+
        """
    )))
    return content


@pytest.mark.parametrize(
    "index,expected", [
        (0, "2221/0001"),
        (1, "221/001"),
        (2, "2111/0001"),
        (3, "2102/0010"),
    ]
)
def test_cnv_vcf_position(
        families, cnv_vcf, gpf_instance_2013,
        index, expected):

    genome = gpf_instance_2013.reference_genome
    next(cnv_vcf)

    transformers = [
        cnv_vcf_to_vcf_trasformer(),
        cnv_variant_to_variant_type(),
        cnv_person_id_to_best_state(families, genome)
    ]

    generator = flexible_variant_loader(
        cnv_vcf,
        in_header=["person_id", "chrom", "pos", "pos_end", "variant"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers)

    results = list(generator)
    assert len(results) == 4

    result = results[index]

    assert mat2str(result["best_state"]) == expected

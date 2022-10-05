# pylint: disable=W0621,C0114,C0116,W0212,W0613
import io
import textwrap
import pytest

from dae.utils.variant_utils import mat2str
from dae.variants.core import Allele

from dae.genomic_resources.testing import convert_to_tab_separated
from dae.variants_loaders.raw.flexible_variant_loader import \
    flexible_variant_loader

from dae.variants_loaders.cnv.flexible_cnv_loader import \
    _cnv_location_to_vcf_trasformer, \
    _cnv_variant_to_variant_type, \
    _cnv_dae_best_state_to_best_state, \
    _cnv_person_id_to_best_state, \
    _cnv_vcf_to_vcf_trasformer, \
    flexible_cnv_loader


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
    next(cnv_dae)  # skip the header

    transformers = [
        _cnv_location_to_vcf_trasformer()
    ]

    generator = flexible_variant_loader(
        cnv_dae,
        in_header=["familyId", "location", "variant", "bestState"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers,
        filters=[])

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
    next(cnv_dae)  # skip header

    transformers = [
        _cnv_variant_to_variant_type()
    ]

    generator = flexible_variant_loader(
        cnv_dae,
        in_header=["familyId", "location", "variant", "bestState"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers,
        filters=[])

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

    transformer = _cnv_variant_to_variant_type(
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

    transformer = _cnv_variant_to_variant_type(
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
        _cnv_location_to_vcf_trasformer(),
        _cnv_variant_to_variant_type(),
        _cnv_dae_best_state_to_best_state(families, genome)
    ]

    generator = flexible_variant_loader(
        cnv_dae,
        in_header=["family_id", "location", "variant", "best_state"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers,
        filters=[])

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
        _cnv_location_to_vcf_trasformer(),
        _cnv_variant_to_variant_type(),
        _cnv_person_id_to_best_state(families, genome)
    ]

    generator = flexible_variant_loader(
        cnv_person_id,
        in_header=["person_id", "location", "variant"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers,
        filters=[])

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
        _cnv_vcf_to_vcf_trasformer(),
        _cnv_variant_to_variant_type(),
        _cnv_person_id_to_best_state(families, genome)
    ]

    generator = flexible_variant_loader(
        cnv_vcf,
        in_header=["person_id", "chrom", "pos", "pos_end", "variant"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers,
        filters=[])

    results = list(generator)
    assert len(results) == 4

    result = results[index]

    assert mat2str(result["best_state"]) == expected


def test_cnv_loader_simple(families, cnv_dae, gpf_instance_2013):

    generator = flexible_cnv_loader(
        cnv_dae, families, gpf_instance_2013.reference_genome,
        regions=[])
    result = list(generator)
    assert len(result) == 4

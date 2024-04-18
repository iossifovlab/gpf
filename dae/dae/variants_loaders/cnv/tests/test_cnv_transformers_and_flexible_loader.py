# pylint: disable=W0621,C0114,C0116,W0212,W0613
import io
import textwrap

import pytest

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.families_data import FamiliesData
from dae.testing import convert_to_tab_separated
from dae.utils.variant_utils import mat2str
from dae.variants.core import Allele
from dae.variants_loaders.cnv.flexible_cnv_loader import (
    _cnv_dae_best_state_to_best_state,
    _cnv_location_to_vcf_trasformer,
    _cnv_person_id_to_best_state,
    _cnv_variant_to_variant_type,
    _cnv_vcf_to_vcf_trasformer,
    flexible_cnv_loader,
)
from dae.variants_loaders.raw.flexible_variant_loader import (
    flexible_variant_loader,
)


@pytest.fixture()
def cnv_dae() -> io.StringIO:
    content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        family_id  location               variant  best_state
        f1         1:1590681-1628197      CNV+     2||2||2||3
        f2         1:28298951-28369279    CNV-     2||2||1
        f1         X:22944530-23302214    CNV-     2||1||1||1
        f1         X:153576690-153779907  CNV+     2||1||2||2
        """,
    )))
    return content


def test_cnv_dae_location(cnv_dae: io.StringIO) -> None:
    next(cnv_dae)  # skip the header

    transformers = [
        _cnv_location_to_vcf_trasformer(),
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


def test_cnv_dae_variant_type(cnv_dae: io.StringIO) -> None:
    next(cnv_dae)  # skip header

    transformers = [
        _cnv_variant_to_variant_type(),
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
    ],
)
def test_cnv_variant_to_variant_type(
    cnv_plus_values: list[str],
    cnv_minus_values: list[str],
    variant: str,
    expected: Allele.Type,
) -> None:

    transformer = _cnv_variant_to_variant_type(
        cnv_plus_values, cnv_minus_values)

    result = transformer({"variant": variant})

    assert result["variant_type"] == expected


@pytest.mark.parametrize(
    "cnv_plus_values,cnv_minus_values,variant", [
        (["CNV+"], ["CNV-"], "CNV"),
    ],
)
def test_cnv_unexpeced_variant_to_variant_type(
    cnv_plus_values: list[str],
    cnv_minus_values: list[str],
    variant: str,
) -> None:

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
    ],
)
def test_cnv_dae_best_state(
    families: FamiliesData,
    cnv_dae: io.StringIO,
    gpf_instance_2013: GPFInstance,
    index: int,
    expected: str,
) -> None:

    genome = gpf_instance_2013.reference_genome
    next(cnv_dae)

    transformers = [
        _cnv_location_to_vcf_trasformer(),
        _cnv_variant_to_variant_type(),
        _cnv_dae_best_state_to_best_state(families, genome),
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


@pytest.fixture()
def cnv_person_id() -> io.StringIO:
    content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        person_id    location               variant
        f1.s2        1:1590681-1628197      CNV+
        f1.p1;f1.s2  2:1590681-1628197      CNV+
        f2.p1        1:28298951-28369279    CNV-
        f1.s2        X:22944530-23302214    CNV-
        f1.p1        X:153576690-153779907  CNV+
        """,
    )))
    return content


@pytest.mark.parametrize(
    "index,expected", [
        (0, "2221/0001"),
        (1, "2211/0011"),
        (2, "221/001"),
        (3, "2111/0001"),
        (4, "2102/0010"),
    ],
)
def test_cnv_person_id_best_state(
    families: FamiliesData,
    cnv_person_id: io.StringIO,
    gpf_instance_2013: GPFInstance,
    index: int,
    expected: str,
) -> None:

    genome = gpf_instance_2013.reference_genome
    next(cnv_person_id)

    transformers = [
        _cnv_location_to_vcf_trasformer(),
        _cnv_variant_to_variant_type(),
        _cnv_person_id_to_best_state(families, genome),
    ]

    generator = flexible_variant_loader(
        cnv_person_id,
        in_header=["person_id", "location", "variant"],
        line_splitter=lambda ln: ln.strip("\n\r").split("\t"),
        transformers=transformers,
        filters=[])

    results = list(generator)
    assert len(results) == 5

    result = results[index]

    assert mat2str(result["best_state"]) == expected


@pytest.fixture()
def cnv_vcf() -> io.StringIO:
    content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        person_id  chr  pos         pos_end      variant
        f1.s2      1    1590681     1628197      CNV+
        f2.p1      1    28298951    28369279     CNV-
        f1.s2      X    22944530    23302214     CNV-
        f1.p1      X    153576690   153779907    CNV+
        """,
    )))
    return content


@pytest.mark.parametrize(
    "index,expected", [
        (0, "2221/0001"),
        (1, "221/001"),
        (2, "2111/0001"),
        (3, "2102/0010"),
    ],
)
def test_cnv_vcf_position(
    families: FamiliesData,
    cnv_vcf: io.StringIO,
    gpf_instance_2013: GPFInstance,
    index: int,
    expected: str,
) -> None:

    genome = gpf_instance_2013.reference_genome
    next(cnv_vcf)

    transformers = [
        _cnv_vcf_to_vcf_trasformer(),
        _cnv_variant_to_variant_type(),
        _cnv_person_id_to_best_state(families, genome),
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


def test_cnv_loader_simple(
    families: FamiliesData,
    cnv_dae: io.StringIO,
    gpf_instance_2013: GPFInstance,
) -> None:

    generator = flexible_cnv_loader(
        cnv_dae, families, gpf_instance_2013.reference_genome,
        regions=[])
    result = list(generator)
    assert len(result) == 4

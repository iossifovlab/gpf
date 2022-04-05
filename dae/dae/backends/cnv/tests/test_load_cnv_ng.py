import textwrap
import pytest
import io

from dae.genomic_resources.test_tools import convert_to_tab_separated
from dae.pedigrees.loader import FamiliesLoader

from dae.backends.cnv.loader import CNVLoader


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
def cnv_vcf_like():
    content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        person_id  chr  pos         pos_end      variant  extra
        f1.s2      1    1590681     1628197      CNV+     0
        f2.p1      1    28298951    28369279     CNV-     1
        """
    )))
    return content


def test_configure_cnv_loader_vcf_like_pos():
    header = ["person_id", "Chr", "Start", "End", "variant", "extra"]
    transformers = []

    CNVLoader._configure_cnv_location(
        header, transformers,
        cnv_chrom="Chr",
        cnv_start="Start",
        cnv_end="End"
    )

    assert header == [
        "person_id", "chrom", "pos", "pos_end", "variant", "extra"]


def test_configure_cnv_loader_vcf_like_pos_missmatch():

    header = ["person_id", "Chr", "Start", "End", "variant", "extra"]
    transformers = []

    with pytest.raises(ValueError):
        CNVLoader._configure_cnv_location(
            header, transformers,
            cnv_chrom="Chrom",
            cnv_start="Start",
            cnv_end="End"
        )


def test_configure_cnv_loader_location():
    header = ["person_id", "location", "variant", "extra"]
    transformers = []
    CNVLoader._configure_cnv_location(header, transformers)
    assert header == [
        "person_id", "location", "variant", "extra"]


def test_configure_cnv_loader_location_mismatch():
    header = ["person_id", "location", "variant", "extra"]
    transformers = []
    with pytest.raises(ValueError):
        CNVLoader._configure_cnv_location(
            header, transformers, cnv_location="Location")


def test_configure_cnv_loader_dae_best_state_default(
        families, gpf_instance_2013):

    header = ["family_id", "location", "variant", "best_state", "extra"]
    transformers = []

    CNVLoader._configure_cnv_best_state(
        header, transformers,
        families, gpf_instance_2013.reference_genome,
    )

    assert header == [
        "family_id", "location", "variant", "best_state", "extra"]


def test_configure_cnv_loader_dae_best_state(
        families, gpf_instance_2013):

    header = ["familyId", "location", "variant", "bestState", "extra"]
    transformers = []

    CNVLoader._configure_cnv_best_state(
        header, transformers,
        families, gpf_instance_2013.reference_genome,
        cnv_family_id="familyId",
        cnv_best_state="bestState",
    )

    assert header == [
        "family_id", "location", "variant", "best_state", "extra"]


def test_configure_cnv_loader_person_id(
        families, gpf_instance_2013):

    header = ["personId", "location", "variant", "extra"]
    transformers = []

    CNVLoader._configure_cnv_best_state(
        header, transformers,
        families, gpf_instance_2013.reference_genome,
        cnv_person_id="personId",
    )

    assert header == [
        "person_id", "location", "variant", "extra"]


def test_configure_cnv_loader_best_state_mixed(
        families, gpf_instance_2013):

    header = ["personId", "location", "variant", "bestState", "extra"]
    transformers = []

    with pytest.raises(ValueError):
        CNVLoader._configure_cnv_best_state(
            header, transformers,
            families, gpf_instance_2013.reference_genome,
            cnv_person_id="personId",
            cnv_best_state="bestSTate",
        )


def test_configure_cnv_loader_best_state_person_id_not_found(
        families, gpf_instance_2013):

    header = ["personId", "location", "variant", "extra"]
    transformers = []

    with pytest.raises(ValueError):
        CNVLoader._configure_cnv_best_state(
            header, transformers,
            families, gpf_instance_2013.reference_genome,
            cnv_person_id="person_id",
        )


def test_configure_cnv_loader_best_state_best_state_not_found(
        families, gpf_instance_2013):

    header = ["familyId", "location", "variant", "bestState", "extra"]
    transformers = []

    with pytest.raises(ValueError):
        CNVLoader._configure_cnv_best_state(
            header, transformers,
            families, gpf_instance_2013.reference_genome,
            cnv_family_id="familyId",
            cnv_best_state="best_state",
        )


def test_configure_cnv_loader_best_state_family_id_not_found(
        families, gpf_instance_2013):

    header = ["familyId", "location", "variant", "bestState", "extra"]
    transformers = []

    with pytest.raises(ValueError):
        CNVLoader._configure_cnv_best_state(
            header, transformers,
            families, gpf_instance_2013.reference_genome,
            cnv_family_id="family_id",
            cnv_best_state="bestState",
        )

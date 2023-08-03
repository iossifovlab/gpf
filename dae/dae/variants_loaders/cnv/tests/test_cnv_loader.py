# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any
from pathlib import Path
import numpy as np
import pytest
from dae.genomic_resources.testing import setup_denovo, setup_pedigree
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing.acgt_import import acgt_gpf
from dae.variants_loaders.cnv.loader import CNVLoader
from dae.pedigrees.loader import FamiliesLoader


@pytest.fixture(scope="module")
def gpf_instance(tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("acgt_instance")
    gpf_instance = acgt_gpf(root_path)
    return gpf_instance


@pytest.fixture(scope="module")
def cnv_ped(tmp_path_factory: pytest.TempPathFactory) -> Any:
    root_path = tmp_path_factory.mktemp("cnv_ped_variants")
    ped_path = setup_pedigree(
        root_path / "cnv_data" / "in.ped",
        """
        familyId  personId  dadId  momId  sex  status  role
        f1        f1.mo     0      0      2    1       mom
        f1        f1.fa     0      0      1    1       dad
        f1        f1.p1     f1.fa  f1.mo  1    2       prb
        f1        f1.s1     f1.fa  f1.mo  2    1       sib
        f2        f2.mo     0      0      2    1       mom
        f2        f2.fa     0      0      1    1       dad
        f2        f2.p1     f2.fa  f2.mo  1    2       prb
        """)

    return ped_path


@pytest.fixture(scope="module")
def variants_file(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("acgt_instance")
    cnv_path = setup_denovo(
        root_path / "cnv_data" / "in.tsv",
        """
        family_id location    variant  best_state
        f1        chr1:1-20   CNV+     2||2||2||3
        f1        chr1:31-50  CNV-     2||2||2||1
        f2        chr2:51-70  CNV+     2||2||3
        f2        chr2:81-100 CNV-     2||2||1
        """)

    return cnv_path


def test_cnv_loader(
        variants_file: Path,
        cnv_ped: Any,
        gpf_instance: GPFInstance
) -> None:
    families = FamiliesLoader.load_simple_families_file(cnv_ped)
    assert families is not None

    loader = CNVLoader(
        families, [str(variants_file)], gpf_instance.reference_genome,
        params={
            "cnv_family_id": "family_id",
            "cnv_best_state": "best_state"
        })

    svs = []
    for sv, fvs in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)

    assert len(svs) == 4


@pytest.fixture(scope="module")
def summary_variants_duplication(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("acgt_instance")
    cnv_path = setup_denovo(
        root_path / "cnv_data" / "in.tsv",
        """
        family_id location    variant  best_state
        f1        chr1:1-20   CNV+     2||2||2||3
        f1        chr1:31-50  CNV-     2||2||2||1
        f2        chr2:51-70  CNV+     2||2||3
        f2        chr2:81-100 CNV-     2||2||1
        f2        chr1:31-50  CNV-     2||2||1
        """)

    return cnv_path


def test_cnv_loader_avoids_summary_variants_duplication(
        summary_variants_duplication: Path,
        cnv_ped: Any,
        gpf_instance: GPFInstance
) -> None:
    families = FamiliesLoader.load_simple_families_file(cnv_ped)
    assert families is not None

    loader = CNVLoader(
        families, [
            str(summary_variants_duplication)
        ], gpf_instance.reference_genome,
        params={
            "cnv_family_id": "family_id",
            "cnv_best_state": "best_state"
        })

    svs = []
    fvs: list[Any] = []
    for sv, fvs_ in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)
        for fv in fvs_:
            fvs.append(fv)

    print(len(fvs))
    assert len(svs) == 4
    assert len(fvs) == 5


# Here we have more columns, Chr, Start, Stop, Del/Dup, person id are
# important(see params)
@pytest.fixture(scope="module")
def variants_file_alt(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("acgt_instance")
    cnv_path = setup_denovo(
        root_path / "cnv_data" / "in.tsv",
        """
        person_id  chr    start      stop      variant_type
        f1.mo      chr15  30943512   31245880  Dup_Germline
        f2.mo      chr15  20005287   32620127  Dup
        f1.fa      chr1   30490438   30804020  Del_Germline
        f2.fa      chr1   1620860    1684472   Del
        f1.fa      chr1   112543347  113721397 Dup_Germline
        f1.mo      chr15   22750305   29050198 Dup
        """)

    return cnv_path


def test_cnv_loader_alt(
        variants_file_alt: Path,
        cnv_ped: Path,
        gpf_instance: GPFInstance
) -> None:
    families = FamiliesLoader.load_simple_families_file(cnv_ped)
    assert families is not None

    loader = CNVLoader(
        families, [str(variants_file_alt)], gpf_instance.reference_genome,
        params={
            "cnv_chrom": "chr",
            "cnv_start": "start",
            "cnv_end": "stop",
            "cnv_variant_type": "variant_type",
            "cnv_plus_values": ["Dup", "Dup_Germline"],
            "cnv_minus_values": ["Del", "Del_Germline"],
            "cnv_person_id": "person_id"
        }
    )

    svs = []
    for sv, fvs in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)

    assert len(svs) == 6


@pytest.fixture(scope="module")
def variants_file_best_state(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("acgt_instance")
    cnv_path = setup_denovo(
        root_path / "cnv_data" / "in.tsv",
        """
        person_id  chr      start       stop        variant_type
        f1.mo	   chr15	30943512	31245880	Dup
        f1.fa	   chr15	30943512	31245880	Dup
        f1.p1	   chr15	30943512	31245880	Dup
        f1.s1	   chr15	30943512	31245880	Dup
        """)

    return cnv_path


def test_cnv_loader_alt_best_state(
        variants_file_best_state: Path,
        cnv_ped: Any,
        gpf_instance: GPFInstance
) -> None:
    families = FamiliesLoader.load_simple_families_file(cnv_ped)
    assert families is not None

    loader = CNVLoader(
        families, [str(variants_file_best_state)],
        gpf_instance.reference_genome,
        params={
            "cnv_chrom": "chr",
            "cnv_start": "start",
            "cnv_end": "stop",
            "cnv_variant_type": "variant_type",
            "cnv_plus_values": ["Dup", "Dup_Germline"],
            "cnv_minus_values": ["Del", "Del_Germline"],
            "cnv_person_id": "person_id"
        }
    )

    svs = []
    fvs: list[Any] = []
    for sv, _fvs in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)
        for fv in _fvs:
            fvs.append(fv)

    assert len(svs) == 1
    assert len(fvs) == 4
    print(fvs[0].best_state)


@pytest.fixture(scope="module")
def variants_file_alt_2(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("acgt_instance")
    cnv_path = setup_denovo(
        root_path / "cnv_data" / "in.tsv",
        """
        person_id  location                 variant
        f1.mo      chr16:24714401-27418700	duplication
        f2.fa      chr15:98936210-99462439	duplication
        f1.fa      chr16:2292001-2295900	deletion
        f2.p1      chr16:29532431-30188900	deletion
        f1.s1      chr16:51934201-51943700	deletion
        f1.fa      chr16:29545142-30188900	deletion
        f1.s1      chr16:3424701-3455500	deletion
        f2.mo      chr15:92940901-92945600	deletion
        f2.mo      chr16:29536287-30190504	duplication
        f1.fa      chr16:29545142-30191700	duplication
        f2.mo      chr15:94193172-94206260	deletion
        f1.fa      chr15:93755201-93797400	deletion
        f1.s1      chr16:29523777-30189981	duplication
        f2.mo      chr16:8806101-9152412	duplication
        f1.s1      chr15:74881560-74909392	duplication
        f1.p1      chr16:29545142-30190504	deletion
        f2.fa      chr16:28743701-29052769	deletion
        f2.mo      chr16:77909701-77998815	deletion
        f1.fa      chr16:29545142-30189981	deletion
        f1.mo      chr15:95927401-96080335	duplication
        f1.mo      chr16:29545142-30189981	deletion
        f1.fa      chr16:29547579-30188800	deletion
        f1.mo      chr16:628401-654300	    deletion
        f2.fa      chr16:8715232-9208187	duplication
        f1.fa      chr16:32304-1264400	    deletion
        f1.p1      chr15:93345472-93448771	deletion
        f1.s1      chr16:29536287-30189981	duplication
        f2.mo      chr16:81031601-81210700	deletion
        f2.fa      chr16:61786101-61802698	duplication
        f2.mo      chr16:76212301-76482200	deletion
        """)

    return cnv_path


def test_cnv_loader_alt_2(
        variants_file_alt_2: Path,
        cnv_ped: Any,
        gpf_instance: GPFInstance
) -> None:
    families = FamiliesLoader.load_simple_families_file(cnv_ped)
    assert families is not None

    loader = CNVLoader(
        families, [str(variants_file_alt_2)], gpf_instance.reference_genome,
        params={
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["duplication"],
            "cnv_minus_values": ["deletion"],
            "cnv_person_id": "person_id"
        }
    )

    svs = []
    fvs: list[Any] = []
    for sv, _fvs in loader.full_variants_iterator():
        print(sv, fvs)
        svs.append(sv)
        for fv in _fvs:
            fvs.append(fv)

    assert len(svs) == 29
    assert len(fvs) == 30


@pytest.fixture
def simple_cnv_loader(gpf_instance_2013, fixture_dirname):
    def ctor(ped_filename, cnf_filename, additional_params):
        families_file = fixture_dirname(ped_filename)
        families = FamiliesLoader.load_simple_families_file(families_file)
        assert families is not None

        params = additional_params
        cnv_filename = fixture_dirname(cnf_filename)
        return CNVLoader(
            families, [cnv_filename],
            genome=gpf_instance_2013.reference_genome, params=params,
        )
    return ctor


adjust_chrom_params = (
    "ped_filename, input_filename, params",
    [
        ("backends/cnv_ped.txt", "backends/cnv_variants.txt",
            {
                "add_chrom_prefix": "chr",
                "cnv_family_id": "familyId",
                "cnv_best_state": "bestState"
            }),
        ("backends/cnv_ped.txt", "backends/cnv_variants_chr.txt",
            {
                "del_chrom_prefix": "chr",
                "cnv_family_id": "familyId",
                "cnv_best_state": "bestState"
            }),
    ],
)


@pytest.mark.parametrize(*adjust_chrom_params)
def test_chromosomes_have_adjusted_chrom(simple_cnv_loader,
                                         ped_filename, input_filename, params):
    loader = simple_cnv_loader(ped_filename, input_filename, params)

    prefix = params.get("add_chrom_prefix", "")
    assert loader.chromosomes == [f"{prefix}1", f"{prefix}X"]


@pytest.mark.parametrize(*adjust_chrom_params)
def test_variants_have_adjusted_chrom(simple_cnv_loader,
                                      ped_filename, input_filename, params):
    loader = simple_cnv_loader(ped_filename, input_filename, params)
    is_add = "add_chrom_prefix" in params

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    for summary_variant, _ in variants:
        if is_add:
            assert summary_variant.chromosome.startswith("chr")
        else:
            assert not summary_variant.chromosome.startswith("chr")


@pytest.mark.parametrize(*adjust_chrom_params)
def test_reset_regions_with_adjusted_chrom(simple_cnv_loader, ped_filename,
                                           input_filename, params):
    loader = simple_cnv_loader(ped_filename, input_filename, params)
    prefix = params.get("add_chrom_prefix", "")
    regions = [f"{prefix}X"]

    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    unique_chroms = np.unique([sv.chromosome for sv, _ in variants])
    assert (unique_chroms == regions).all()

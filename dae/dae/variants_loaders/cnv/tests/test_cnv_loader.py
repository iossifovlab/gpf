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
        f1.mo      chr15  12         15        Dup_Germline
        f2.mo      chr15  1           4        Dup
        f1.fa      chr1   7          10        Del_Germline
        f2.fa      chr1   44         48        Del
        f1.fa      chr1   66         68        Dup_Germline
        f1.mo      chr15  93         96        Dup
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
        f1.mo	   chr15	1	        12	        Dup
        f1.fa	   chr15	13	        20	        Dup
        f1.p1	   chr15	23	        29	        Dup
        f1.s1	   chr15	55	        59	        Dup
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

    assert len(svs) == 4
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
        person_id  location     variant
        f1.mo      chr1:1-3	    duplication
        f2.fa      chr1:5-8	    duplication
        f1.s1      chr2:77-79	deletion
        f1.p1      chr2:98-99	deletion
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

    assert len(svs) == 4
    assert len(fvs) == 4


@pytest.fixture
def simple_cnv_loader(gpf_instance: GPFInstance) -> Any:
    def ctor(
            cnv_ped: Path,
            cnf_filename: Path,
            additional_params: Any
    ) -> Any:
        families = FamiliesLoader.load_simple_families_file(cnv_ped)
        assert families is not None

        params = additional_params
        return CNVLoader(
            families, [str(cnf_filename)],
            genome=gpf_instance.reference_genome, params=params,
        )
    return ctor


@pytest.fixture(scope="module")
def variants_file_2(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("acgt_instance")
    cnv_path = setup_denovo(
        root_path / "cnv_data" / "in.tsv",
        """
        family_id	location	              variant	best_state
        f1          chr1:1-4	              CNV+	    2||2||2||3
        f1          chr1:5-8	              CNV-	    2||2||2||1
        f2          chr1:12-20	              CNV+	    2||2||3
        f2          chr2:21-23	              CNV+	    2||2||3
        f1          chr1:44-48	              CNV-	    2||2||1||2
        f1          chr1:91-95                CNV+	    2||1||2||2
        """)

    return cnv_path


def test_chromosomes_have_adjusted_chrom_add(
    simple_cnv_loader: Any,
    cnv_ped: Any,
    variants_file: Path
) -> None:
    loader = simple_cnv_loader(cnv_ped, variants_file, {
        "add_chrom_prefix": "chr",
        "cnv_family_id": "family_id",
        "cnv_best_state": "best_state"
    })
    assert loader.chromosomes == ["chrchr1", "chrchr2"]


def test_chromosomes_have_adjusted_chrom_del(
    simple_cnv_loader: Any,
    cnv_ped: Any,
    variants_file_2: Path
) -> None:
    loader = simple_cnv_loader(cnv_ped, variants_file_2, {
        "del_chrom_prefix": "chr",
        "cnv_family_id": "family_id",
        "cnv_best_state": "best_state"
    })
    assert loader.chromosomes == ["1", "2"]


def test_variants_have_adjusted_chrom_add(
    simple_cnv_loader: Any,
    cnv_ped: Any,
    variants_file: Path
) -> None:
    loader = simple_cnv_loader(cnv_ped, variants_file, {
        "add_chrom_prefix": "chr",
        "cnv_family_id": "family_id",
        "cnv_best_state": "best_state"
    })

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    for summary_variant, _ in variants:
        assert summary_variant.chromosome.startswith("chrchr")


def test_variants_have_adjusted_chrom_del(
    simple_cnv_loader: Any,
    cnv_ped: Any,
    variants_file_2: Path
) -> None:
    loader = simple_cnv_loader(cnv_ped, variants_file_2, {
        "del_chrom_prefix": "chr",
        "cnv_family_id": "family_id",
        "cnv_best_state": "best_state"
    })

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    for summary_variant, _ in variants:
        assert not summary_variant.chromosome.startswith("chrchr")


def test_reset_regions_with_adjusted_chrom_add(
    simple_cnv_loader: Any,
    cnv_ped: Any,
    variants_file: Path
) -> None:
    loader = simple_cnv_loader(cnv_ped, variants_file, {
        "add_chrom_prefix": "chr",
        "cnv_family_id": "family_id",
        "cnv_best_state": "best_state"
    })
    regions = ["chrchr1"]
    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    unique_chroms = np.unique([sv.chromosome for sv, _ in variants])
    assert (unique_chroms == regions).all()


def test_reset_regions_with_adjusted_chrom_del(
    simple_cnv_loader: Any,
    cnv_ped: Any,
    variants_file_2: Path
) -> None:
    loader = simple_cnv_loader(cnv_ped, variants_file_2, {
        "del_chrom_prefix": "chr",
        "cnv_family_id": "family_id",
        "cnv_best_state": "best_state"
    })
    regions = ["1"]
    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    unique_chroms = np.unique([sv.chromosome for sv, _ in variants])
    assert (unique_chroms == regions).all()

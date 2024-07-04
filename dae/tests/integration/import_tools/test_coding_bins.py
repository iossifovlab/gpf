# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing import (
    denovo_study,
    setup_denovo,
    setup_pedigree,
    setup_vcf,
    t4c8_gpf,
    vcf_study,
)
from dae.testing.import_helpers import StudyInputLayout


@pytest.fixture()
def vcf_import_data(
    tmp_path: pathlib.Path,
    genotype_storage: GenotypeStorage,
) -> tuple[pathlib.Path, GPFInstance, StudyInputLayout]:
    root_path = tmp_path
    gpf_instance = t4c8_gpf(root_path)

    if genotype_storage:
        gpf_instance\
            .genotype_storages\
            .register_default_storage(genotype_storage)

    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
chr1   12  .  T   C   .    .      .    GT     0/1 0/1 0/1 0/0 0/0 0/1
chr1   20  .  G   A   .    .      .    GT     0/0 0/0 0/1 0/1 0/0 0/1
chr1   129 .  T   C   .    .      .    GT     0/1 0/1 0/1 0/0 0/0 0/1
chr1   143 .  C   A   .    .      .    GT     0/0 0/0 0/1 0/1 0/0 0/1
        """)

    return root_path, gpf_instance, StudyInputLayout(
        "vcf_fixture", ped_path, [vcf_path], [], [], [])


@pytest.fixture()
def vcf_fixture(
    vcf_import_data: tuple[pathlib.Path, GPFInstance, StudyInputLayout],
    genotype_storage: GenotypeStorage,
) -> tuple[pathlib.Path, GenotypeData]:
    root_path, gpf_instance, layout = vcf_import_data

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
            },
        },
        "destination": {
            "storage_id": genotype_storage.storage_id,
        },
        "partition_description": {
            "coding_bin": {
                "coding_effect_types": "noStart,missense,synonymous",
            },
        },
        "processing_config": {
            "denovo": {
                "chromosomes": ["chr1"],
                "region_length": 100,
            },
            "vcf": {
                "chromosomes": ["chr1"],
                "region_length": 100,
            },
        },
    }
    return root_path, vcf_study(
        root_path,
        "vcf_coding_bin", layout.pedigree,
        layout.vcf,
        gpf_instance,
        project_config_update=project_config_update)


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_impala2(reason="supported for schema2 impala")
@pytest.mark.gs_gcp(reason="supported for gcp")
def test_coding_bin_for_vcf(
    vcf_fixture: tuple[pathlib.Path, GenotypeData],
    genotype_storage: GenotypeStorage,
) -> None:

    root_path, _ = vcf_fixture
    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            "vcf_coding_bin/family/coding_bin=1"))
    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            "vcf_coding_bin/family/coding_bin=0"))

    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            "vcf_coding_bin/summary/coding_bin=1"))
    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            "vcf_coding_bin/summary/coding_bin=0"))


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_impala2(reason="supported for schema2 impala")
@pytest.mark.gs_gcp(reason="supported for gcp")
@pytest.mark.parametrize(
    "effect_types,count",
    [
        (None, 8),
        (["missense", "noStart"], 4),
        (["intron"], 4),
    ],
)
def test_vcf_import_coding_bin_queries(
    effect_types: list[str] | None, count: int,
    vcf_fixture: tuple[pathlib.Path, GenotypeData],
    genotype_storage: GenotypeStorage,
) -> None:
    _, study = vcf_fixture
    vs = list(study.query_variants(effect_types=effect_types))
    assert len(vs) == count


@pytest.fixture()
def denovo_import_data(
    tmp_path: pathlib.Path,
    genotype_storage: GenotypeStorage,
) -> tuple[pathlib.Path, GPFInstance, StudyInputLayout]:
    root_path = tmp_path

    gpf_instance = t4c8_gpf(root_path)

    if genotype_storage:
        gpf_instance\
            .genotype_storages\
            .register_default_storage(genotype_storage)

    ped_path = setup_pedigree(
        root_path / "denovo_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        """)
    denovo_path = setup_denovo(
        root_path / "denovo_data" / "in.tsv",
        """
        familyId location variant   bestState
        f1       chr1:12  sub(T->C) 2||2||1/0||0||1
        f2       chr1:20  sub(G->A) 2||2||1/0||0||1
        f1       chr1:129 sub(T->C) 2||2||1/0||0||1
        f2       chr1:143 sub(C->A) 2||2||1/0||0||1
        """)

    return root_path, gpf_instance, StudyInputLayout(
        "denovo_fixture", ped_path, [], [denovo_path], [], [])


@pytest.fixture()
def denovo_fixture(
    tmp_path: pathlib.Path,
    denovo_import_data: tuple[pathlib.Path, GPFInstance, StudyInputLayout],
    genotype_storage: GenotypeStorage,
) -> tuple[pathlib.Path, GenotypeData]:
    root_path, gpf_instance, layout = denovo_import_data

    project_config_update = {
        "destination": {
            "storage_type": genotype_storage.storage_type,
        },
        "partition_description": {
            "coding_bin": {
                "coding_effect_types": "noStart,missense,synonymous",
            },
        },
        "processing_config": {
            "denovo": {
                "chromosomes": ["chr1"],
                "region_length": 100,
            },
            "vcf": {
                "chromosomes": ["chr1"],
                "region_length": 100,
            },
        },
    }
    study = denovo_study(
        root_path,
        "denovo_coding_bin", layout.pedigree, layout.denovo,
        gpf_instance,
        project_config_update=project_config_update)
    return root_path, study


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_impala2(reason="supported for schema2 impala")
@pytest.mark.gs_gcp(reason="supported for gcp")
def test_denovo_coding_bin_for_denovo_import(
    denovo_fixture: tuple[pathlib.Path, GenotypeData],
    genotype_storage: GenotypeStorage,
) -> None:
    root_path, _ = denovo_fixture
    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            "denovo_coding_bin/family/coding_bin=0"))
    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            "denovo_coding_bin/family/coding_bin=1"))

    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            "denovo_coding_bin/summary/coding_bin=0"))
    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            "denovo_coding_bin/summary/coding_bin=1"))


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_impala2(reason="supported for schema2 impala")
@pytest.mark.gs_gcp(reason="supported for gcp")
@pytest.mark.parametrize(
    "effect_types,count",
    [
        (None, 4),
        (["missense", "noStart"], 2),
        (["intron"], 2),
    ],
)
def test_denovo_import_coding_bin_queries(
    effect_types: list[str] | None, count: int,
    denovo_fixture: tuple[pathlib.Path, GenotypeData],
    genotype_storage: GenotypeStorage,
) -> None:
    _, study = denovo_fixture

    vs = list(study.query_variants(effect_types=effect_types))
    assert len(vs) == count

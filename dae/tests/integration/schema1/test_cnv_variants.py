# pylint: disable=W0621,C0114,C0116,W0212,W0613
import copy
import pytest

import numpy as np

from dae.variants.core import Allele
from dae.variants_loaders.cnv.loader import CNVLoader
from dae.pedigrees.loader import FamiliesLoader
from dae.variants_loaders.raw.loader import AnnotationPipelineDecorator
from dae.inmemory_storage.raw_variants import RawMemoryVariants
from dae.import_tools.import_tools import ImportProject
from dae.import_tools.cli import run_with_project

from dae.configuration.gpf_config_parser import FrozenBox
from dae.utils.regions import Region


@pytest.fixture
def cnv_loader(
        fixture_dirname, gpf_instance_2013, annotation_pipeline_internal):

    families_filename = fixture_dirname("backends/cnv_ped.txt")
    variants_filename = fixture_dirname("backends/cnv_variants.txt")

    families_loader = FamiliesLoader(
        families_filename, **{"ped_file_format": "simple"})
    families = families_loader.load()

    variants_loader = CNVLoader(
        families, [variants_filename], gpf_instance_2013.reference_genome,
        params={
            "cnv_family_id": "familyId",
            "cnv_best_state": "bestState"})

    return families_loader, AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )


@pytest.fixture
def cnv_raw(cnv_loader):
    _families_loader, variants_loader = cnv_loader
    fvars = RawMemoryVariants([variants_loader], variants_loader.families)
    return fvars


@pytest.fixture(scope="session")
def cnv_project_config(fixture_dirname, impala_genotype_storage):
    families_filename = fixture_dirname("backends/cnv_ped.txt")
    variants_filename = fixture_dirname("backends/cnv_variants.txt")

    project = {
        "id": "cnv_test",
        "input": {
            "pedigree": {
                "file": families_filename,
                "file_format": "simple"
            },
            "cnv": {
                "files": [
                    variants_filename,
                ],
                "family_id": "familyId",
                "best_state": "bestState",
                "transmission_type": "denovo",
            }
        },
        "destination": {
            "storage_id": impala_genotype_storage.storage_id,
        }
    }
    return project


@pytest.fixture(scope="session")
def cnv_impala(
        cnv_project_config,
        gpf_instance_2013,
        hdfs_host,
        impala_host,
        impala_genotype_storage,
        reimport):
    # pylint: disable=too-many-locals,import-outside-toplevel
    from dae.impala_storage.helpers.impala_helpers import ImpalaHelpers

    impala_helpers = ImpalaHelpers(
        impala_hosts=[impala_host], impala_port=21050)

    study_id = f"cnv_test_{impala_genotype_storage.storage_id}"
    gpf_instance_2013.genotype_storages.register_genotype_storage(
        impala_genotype_storage)
    (variant_table, pedigree_table) = \
        impala_genotype_storage.study_tables(
            FrozenBox({"id": study_id}))

    if reimport or \
            not impala_helpers.check_table(
                "impala_test_db", variant_table) or \
            not impala_helpers.check_table(
                "impala_test_db", pedigree_table):

        from dae.impala_storage.helpers.hdfs_helpers import HdfsHelpers

        hdfs = HdfsHelpers(hdfs_host, 8020)

        tmp_dirname = hdfs.tempdir(prefix="variants_", suffix="_data")
        project = copy.deepcopy(cnv_project_config)
        project["processing_config"] = {
            "work_dir": tmp_dirname
        }
        project["id"] = study_id
        import_project = ImportProject.build_from_config(
            project, gpf_instance=gpf_instance_2013)
        run_with_project(import_project)

    fvars = impala_genotype_storage.build_backend(
        FrozenBox({"id": study_id}), gpf_instance_2013.reference_genome,
        gpf_instance_2013.gene_models
    )

    return fvars


def test_cnv_impala(cnv_impala):
    variants = cnv_impala.query_variants(
        effect_types=["CNV+", "CNV-"],
        variant_type="cnv+ or cnv-",
        inheritance="denovo"
    )
    variants = list(variants)

    print(variants)

    for fv in variants:
        assert fv.alt_alleles
        for aa in fv.alt_alleles:
            assert Allele.Type.cnv & aa.allele_type
    assert len(variants) == 12


def test_cnv_impala_region_query(cnv_impala):
    variants = cnv_impala.query_variants(
        regions=[
            Region("1", 1600000, 1620000)
        ],
        effect_types=["CNV+", "CNV-"],
        variant_type="cnv+ or cnv-",
        inheritance="denovo"
    )
    assert len(list(variants)) == 1
    variants = cnv_impala.query_variants(
        regions=[
            Region("1", 1600000, 1630000)
        ],
        effect_types=["CNV+", "CNV-"],
        variant_type="cnv+ or cnv-",
        inheritance="denovo"
    )
    assert len(list(variants)) == 2
    variants = cnv_impala.query_variants(
        regions=[
            Region("1", 1000000, 2000000)
        ],
        effect_types=["CNV+", "CNV-"],
        variant_type="cnv+ or cnv-",
        inheritance="denovo"
    )
    assert len(list(variants)) == 2


def test_cnv_best_state_x(cnv_raw):
    variants = cnv_raw.query_variants(
        effect_types=["CNV+", "CNV-"],
        variant_type="cnv+ or cnv-",
    )
    variants = [v for v in variants if v.chrom == "X"]

    assert len(variants) == 2
    for v in variants:
        assert v.alt_alleles
        for aa in v.alt_alleles:
            assert Allele.Type.cnv & aa.allele_type

    assert np.array_equal(
        variants[0].best_state,
        np.asarray([
            [2, 1, 0, 2],
            [0, 0, 1, 0]
        ])
    )

    assert np.array_equal(
        variants[1].best_state,
        np.asarray([
            [2, 1, 0, 2],
            [0, 0, 1, 0]
        ])
    )

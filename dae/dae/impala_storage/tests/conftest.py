# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
from io import StringIO

import numpy as np

import pytest

from dae.pedigrees.loader import FamiliesLoader
from dae.utils.variant_utils import GENOTYPE_TYPE, BEST_STATE_TYPE
from dae.backends.dae.loader import DenovoLoader
from dae.backends.raw.loader import AnnotationPipelineDecorator
from dae.impala_storage.parquet_io import ParquetManager, \
    NoPartitionDescriptor
from dae.configuration.gpf_config_parser import FrozenBox
from dae.impala_storage.hdfs_helpers import HdfsHelpers

PED1 = """
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          d1,          0,        0,        1,     1,         dad
f1,          m1,          0,        0,        2,     1,         mom
f1,          p1,          d1,       m1,       1,     2,         prb
"""

PED2 = """
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f2,          d2,          0,        0,        1,     1,         dad
f2,          m2,          0,        0,        2,     1,         mom
f2,          p2,          d2,       m2,       1,     2,         prb
"""


@pytest.fixture(scope="module")
def fam1():
    families_loader = FamiliesLoader(StringIO(PED1), ped_sep=",")
    families = families_loader.load()
    family = families["f1"]

    assert len(family.trios) == 1
    return family


@pytest.fixture(scope="module")
def fam2():
    families_loader = FamiliesLoader(StringIO(PED2), ped_sep=",")
    families = families_loader.load()
    family = families["f2"]

    assert len(family.trios) == 1
    return family


@pytest.fixture(scope="module")
def genotype():
    return np.array([[0, 0, 0], [0, 0, 0]], dtype=GENOTYPE_TYPE)


@pytest.fixture(scope="module")
def best_state():
    return np.array(
        [[2, 1, 0, 0], [0, 1, 2, 1], [0, 0, 0, 1]], dtype=BEST_STATE_TYPE
    )


@pytest.fixture(scope="module")
def best_state_serialized():
    return "\x02\x00\x00\x01\x01\x00\x00\x02\x00\x00\x01\x01"


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


@pytest.fixture
def extra_attrs_impala(
        request,
        denovo_extra_attr_loader,
        gpf_instance_2013,
        hdfs_host,
        impala_genotype_storage):
    hdfs = HdfsHelpers(hdfs_host, 8020)

    temp_dirname = hdfs.tempdir(prefix="variants_", suffix="_data")
    hdfs.mkdir(temp_dirname)

    study_id = "denovo_extra_attrs"
    parquet_filenames = ParquetManager.build_parquet_filenames(
        temp_dirname, bucket_index=2, study_id=study_id
    )

    assert parquet_filenames is not None

    ParquetManager.families_to_parquet(
        denovo_extra_attr_loader.families, parquet_filenames.pedigree
    )

    variants_dir = os.path.join(temp_dirname, "variants")
    partition_description = NoPartitionDescriptor(variants_dir)

    ParquetManager.variants_to_parquet(
        denovo_extra_attr_loader, partition_description
    )

    impala_genotype_storage.impala_load_dataset(
        study_id,
        variants_dir=os.path.dirname(parquet_filenames.variants),
        pedigree_file=parquet_filenames.pedigree,
    )

    fvars = impala_genotype_storage.build_backend(
        FrozenBox({"id": study_id}), gpf_instance_2013.reference_genome,
        gpf_instance_2013.gene_models
    )

    return fvars

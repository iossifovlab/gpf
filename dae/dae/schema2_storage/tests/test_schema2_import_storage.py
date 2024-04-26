# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pyarrow.parquet as pq
import pytest

from dae.schema2_storage.schema2_import_storage import (
    Schema2DatasetLayout,
    schema2_dataset_layout,
)
from dae.testing import acgt_gpf, setup_pedigree, setup_vcf
from dae.testing.import_helpers import vcf_study


@pytest.fixture(scope="module")
def import_data(
    tmp_path_factory: pytest.TempPathFactory
) -> Schema2DatasetLayout:
    root_path = tmp_path_factory.mktemp("import_data")
    gpf_instance = acgt_gpf(root_path)
    ped_path = setup_pedigree(
        root_path / "study" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "study" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS  ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1
chr1   1    .  A   G,TA .    .      .    GT     0/1  0/1  0/0
chr2   1    .  A   G,TA .    .      .    GT     0/1  0/1  0/0
chr3   1    .  A   G,TA .    .      .    GT     0/1  0/1  0/0
        """)
    vcf_study(
        root_path,
        "study", ped_path, [vcf_path],
        gpf_instance,
        project_config_overwrite={"destination": {"storage_type": "schema2"}},
    )
    return schema2_dataset_layout(f"{root_path}/work_dir/study")


def test_schema2_import_metadata(import_data: Schema2DatasetLayout) -> None:
    meta_file = pq.ParquetFile(import_data.meta)
    meta = {row["key"]: row["value"]
            for row in meta_file.read().to_pylist()}
    meta_file.close()

    assert "contigs" in meta
    assert meta["contigs"].split(",") == ["chr1", "chr2", "chr3"]
    assert "reference_genome" in meta
    assert meta["reference_genome"] == "genome"
    assert "gene_models" in meta
    assert meta["gene_models"] == "empty_gene_models"

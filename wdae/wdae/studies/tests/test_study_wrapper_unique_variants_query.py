# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from pathlib import Path
from typing import Any

import pytest
from dae.duckdb_storage.duckdb_genotype_storage import duckdb_storage_factory
from dae.testing import setup_dataset, setup_pedigree, setup_vcf, vcf_study
from dae.testing.alla_import import alla_gpf
from gpf_instance.gpf_instance import WGPFInstance

from studies.query_transformer import QueryTransformer, make_query_transformer
from studies.study_wrapper import WDAEStudyGroup


@pytest.fixture(scope="module")
def instance_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("test_unique_family_variants_query")


@pytest.fixture(scope="module")
def wgpf_instance(instance_path: Path) -> WGPFInstance:
    storage_config = {
        "id": "duckdb",
        "storage_type": "duckdb",
        "db": "duckdb2_storage/storage2.db",
        "base_dir": str(instance_path),
    }
    gpf_instance = alla_gpf(
        instance_path, duckdb_storage_factory(storage_config),
    )

    return WGPFInstance(
        gpf_instance.dae_config,
        gpf_instance.dae_dir,
        gpf_instance.dae_config_path,
        grr=gpf_instance.grr,
    )


@pytest.fixture(scope="module")
def dataset(
    instance_path: Path,
    wgpf_instance: WGPFInstance,
) -> WDAEStudyGroup:
    root_path = instance_path

    ped_path1 = setup_pedigree(
        root_path / "study_1" / "in.ped", textwrap.dedent("""
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       ch1      dad1  mom1  2   2      prb
f2       mom2     0     0     2   1      mom
f2       dad2     0     0     1   1      dad
f2       ch2      dad2  mom2  2   2      prb
        """))

    vcf_path1 = setup_vcf(
        root_path / "study_1" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1 dad2 ch2 mom2
chrA   1   .  A   C,G   .    .      .    GT     0/1  0/2  0/0 0/1  0/0 0/0
chrA   2   .  A   C     .    .      .    GT     0/0  0/1  0/0 0/1  0/0 0/1
        """)

    ped_path2 = setup_pedigree(
        root_path / "study_2" / "in.ped", textwrap.dedent("""
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       ch1      dad1  mom1  2   2      prb
f2       mom2     0     0     2   1      mom
f2       dad2     0     0     1   1      dad
f2       ch2      dad2  mom2  2   2      prb
        """))

    vcf_path2 = setup_vcf(
        root_path / "study_2" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1 dad2 ch2 mom2
chrA   1   .  A   C,G   .    .      .    GT     0/1  0/2  0/0 0/0  0/0 0/0
chrA   2   .  A   C     .    .      .    GT     0/1  0/0  0/0 0/1  0/0 0/1
        """)

    study1 = vcf_study(
        root_path,
        "study_1", ped_path1, [vcf_path1],
        wgpf_instance)
    study2 = vcf_study(
        root_path,
        "study_2", ped_path2, [vcf_path2],
        wgpf_instance)

    (root_path / "dataset").mkdir(exist_ok=True)

    wgpf_instance.reload()

    setup_dataset(
        "ds1", wgpf_instance, study1, study2,
        dataset_config_update=textwrap.dedent(f"""
            conf_dir: {root_path / "dataset "}
        """),
    )

    wrapper = wgpf_instance.get_wdae_wrapper("ds1")
    assert isinstance(wrapper, WDAEStudyGroup)

    return wrapper


@pytest.fixture(scope="module")
def query_transformer(
    wgpf_instance: WGPFInstance,
) -> QueryTransformer:
    return make_query_transformer(wgpf_instance)


@pytest.mark.parametrize(
    "unique_family_variants, count",
    [
        (False, 7),
        (True, 4),
    ],
)
def test_unique_family_variants(
    dataset: WDAEStudyGroup,
    query_transformer: QueryTransformer,
    unique_family_variants: bool,  # noqa: FBT001
    count: int,
) -> None:
    query: dict[str, Any] = {"unique_family_variants": unique_family_variants}
    vs = list(dataset.query_variants_raw(query, query_transformer))

    assert len(vs) == count

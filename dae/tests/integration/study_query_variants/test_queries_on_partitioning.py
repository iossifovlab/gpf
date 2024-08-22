# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.t4c8_import import t4c8_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module", params=["srb", "irb"])
def study_2p(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage: GenotypeStorage,
) -> GenotypeData:
    param = request.param
    study_id = f"study_2p_{genotype_storage.storage_id}_{param}"

    root_path = tmp_path_factory.mktemp(study_id)

    t4c8_instance = t4c8_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / study_id / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / study_id / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS  ID REF ALT  QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   4    .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/1  0/2  0/2
chr1   54   .  T   C    .    .      .    GT     0/1  0/1  0/1 0/1  0/0  0/1
chr1   90   .  G   C,GA .    .      .    GT     0/1  0/2  0/2 0/1  0/2  0/1
chr1   100  .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/2  0/2  0/0
chr1   119  .  A   G,C  .    .      .    GT     0/0  0/2  0/2 0/1  0/2  0/1
chr1   122  .  A   C,AC .    .      .    GT     0/1  0/1  0/1 0/2  0/2  0/2
        """)

    if request.param == "srb":
        integer_region_bins = False
    elif request.param == "irb":
        integer_region_bins = True
    else:
        raise ValueError(f"unexpected param: {request.param}")

    project_config_update = {
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 100,
                "integer_region_bins": integer_region_bins,
            },
            "frequency_bin": {
                "rare_boundary": 25.0,
            },
            "coding_bin": {
                "coding_effect_types": [
                    "frame-shift",
                    "noStart",
                    "missense",
                    "synonymous",
                ],
            },
            "family_bin": {
                "family_bin_size": 2,
            },
        },
    }

    return vcf_study(
        root_path,
        study_id, ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
    )


def test_variants_simple(study_2p: GenotypeData) -> None:
    svs = list(study_2p.query_summary_variants())
    assert len(svs) == 6

    fvs = list(study_2p.query_variants())
    assert len(fvs) == 12


@pytest.mark.no_gs_parquet()
@pytest.mark.parametrize("params, count", [
    ({"genes": ["t4"]}, 2),
    ({"genes": ["c8"]}, 5),
    ({"effect_types": ["missense"]}, 2),
    ({"effect_types": ["synonymous"]}, 4),
    ({"regions": [Region("chr1")]}, 12),
    ({"regions": [Region("chr1", None, 55)]}, 4),
    ({"regions": [Region("chr1", 55, None)]}, 8),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, 2),
    ({"frequency_filter": [("af_allele_freq", (15.0, None))]}, 12),
    ({"frequency_filter": [("af_allele_freq", (None, 25.0))]}, 9),
    ({"frequency_filter": [("af_allele_freq", (25.0, None))]}, 12),
    ({"real_attr_filter": [("af_allele_count", (None, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (1, None))]}, 12),
    ({"real_attr_filter": [("af_allele_count", (1, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (2, None))]}, 12),
    ({"real_attr_filter": [("af_allele_count", (2, 2))]}, 8),
    ({"limit": 1}, 1),
    ({"limit": 2}, 2),
    ({"ultra_rare": True}, 2),
])
def test_query_family_variants_counting(
    params: dict[str, Any],
    count: int,
    study_2p: GenotypeData,
) -> None:
    fvs = list(study_2p.query_variants(**params))
    assert len(fvs) == count


@pytest.mark.no_gs_parquet()
@pytest.mark.parametrize("params, count", [
    ({"genes": ["t4"]}, 1),
    ({"genes": ["c8"]}, 3),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["synonymous"]}, 3),
    ({"regions": [Region("chr1")]}, 6),
    ({"regions": [Region("chr1", None, 55)]}, 2),
    ({"regions": [Region("chr1", 55, None)]}, 4),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, 2),
    ({"frequency_filter": [("af_allele_freq", (15.0, None))]}, 6),
    ({"frequency_filter": [("af_allele_freq", (None, 25.0))]}, 5),
    ({"frequency_filter": [("af_allele_freq", (25.0, None))]}, 6),
    ({"real_attr_filter": [("af_allele_count", (None, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (1, None))]}, 6),
    ({"real_attr_filter": [("af_allele_count", (1, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (2, None))]}, 6),
    ({"real_attr_filter": [("af_allele_count", (2, 2))]}, 4),
    ({"limit": 1}, 1),
    ({"limit": 2}, 2),
    ({"ultra_rare": True}, 2),
])
def test_query_summary_variants_counting(
    params: dict[str, Any],
    count: int,
    study_2p: GenotypeData,
) -> None:
    svs = list(study_2p.query_summary_variants(**params))
    assert len(svs) == count


@pytest.mark.parametrize("params, count", [
    ({}, 12),
    ({"roles": "prb"}, 9),
    ({"roles": "not prb"}, 7),
    ({"roles": "mom and not prb"}, 5),
    ({"roles": "mom and dad and not prb"}, 3),
    ({"roles": "prb and not mom and not dad"}, 0),
])
def test_query_family_variants_by_role(
    params: dict[str, Any],
    count: int,
    study_2p: GenotypeData,
) -> None:
    fvs = list(study_2p.query_variants(
        **params))
    assert len(fvs) == count


@pytest.mark.parametrize("params, count", [
    ({}, 12),
    ({"sexes": "M"}, 11),
    ({"sexes": "M and not F"}, 2),
    ({"sexes": "female and not male"}, 5),
])
def test_query_family_variants_by_sex(
    params: dict[str, Any],
    count: int,
    study_2p: GenotypeData,
) -> None:
    fvs = list(study_2p.query_variants(
        **params,
    ))
    assert len(fvs) == count


@pytest.mark.parametrize("params, count", [
    ({}, 12),
    ({"inheritance": ["missing"]}, 7),
    ({"inheritance": ["mendelian"]}, 9),
    ({"inheritance": ["denovo"]}, 0),
    ({"inheritance": ["mendelian or missing"]}, 12),
    ({"inheritance": ["mendelian and missing"]}, 0),
])
def test_query_family_variants_by_inheritance(
    params: dict[str, Any],
    count: int,
    study_2p: GenotypeData,
) -> None:
    fvs = list(study_2p.query_variants(
        **params,
    ))
    assert len(fvs) == count


@pytest.mark.parametrize("params, count", [
    ({}, 12),
    ({"variant_type": "sub"}, 10),
    ({"variant_type": "ins"}, 5),
    ({"variant_type": "del"}, 0),
])
def test_query_family_variants_by_variant_type(
    params: dict[str, Any],
    count: int,
    study_2p: GenotypeData,
) -> None:
    fvs = list(study_2p.query_variants(**params))
    assert len(fvs) == count


@pytest.mark.parametrize("params, count", [
    ({}, 12),
    ({"person_ids": ["ch3"]}, 5),
    ({"person_ids": ["ch3"], "family_ids": ["f1.1"]}, 0),
    ({"person_ids": ["ch3"], "family_ids": ["f1.3"]}, 5),
    ({"family_ids": ["f1.1"]}, 6),
    ({"family_ids": ["f1.1"], "person_ids": ["ch1"]}, 4),
])
def test_query_family_variants_by_family_and_person_ids(
    params: dict[str, Any],
    count: int,
    study_2p: GenotypeData,
) -> None:
    fvs = list(study_2p.query_variants(
        **params,
    ))
    assert len(fvs) == count

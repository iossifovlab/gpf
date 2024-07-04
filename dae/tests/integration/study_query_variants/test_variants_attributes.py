# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def imported_study(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"test_variant_attributes_{genotype_storage.storage_id}")
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId momId sex status role
        f1       mom      0     0     2   1      mom
        f1       dad      0     0     1   1      dad
        f1       ch1      dad   mom   2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=bar>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom dad ch1
chrA   1   .  A   C   .    .      .    GT     0/1 0/0 0/0
chrA   2   .  A   C   .    .      .    GT     0/0 0/1 0/0
chrA   3   .  A   C   .    .      .    GT     1/1 0/0 0/0
chrA   4   .  A   C   .    .      .    GT     0/0 0/1 1/1
        """)

    study = vcf_study(
        root_path,
        "test_variant_attributes", pathlib.Path(ped_path),
        [pathlib.Path(vcf_path)],
        gpf_instance,
        project_config_update={
            "input": {
                "vcf": {
                    "include_reference_genotypes": True,
                    "include_unknown_family_genotypes": True,
                    "include_unknown_person_genotypes": True,
                    "denovo_mode": "denovo",
                    "omission_mode": "omission",
                },
            },
            "processing_config": {
                "include_reference": True,
            },
        })
    return study


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_impala2(reason="supported for schema2 impala")
@pytest.mark.gs_gcp(reason="supported for schema2 gcp")
@pytest.mark.gs_inmemory(reason="supported for inmemory storage")
@pytest.mark.parametrize("position,freqs", [
    (1, [75.0, 25.0]),
    (2, [75.0, 25.0]),
    (3, [50.0, 50.0]),
    (4, [75.0, 25.0]),
])
def test_variant_frequencies(
    imported_study: GenotypeData,
    position: int,
    freqs: list[float | None],
) -> None:
    regions = [Region("chrA", position, position)]
    vs = list(imported_study.query_variants(regions=regions))
    assert len(vs) == 1

    assert len(vs[0].get_attribute("af_allele_count")) == 1
    assert len(vs[0].get_attribute("af_allele_freq")) == 1
    assert len(vs[0]["af_ref_allele_freq"]) == 1
    assert len(vs[0]["af_allele_freq"]) == 1

    assert len(vs[0].alt_alleles) == 1
    aa = vs[0].alt_alleles[0]

    ref_freq, alt_freq = freqs
    assert aa["af_ref_allele_freq"] == pytest.approx(ref_freq, 1e-2)
    assert aa["af_allele_freq"] == pytest.approx(alt_freq, 1e-2)

    assert aa.get_attribute("af_ref_allele_freq") == \
        pytest.approx(ref_freq, 1e-2)
    assert aa.get_attribute("af_allele_freq") == \
        pytest.approx(alt_freq, 1e-2)

    assert aa.get_attribute("ala_bala") is None
    with pytest.raises(AttributeError):
        assert aa["ala_bala"] is None

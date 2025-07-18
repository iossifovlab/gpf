# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.loader import FamiliesLoader
from dae.testing import (
    setup_genome,
    setup_pedigree,
    setup_vcf,
)
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture(scope="module")
def import_vcf_data(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[ReferenceGenome, pathlib.Path, pathlib.Path]:
    root_path = tmp_path_factory.mktemp("vcf2parquet_contigs_problem")

    genome = setup_genome(
        root_path / "acgt_gpf" / "genome" / "allChr.fa",
        f"""
        >chr1
        {25 * "ACGT"}
        >chr2
        {25 * "ACGT"}
        >HLA-B*27:05:18
        {25 * "ACGT"}
        """,
    )
    ped_path = setup_pedigree(
        root_path / "study_1" / "in.ped",
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
        root_path / "study_1" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        ##contig=<ID=chr2>
        ##contig=<ID=HLA-B*27:05:18>
        #CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
        chr2   1   .  A   T    .    .      .    GT     0/1 0/0 0/1 0/0 0/0 0/1
        chr2   2   .  A   T    .    .      .    GT     0/0 0/0 0/0 0/0 0/0 0/1
        """, csi=True)
    return (genome, ped_path, vcf_path)


def test_vcf_loader_with_csi_index(import_vcf_data):
    genome, ped_path, vcf_path = import_vcf_data

    families_loader = FamiliesLoader(str(ped_path))
    families = families_loader.load()

    loader = VcfLoader(
        families,
        [str(vcf_path)],
        genome,
        params={
            "vcf_include_reference_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
            "vcf_include_unknown_person_genotypes": True,
        },
    )
    assert loader is not None

    assert loader.chromosomes == ["chr2"]

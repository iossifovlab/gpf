# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.testing import setup_denovo, setup_pedigree
from dae.variants_loaders.dae.loader import DenovoLoader


@pytest.fixture(scope="session")
def trio_families(tmp_path_factory: pytest.TempPathFactory) -> FamiliesData:
    root_path = tmp_path_factory.mktemp(
        "denovo_add_chrom_trio_families")
    ped_path = setup_pedigree(
        root_path / "trio_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        """)
    loader = FamiliesLoader(ped_path)
    return loader.load()


@pytest.fixture(scope="session")
def trio_denovo(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp(
        "denovo_add_chrom_trio")
    return setup_denovo(
        root_path / "trio_data" / "in.tsv",
        """
          chrom  pos  ref  alt  person_id  someAttr
          chr1   1    ACG  A    p1         someAttr1
          chr2   2    A    AAA  p1         someAttr2
        """,
    )


@pytest.fixture
def denovo_extra_attr_loader(
    acgt_genome_38: ReferenceGenome,
    trio_families: FamiliesData,
    trio_denovo: pathlib.Path,
) -> DenovoLoader:

    return DenovoLoader(
        trio_families,
        str(trio_denovo),
        genome=acgt_genome_38)


def test_denovo_extra_attributes(denovo_extra_attr_loader):

    loader = denovo_extra_attr_loader
    fvs = list(loader.family_variants_iterator())
    print(fvs)
    for fv in fvs:
        for fa in fv.alt_alleles:
            print(fa.attributes, fa.summary_attributes)
            assert "someAttr" in fa.attributes

    fv = fvs[0]
    for fa in fv.alt_alleles:
        print(fa, fa.attributes, fa.summary_attributes)
        assert "someAttr" in fa.attributes
        assert fa.get_attribute("someAttr") == "someAttr1"

    fv = fvs[-1]
    for fa in fv.alt_alleles:
        print(fa.attributes, fa.summary_attributes)
        assert "someAttr" in fa.attributes
        assert fa.get_attribute("someAttr") == "someAttr2"

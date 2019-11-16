from dae.pedigrees.pedigree_reader import PedigreeReader
from dae.pedigrees.family import FamiliesData

from dae.backends.vcf.loader import VcfLoader


def test_vcf_loader(vcf_loader_data):
    conf = vcf_loader_data('backends/effects_trio_dad')
    print(conf)

    ped_df = PedigreeReader.flexible_pedigree_read(conf.pedigree)
    families = FamiliesData.from_pedigree_df(ped_df)

    loader = VcfLoader(families, conf.vcf)
    assert loader is not None

    print(loader.samples)

    for v in loader.full_variants_iterator():
        print(v)

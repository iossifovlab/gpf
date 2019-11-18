import pytest
from dae.pedigrees.family import PedigreeReader
from dae.pedigrees.family import FamiliesData

from dae.backends.vcf.loader import VcfLoader


@pytest.mark.parametrize("fixture_data", [
    "backends/effects_trio_dad",
    "backends/effects_trio",
    "backends/trios2",
    "backends/members_in_order1",
    "backends/members_in_order2",
    "backends/unknown_trio",
    "backends/trios_multi",
    "backends/quads_f1",
])
def test_vcf_loader(vcf_loader_data, variants_vcf, fixture_data):
    conf = vcf_loader_data(fixture_data)
    print(conf)

    fvars = variants_vcf(fixture_data)

    ped_df = PedigreeReader.flexible_pedigree_read(conf.pedigree)
    families = FamiliesData.from_pedigree_df(ped_df)

    loader = VcfLoader(families, conf.vcf)
    assert loader is not None

    print(loader.samples)
    vars_old = list(fvars.query_variants(
        return_reference=True, return_unknown=True))
    vars_new = list(loader.family_variants_iterator())

    for nfv, ofv in zip(vars_new, vars_old):
        print(nfv, ofv)

        assert nfv == ofv

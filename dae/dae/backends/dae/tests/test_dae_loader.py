from dae.utils.variant_utils import mat2str


def test_dae_transmitted_loader_simple(dae_transmitted):
    for fv in dae_transmitted.family_variants_iterator():
        print(fv, mat2str(fv.best_state), mat2str(fv.gt))

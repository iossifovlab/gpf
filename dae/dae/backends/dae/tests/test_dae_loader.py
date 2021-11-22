import numpy as np
from dae.utils.variant_utils import mat2str, str2mat


def test_dae_transmitted_loader_simple(dae_transmitted):
    for fv in dae_transmitted.family_variants_iterator():
        print(fv, mat2str(fv.best_state), mat2str(fv.gt))
        for fa in fv.alt_alleles:
            read_counts = fa.get_attribute("read_counts")
            assert read_counts is not None

    assert np.all(
        read_counts == str2mat(
            "54 88 51 108/39 0 65 1/2 0 1 3", col_sep=" ", row_sep="/"))

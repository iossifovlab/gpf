# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
import numpy as np
from dae.backends.dae.loader import DaeTransmittedLoader
from dae.pedigrees.loader import FamiliesLoader
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


@pytest.fixture
def simple_dae_loader(gpf_instance_2013, fixture_dirname):
    def ctor(input_prefix, additional_params):
        input_prefix = fixture_dirname(input_prefix)
        summary_filename = f"{input_prefix}.txt.gz"
        family_filename = f"{input_prefix}.families.txt"

        families = FamiliesLoader.load_simple_families_file(family_filename)

        variants_loader = DaeTransmittedLoader(
            families,
            summary_filename,
            genome=gpf_instance_2013.reference_genome,
            params=additional_params,
            regions=None,
        )

        return variants_loader
    return ctor


@pytest.mark.parametrize("input_prefix, params", [
    ("dae_transmitted/transmission", {"add_chrom_prefix": "chr"}),
])
def test_chromosomes_have_adjusted_chrom(simple_dae_loader,
                                         input_prefix, params):
    loader = simple_dae_loader(input_prefix, params)

    prefix = params.get("add_chrom_prefix", "")
    assert loader.chromosomes == [f"{prefix}1"]


@pytest.mark.parametrize("input_prefix, params", [
    ("dae_transmitted/transmission", {"add_chrom_prefix": "chr"}),
])
def test_variants_have_adjusted_chrom(simple_dae_loader,
                                      input_prefix, params):
    loader = simple_dae_loader(input_prefix, params)
    is_add = "add_chrom_prefix" in params

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    for summary_variant, _ in variants:
        if is_add:
            assert summary_variant.chromosome.startswith("chr")
        else:
            assert not summary_variant.chromosome.startswith("chr")


@pytest.mark.parametrize("input_prefix, params", [
    ("dae_transmitted/transmission", {"add_chrom_prefix": "chr"}),
])
def test_reset_regions_with_adjusted_chrom(simple_dae_loader,
                                           input_prefix, params):
    loader = simple_dae_loader(input_prefix, params)
    prefix = params.get("add_chrom_prefix", "")
    regions = [f"{prefix}1:801943-802025"]
    unique_regions = [f"{prefix}1"]

    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 7
    unique_chroms = np.unique([sv.chromosome for sv, _ in variants])
    assert (unique_chroms == unique_regions).all()

# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
import numpy as np
from dae.variants_loaders.dae.loader import DenovoLoader


@pytest.fixture
def simple_denovo_loader(gpf_instance_2013, fixture_dirname, fake_families):
    def ctor(input_filename, additional_params):
        params = {
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
            **additional_params,
        }
        denovo_filename = fixture_dirname(input_filename)
        return DenovoLoader(
            fake_families, denovo_filename,
            genome=gpf_instance_2013.reference_genome, params=params,
        )
    return ctor


@pytest.mark.parametrize("input_filename, params", [
    ("denovo_import/variants_VCF_style.tsv", {"add_chrom_prefix": "chr"}),
    ("denovo_import/variants_VCF_style_chr.tsv", {"del_chrom_prefix": "chr"}),
])
def test_chromosomes_have_adjusted_chrom(simple_denovo_loader,
                                         input_filename, params):
    loader = simple_denovo_loader(input_filename, params)

    prefix = params.get("add_chrom_prefix", "")
    assert loader.chromosomes == [f"{prefix}1", f"{prefix}2", f"{prefix}3",
                                  f"{prefix}4"]


@pytest.mark.parametrize("input_filename, params", [
    ("denovo_import/variants_VCF_style.tsv", {"add_chrom_prefix": "chr"}),
    ("denovo_import/variants_VCF_style_chr.tsv", {"del_chrom_prefix": "chr"}),
])
def test_variants_have_adjusted_chrom(simple_denovo_loader,
                                      input_filename, params):
    loader = simple_denovo_loader(input_filename, params)
    is_add = "add_chrom_prefix" in params

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    for summary_variant, _ in variants:
        if is_add:
            assert summary_variant.chromosome.startswith("chr")
        else:
            assert not summary_variant.chromosome.startswith("chr")


@pytest.mark.parametrize("input_filename, params", [
    ("denovo_import/variants_VCF_style.tsv", {"add_chrom_prefix": "chr"}),
    ("denovo_import/variants_VCF_style_chr.tsv", {"del_chrom_prefix": "chr"}),
])
def test_reset_regions_with_adjusted_chrom(simple_denovo_loader,
                                           input_filename, params):
    loader = simple_denovo_loader(input_filename, params)
    prefix = params.get("add_chrom_prefix", "")
    regions = [f"{prefix}1", f"{prefix}2"]

    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    unique_chroms = np.unique([sv.chromosome for sv, _ in variants])
    assert (unique_chroms == regions).all()

    for sv, _ in variants:
        assert sv.position is not None
        assert sv.end_position is not None
        assert sv.position == sv.end_position

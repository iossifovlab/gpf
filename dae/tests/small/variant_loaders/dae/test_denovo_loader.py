# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.families_data import FamiliesData
from dae.utils.regions import Region
from dae.variants_loaders.dae.loader import DenovoLoader


@pytest.fixture
def denovo_loader(
    denovo_families: FamiliesData,
) -> Callable[
        [pathlib.Path, dict[str, str], ReferenceGenome], DenovoLoader]:

    def ctor(
        denovo_filename: pathlib.Path,
        additional_params: dict[str, str],
        genome: ReferenceGenome,
    ) -> DenovoLoader:
        params = {
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
            **additional_params,
        }
        return DenovoLoader(
            denovo_families,
            str(denovo_filename),
            genome=genome,
            params=params,
        )

    return ctor


def test_loader_chromosome_names(
    denovo_loader: Callable[
        [pathlib.Path, dict[str, str], ReferenceGenome], DenovoLoader],
    denovo_vcf_style: pathlib.Path,
    acgt_genome_19: ReferenceGenome,
) -> None:
    loader = denovo_loader(denovo_vcf_style, {}, acgt_genome_19)
    assert loader.chromosomes == ["1", "2", "3"]


def test_loader_chromosome_names_add_prefix(
    denovo_loader: Callable[
        [pathlib.Path, dict[str, str], ReferenceGenome], DenovoLoader],
    denovo_vcf_style: pathlib.Path,
    acgt_genome_38: ReferenceGenome,
) -> None:
    loader = denovo_loader(
        denovo_vcf_style, {"add_chrom_prefix": "chr"}, acgt_genome_38)
    assert loader.chromosomes == ["chr1", "chr2", "chr3"]


def test_loader_chromosome_names_del_prefix(
    denovo_loader: Callable[
        [pathlib.Path, dict[str, str], ReferenceGenome], DenovoLoader],
    denovo_vcf_style_chr: pathlib.Path,
    acgt_genome_19: ReferenceGenome,
) -> None:
    loader = denovo_loader(
        denovo_vcf_style_chr, {"del_chrom_prefix": "chr"}, acgt_genome_19)
    assert loader.chromosomes == ["1", "2", "3"]


def test_variants_chromosome_names(
    denovo_loader: Callable[
        [pathlib.Path, dict[str, str], ReferenceGenome], DenovoLoader],
    denovo_vcf_style: pathlib.Path,
    acgt_genome_19: ReferenceGenome,
) -> None:
    loader = denovo_loader(denovo_vcf_style, {}, acgt_genome_19)
    variants = list(loader.full_variants_iterator())
    assert len(variants) == 4
    chromsomes = {sv.chromosome for sv, _ in variants}
    assert chromsomes == {"1", "2", "3"}


def test_variants_chromosome_names_del_prefix(
    denovo_loader: Callable[
        [pathlib.Path, dict[str, str], ReferenceGenome], DenovoLoader],
    acgt_genome_19: ReferenceGenome,
    denovo_vcf_style_chr: pathlib.Path,
) -> None:
    loader = denovo_loader(
        denovo_vcf_style_chr, {"del_chrom_prefix": "chr"}, acgt_genome_19)
    variants = list(loader.full_variants_iterator())
    assert len(variants) == 4
    chromsomes = {sv.chromosome for sv, _ in variants}
    assert chromsomes == {"1", "2", "3"}


def test_variants_chromosome_names_add_prefix(
    denovo_loader: Callable[
        [pathlib.Path, dict[str, str], ReferenceGenome], DenovoLoader],
    acgt_genome_38: ReferenceGenome,
    denovo_vcf_style: pathlib.Path,
) -> None:
    loader = denovo_loader(
        denovo_vcf_style, {"add_chrom_prefix": "chr"}, acgt_genome_38)
    variants = list(loader.full_variants_iterator())
    assert len(variants) == 4
    chromsomes = {sv.chromosome for sv, _ in variants}
    assert chromsomes == {"chr1", "chr2", "chr3"}


def test_reset_regions_with_chrom(
    denovo_loader: Callable[
        [pathlib.Path, dict[str, str], ReferenceGenome], DenovoLoader],
    denovo_vcf_style: pathlib.Path,
    acgt_genome_19: ReferenceGenome,
) -> None:
    loader = denovo_loader(denovo_vcf_style, {}, acgt_genome_19)
    regions = [Region.from_str("1"), Region.from_str("2")]

    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 3
    assert {sv.chromosome for sv, _ in variants} == {"1", "2"}


def test_reset_regions_with_chrom_del_prefix(
    denovo_loader: Callable[
        [pathlib.Path, dict[str, str], ReferenceGenome], DenovoLoader],
    acgt_genome_19: ReferenceGenome,
    denovo_vcf_style_chr: pathlib.Path,
) -> None:
    loader = denovo_loader(
        denovo_vcf_style_chr, {"del_chrom_prefix": "chr"}, acgt_genome_19)
    regions = [Region.from_str("1"), Region.from_str("2")]

    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 3
    assert {sv.chromosome for sv, _ in variants} == {"1", "2"}


def test_reset_regions_with_chrom_add_prefix(
    denovo_loader: Callable[
        [pathlib.Path, dict[str, str], ReferenceGenome], DenovoLoader],
    acgt_genome_38: ReferenceGenome,
    denovo_vcf_style: pathlib.Path,
) -> None:
    loader = denovo_loader(
        denovo_vcf_style,
        {"add_chrom_prefix": "chr"},
        acgt_genome_38)
    regions = [Region.from_str("chr1"), Region.from_str("chr2")]

    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 3
    assert {sv.chromosome for sv, _ in variants} == {"chr1", "chr2"}

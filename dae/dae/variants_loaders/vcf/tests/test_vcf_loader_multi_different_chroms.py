# pylint: disable=W0621,C0114,C0116,W0212,W0613
import numpy as np
import pytest

from dae.genomic_resources.testing import setup_pedigree, setup_vcf
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.loader import FamiliesLoader
from dae.testing.acgt_import import acgt_gpf
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture()
def gpf_instance(
        tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("instance")
    gpf_instance = acgt_gpf(root_path)
    return gpf_instance


@pytest.fixture()
def quad_ped(
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    root_path = tmp_path_factory.mktemp("quad_ped")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1	        mom1	    0	    0	    2	1   	mom
    f1	        dad1	    0	    0	    1	1   	dad
    f1	        ch1	        dad1	mom1	2	2   	prb
    f1	        ch2	        dad1	mom1	1	1   	sib
    """)

    return str(ped_path)


@pytest.fixture()
def multi_contig_vcf(
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    root_path = tmp_path_factory.mktemp("multi_contig_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    ##contig=<ID=chr3>
    ##contig=<ID=chr4>
    #CHROM	POS	    ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    chr1   	3   	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    chr1   	13  	.	T	G,A	        .	    .   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    chr1   	15  	.	T	G,A	        .	    .   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    chr2   	16  	.	T	G,A	        .	    .   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    chr3   	23  	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3   	25  	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3   	29   	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    chr4   	44  	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    chr4   	55   	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    chr4   	95  	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3	2/2	2/2	2/2	2/2	2/2	2/2
    """) # noqa

    return str(vcf_path)


@pytest.fixture()
def multi_contig_vcf_gz(
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    root_path = tmp_path_factory.mktemp("multi_contig_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    ##contig=<ID=chr3>
    ##contig=<ID=chr4>
    #CHROM	POS	    ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom 	dad 	ch1 	ch2 	ch3 	gma 	gpa
    chr1   	3 	    .	T	G,A	        .	    .   	.   	GT  	0/0 	0/0 	0/0 	0/0 	0/0 	0/0	    0/0
    chr1   	13	    .	T	G,A	        .	    .   	.   	GT  	0/2 	0/0 	0/0 	0/0 	0/0 	0/0 	0/0
    chr1   	15  	.	T	G,A	        .	    .   	.   	GT  	./. 	./. 	./. 	./. 	./. 	./. 	./.
    chr2   	16  	.	T	G,A	        .	    .   	.   	GT  	0/1 	0/0 	0/0 	0/0 	0/2 	0/0	    0/0
    chr3   	23  	.	T	G,A	        .	    .   	.   	GT  	0/0 	0/0 	./. 	0/0 	0/0 	0/0	    0/0
    chr3   	25  	.	T	G	        .	    .   	.   	GT  	0/0 	0/0 	./. 	0/0 	0/0 	0/0	    0/0
    chr3   	29  	.	T	G	        .	    .   	.   	GT  	0/0 	0/0 	./. 	0/0 	0/1 	0/0	    0/0
    chr4   	44  	.	T	G	        .	    .   	.   	GT  	0/0 	0/0 	0/0 	1/1 	0/1 	0/0	    0/0
    chr4   	55  	.	T	G	        .	    .   	.   	GT  	0/0 	0/0 	0/0 	0/1 	0/0 	0/0	    1/1
    chr4   	95  	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3 	2/2 	2/2 	2/2 	2/2 	2/2	2/2
    """) # noqa

    return str(vcf_path)


@pytest.fixture()
def multi_generational_ped(
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    root_path = tmp_path_factory.mktemp("multi_contig_chr_ped")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f	        gpa     	0	    0	    1	1   	paternal_grandfather
    f	        gma     	0	    0	    2	1   	paternal_grandmother
    f	        mom     	0	    0	    2	1   	mom
    f	        dad     	gpa	    gma	    1	1   	dad
    f	        ch1     	dad	    mom	    2	2   	prb
    f	        ch2     	dad	    mom	    2	1   	sib
    f	        ch3     	dad	    mom	    2	1   	sib
    """)

    return str(ped_path)


@pytest.fixture()
def multi_contig_chr_vcf(
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    root_path = tmp_path_factory.mktemp("multi_contig_chr_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    ##contig=<ID=chr3>
    ##contig=<ID=chr4>
    #CHROM	POS 	ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    chr1	3  	    .	T	G,A	        .	    .   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	13  	.	T	G,A	        .	    .   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	15  	.	T	G,A	        .	    .   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    chr2	16  	.	T	G,A	        .	    .   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    chr3	23  	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	25   	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	29   	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    chr4	44   	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    chr4	55  	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    chr4	95  	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3	2/2	2/2	2/2	2/2	2/2	2/2
    """) # noqa

    return str(vcf_path)


@pytest.fixture()
def multi_contig_chr_vcf_gz(
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    root_path = tmp_path_factory.mktemp("multi_contig_chr_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    ##contig=<ID=chr3>
    ##contig=<ID=chr4>
    #CHROM	POS 	ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    chr1	3    	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	13   	.	T	G,A	        .	    .   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	15    	.	T	G,A	        .	    .   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    chr2	16  	.	T	G,A	        .	    .   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    chr3	23   	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	25   	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	29    	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    chr4	44    	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    chr4	55     	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    chr4	95  	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3	2/2	2/2	2/2	2/2	2/2	2/2
    """) # noqa

    return str(vcf_path)


def test_chromosomes_have_adjusted_chrom_add_prefix(
    quad_ped: str,
    multi_contig_vcf: str,
    gpf_instance: GPFInstance,
) -> None:
    ped_file = quad_ped

    family_loader = FamiliesLoader(ped_file).load()
    loader = VcfLoader(
        family_loader,
        [multi_contig_vcf],
        gpf_instance.reference_genome,
        params={"add_chrom_prefix": "chr"})

    assert loader.chromosomes == ["chrchr1", "chrchr2", "chrchr3", "chrchr4"]


def test_chromosomes_have_adjusted_chrom_del_prefix(
    multi_generational_ped: str,
    multi_contig_chr_vcf: str,
    gpf_instance: GPFInstance,
) -> None:
    ped_file = multi_generational_ped

    family_loader = FamiliesLoader(ped_file).load()
    loader = VcfLoader(
        family_loader,
        [multi_contig_chr_vcf],
        gpf_instance.reference_genome,
        params={"del_chrom_prefix": "chr"},
    )

    assert loader.chromosomes == ["1", "2", "3", "4"]


def test_variants_have_adjusted_chrom_add_prefix(
    quad_ped: str,
    multi_contig_vcf: str,
    gpf_instance: GPFInstance,
) -> None:
    ped_file = quad_ped

    family_loader = FamiliesLoader(ped_file).load()
    loader = VcfLoader(
        family_loader,
        [multi_contig_vcf],
        gpf_instance.reference_genome,
        params={"add_chrom_prefix": "chr"},
    )

    variants = list(loader.full_variants_iterator())

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    for summary_variant, _ in variants:
        assert summary_variant.chromosome.startswith("chr")


def test_variants_have_adjusted_chrom_del_prefix(
    multi_generational_ped: str,
    multi_contig_chr_vcf: str,
    gpf_instance: GPFInstance,
) -> None:
    ped_file = multi_generational_ped

    family_loader = FamiliesLoader(ped_file).load()
    loader = VcfLoader(
        family_loader,
        [multi_contig_chr_vcf],
        gpf_instance.reference_genome,
        params={"del_chrom_prefix": "chr"})

    list(loader.full_variants_iterator())

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    for summary_variant, _ in variants:
        assert not summary_variant.chromosome.startswith("chr")


def test_reset_regions_with_adjusted_chrom_add_prefix(
    quad_ped: str,
    multi_contig_vcf_gz: str,
    gpf_instance: GPFInstance,
) -> None:
    ped_file = quad_ped

    family_loader = FamiliesLoader(ped_file).load()
    loader = VcfLoader(
        family_loader,
        [multi_contig_vcf_gz],
        gpf_instance.reference_genome,
        params={"add_chrom_prefix": "chr"},
    )
    regions = ["chrchr1", "chrchr2"]

    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    unique_chroms = np.unique([sv.chromosome for sv, _ in variants])
    assert (unique_chroms == regions).all()


def test_reset_regions_with_adjusted_chrom_del_prefix(
    quad_ped: str,
    multi_contig_chr_vcf_gz: str,
    gpf_instance: GPFInstance,
) -> None:
    ped_file = quad_ped
    family_loader = FamiliesLoader(ped_file).load()

    loader = VcfLoader(
        family_loader,
        [multi_contig_chr_vcf_gz],
        gpf_instance.reference_genome,
        params={"del_chrom_prefix": "chr"})
    regions = ["1", "2"]

    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    unique_chroms = np.unique([sv.chromosome for sv, _ in variants])
    assert (unique_chroms == regions).all()

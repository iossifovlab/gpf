# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Literal

import pytest

from dae.genomic_resources.testing import setup_pedigree, setup_vcf
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.loader import FamiliesLoader
from dae.testing.acgt_import import acgt_gpf
from dae.variants.attributes import Inheritance
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture()
def gpf_instance(
        tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("instance")
    gpf_instance = acgt_gpf(root_path)
    return gpf_instance


# def test_transform_vcf_genotype():
#     genotypes = [
#         [0, 0, False],
#         [0, 1, False],
#         [1, 0, False],
#         [1, 1, False],
#         [0, True],
#         [1, True],
#     ]
#     expected = np.array([
#         [0, 0, 1, 1, 0, 1],
#         [0, 1, 0, 1, -2, -2],
#         [False, False, False, False, True, True]
#     ], dtype=GenotypeType)

#     assert np.array_equal(
#         expected, VcfLoader.transform_vcf_genotypes(genotypes)
#     )


@pytest.fixture()
def inheritance_trio_denovo_omission(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[str, str]:
    root_path = tmp_path_factory.mktemp("inheritance_trio_denovo_omission")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1		    mom1		0	    0	    2	1	    mom
    f1		    dad1		0	    0	    1	1	    dad
    f1		    ch1		    dad1	mom1	2	2	    prb
    """)

    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
    ##contig=<ID=chr1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	mom1	dad1	ch1
    chr1	1   	.	T	G	.	    .   	INH=OMI	GT	    0/0 	1/0 	1/1
    chr1	5   	.	T	G	.	    .   	INH=DEN	GT	    1/1 	1/1 	1/0
    chr1	12  	.	T	G	.	    .   	INH=DEN	GT	    1/1 	1/1 	0/1
    """)

    return (str(ped_path), str(vcf_path))


@pytest.mark.parametrize(
    "denovo_mode, total, unexpected_inheritance",
    [
        ("denovo", 3, {Inheritance.possible_denovo}),
        ("possible_denovo", 3, {Inheritance.denovo}),
        ("ignore", 1, {Inheritance.possible_denovo, Inheritance.denovo}),
        ("ala_bala", 3, {Inheritance.denovo}),
    ],
)
def test_vcf_denovo_mode(
    denovo_mode: Literal["denovo", "possible_denovo", "ignore", "ala_bala"],
    total: Literal[1, 3],
    unexpected_inheritance: set[Inheritance],
    inheritance_trio_denovo_omission: tuple[str, str],
    gpf_instance: GPFInstance,
) -> None:
    ped_path, vcf_path = inheritance_trio_denovo_omission
    families = FamiliesLoader(ped_path).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_denovo_mode": denovo_mode,
    }
    vcf_loader = VcfLoader(
        families,
        [vcf_path],
        gpf_instance.reference_genome,
        params=params,
    )

    assert vcf_loader is not None
    variants = list(vcf_loader.family_variants_iterator())
    assert len(variants) == total
    for fv in variants:
        for fa in fv.alleles:
            print(fa, fa.inheritance_in_members)
            assert set(
                fa.inheritance_in_members,
            ) & unexpected_inheritance == set([])


@pytest.mark.parametrize(
    "omission_mode, total, unexpected_inheritance",
    [
        ("omission", 3, {Inheritance.possible_omission}),
        ("possible_omission", 3, {Inheritance.omission}),
        ("ignore", 2, {Inheritance.possible_omission, Inheritance.omission}),
        ("ala_bala", 3, {Inheritance.omission}),
    ],
)
def test_vcf_omission_mode(
    omission_mode: Literal[
        "omission", "possible_omission", "ignore", "ala_bala",
    ],
    total: Literal[3, 2],
    unexpected_inheritance: set[Inheritance],
    inheritance_trio_denovo_omission: tuple[str, str],
    gpf_instance: GPFInstance,
) -> None:
    ped_path, vcf_path = inheritance_trio_denovo_omission
    families = FamiliesLoader(ped_path).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_omission_mode": omission_mode,
    }
    vcf_loader = VcfLoader(
        families,
        [vcf_path],
        gpf_instance.reference_genome,
        params=params,
    )

    assert vcf_loader is not None
    variants = list(vcf_loader.family_variants_iterator())
    assert len(variants) == total
    for fv in variants:
        for fa in fv.alleles:
            print(20 * "-")
            print(fa, fa.inheritance_in_members)
            assert set(
                fa.inheritance_in_members,
            ) & unexpected_inheritance == set([])


@pytest.fixture()
def f1_test(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[str, str]:
    root_path = tmp_path_factory.mktemp("inheritance_trio_denovo_omission")

    ped_path = setup_pedigree(root_path / "data" / "f1_test.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1	        mom1	    0	    0	    2	1   	mom
    f1	        dad1	    0	    0	    1	1   	dad
    f1	        ch1	        dad1	mom1	2	2   	prb
    f1	        ch2	        dad1	mom1	1	1   	sib
    """)

    vcf_path = setup_vcf(root_path / "data" / "f1_test.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
    ##contig=<ID=chr1>
    #CHROM	POS	 ID	REF	ALT	QUAL	FILTER	INFO	            FORMAT	mom1	dad1	ch1	  ch2
    chr1	2    .	C	T,A	.	    .	    EFF=SYN!MIS;INH=MIX	GT  	0/0 	0/1 	0/1	  0/2
    chr1    15   .	C	T,A	.	    .	    EFF=SYN!MIS;INH=UKN	GT  	./. 	./. 	./.	  ./.
    chr1    20   .	G	A,T	.	    .	    EFF=SYN!MIS;INH=MIX	GT	    0/0 	0/0	    ./.	  0/0
    chr1    55   .	C	T,A	.	    .	    EFF=SYN!MIS;INH=DEN	GT	    0/0 	0/0	    0/1	  0/0
    chr1    70   .	A	G,T	.	    .	    EFF=SYN!MIS;INH=OMI	GT	    1/1 	0/0 	0/1	  0/0
    chr1    77   .	G	A,T	.	    .	    EFF=SYN!MIS;INH=MIX	GT	    1/0 	0/0 	0/.	  0/2
    chr1    97   .	T	C,A	.	    .	    EFF=SYN!MIS;INH=OMI	GT	    1/1 	2/2 	1/1	  2/2
    """) # noqa

    return (str(ped_path), str(vcf_path))


@pytest.mark.parametrize(
    "vcf_include_reference_genotypes,"
    "vcf_include_unknown_family_genotypes,"
    "vcf_include_unknown_person_genotypes,count",
    [
        (True, True, True, 7),
        (True, True, False, 4),
        (True, False, True, 6),
        (False, True, True, 7),
        (True, False, False, 4),
        (False, False, False, 4),
    ],
)
def test_vcf_loader_params(
    f1_test: tuple[str, str],
    vcf_include_reference_genotypes: bool,
    vcf_include_unknown_family_genotypes: bool,
    vcf_include_unknown_person_genotypes: bool,
    count: bool,
    gpf_instance: GPFInstance,
) -> None:
    params = {
        "vcf_include_reference_genotypes":
        vcf_include_reference_genotypes,
        "vcf_include_unknown_family_genotypes":
        vcf_include_unknown_family_genotypes,
        "vcf_include_unknown_person_genotypes":
        vcf_include_unknown_person_genotypes,
    }
    ped_path, vcf_path = f1_test
    families = FamiliesLoader(ped_path).load()
    vcf_loader = VcfLoader(families,
                           [vcf_path],
                           gpf_instance.reference_genome,
                           params=params)

    variants = list(vcf_loader.family_variants_iterator())
    assert len(variants) == count


@pytest.fixture()
def simple_family(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, str]:
    root_path = tmp_path_factory.mktemp("simple_family")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f	        gpa     	0   	0   	1	1   	paternal_grandfather
    f	        gma     	0   	0   	2	1   	paternal_grandmother
    f	        mom     	0   	0   	2	1   	mom
    f	        dad     	gpa 	gma 	1	1   	dad
    f	        ch1     	dad 	mom 	2	2   	prb
    f	        ch2     	dad 	mom 	2	1   	sib
    f	        ch3     	dad 	mom 	2	1   	sib
    """)

    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=chr1>
    #CHROM	POS	ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    chr1    1   .	T	G,A	        .   	.   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    chr1    11  .	T	G,A	        .   	.   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    chr1    14  .	T	G,A	        .   	.   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    chr1    23  .	C	G,A	        .   	.   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    chr1    34  .	T	G,A	        .   	.   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr1    42  .	T	G	        .   	.   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr1    50  .	A	G	        .   	.   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    chr1    55  .	T	G	        .   	.   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    chr1    64  .	C	G	        .   	.   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    chr1    77  .	T	GA,AA,CA,CC	.   	.   	.   	GT  	2/3	2/2	2/1	2/2	2/2	2/2	2/2
    """) # noqa

    return str(ped_path), str(vcf_path)


def test_family_variants(
    simple_family: tuple[str, str],
    gpf_instance: GPFInstance,
) -> None:
    ped_filename, vcf_filename = simple_family
    families = FamiliesLoader(ped_filename).load()

    vcf_loader = VcfLoader(
        families,
        [vcf_filename],
        gpf_instance.reference_genome,
    )
    variants = list(vcf_loader.full_variants_iterator())
    assert len(variants) == 10

    family_variants = [v[1] for v in variants]
    exp_num_fam_variants_and_alleles = [
        # (num variants, num alleles)
        (0, 0),  # 1st variant is not found in any individual
        (1, 2),  # only the 2nd alt allele of the second variant is found
        (0, 0),  # the 3rd variant is unknown across the board
        (1, 3),  # the 4th variant is found in 1 individual (similar to 2nd)
        (0, 0),  # the 5th, 6th and 7th have missing values
        (0, 0),
        (0, 0),
        (1, 2),  # the 8th is a normal-looking variant
        (1, 2),  # the 9th is a normal-looking variant
        (1, 4),  # the 10th is found in all individuals
    ]

    for i, fam_variants in enumerate(family_variants):
        exp_num_variants, exp_num_alleles = exp_num_fam_variants_and_alleles[i]
        assert len(fam_variants) == exp_num_variants
        assert sum(len(fv.alleles) for fv in fam_variants) == exp_num_alleles

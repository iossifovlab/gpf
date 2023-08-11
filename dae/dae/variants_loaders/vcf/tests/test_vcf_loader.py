# pylint: disable=W0621,C0114,C0116,W0212,W0613
from pathlib import Path
from typing import Any
import pytest
from dae.import_tools.import_tools import construct_import_annotation_pipeline
from dae.variants_loaders.dae.loader import DenovoLoader
from dae.variants_loaders.raw.loader import AnnotationPipelineDecorator
from dae.variants.attributes import Inheritance
from dae.variants_loaders.vcf.loader import VcfLoader
from dae.configuration.gpf_config_parser import DefaultBox
from dae.genomic_resources.testing import setup_pedigree, setup_vcf
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing.acgt_import import acgt_gpf
from dae.pedigrees.loader import FamiliesLoader


@pytest.fixture
def gpf_instance(
        tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("instance")
    gpf_instance = acgt_gpf(root_path)
    return gpf_instance


@pytest.fixture
def quads_f1_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("quads_f1")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId  personId	dadId	momId	sex	status	role
    f1	      mom1	    0	    0	    2	1	    mom
    f1	      dad1	    0	    0	    1	1	    dad
    f1	      prb1	    dad1	mom1	1	2	    prb
    f1	      sib1	    dad1	mom1	2	2	    sib
    """)
    return ped_path


@pytest.fixture
def quads_f1_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("quads_f1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    ##contig=<ID=2>
    #CHROM	POS	    ID	REF	ALT	QUAL  FILTER  INFO	FORMAT	mom1  dad1	prb1  sib1
    1	    11539	.	T	G	.	  .	      .	    GT	    0/1	  0/0	0/1	  0/0
    2	    11540	.	T	G	.	  .	      .	    GT	    0/0	  0/1	0/1	  0/0
    """)
    return vcf_path


def vcf_loader_data(prefix: str, pedigree: Path, vcf: Path) -> DefaultBox:
    conf = {
        "prefix": prefix,
        "pedigree": str(pedigree),
        "vcf": str(vcf)
    }

    return DefaultBox(conf)


@pytest.fixture()
def vcf_variants_loaders(gpf_instance):
    annotation_pipeline = construct_import_annotation_pipeline(
        gpf_instance
    )

    def builder(
        path,
        params={
            "vcf_include_reference_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
            "vcf_include_unknown_person_genotypes": True,
            "vcf_denovo_mode": "denovo",
            "vcf_omission_mode": "omission",
        },
    ):
        config = path

        families_loader = FamiliesLoader(config.pedigree)
        families = families_loader.load()

        loaders = []

        if config.denovo:
            denovo_loader = DenovoLoader(
                families,
                config.denovo,
                gpf_instance.reference_genome,
                params={
                    "denovo_genotype": "genotype",
                    "denovo_family_id": "family",
                    "denovo_chrom": "chrom",
                    "denovo_pos": "pos",
                    "denovo_ref": "ref",
                    "denovo_alt": "alt",
                }
            )
            loaders.append(AnnotationPipelineDecorator(
                denovo_loader, annotation_pipeline))

        vcf_loader = VcfLoader(
            families,
            [config.vcf],
            gpf_instance.reference_genome,
            params=params
        )

        loaders.append(AnnotationPipelineDecorator(
            vcf_loader, annotation_pipeline
        ))

        return loaders

    return builder


def test_vcf_loader(
    request: pytest.FixtureRequest,
    gpf_instance: GPFInstance
) -> None:
    prefix, pedigree, vcf = ("quads_f1", "quads_f1_ped", "quads_f1_vcf")
    pedigree_path = request.getfixturevalue(pedigree)
    vcf_path = request.getfixturevalue(vcf)
    conf = vcf_loader_data(prefix, pedigree_path, vcf_path)
    print(conf)
    families_loader = FamiliesLoader(conf.pedigree)
    families = families_loader.load()

    loader = VcfLoader(
        families,
        [conf.vcf],
        gpf_instance.reference_genome,
        params={
            "vcf_include_reference_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
            "vcf_include_unknown_person_genotypes": True,
        },
    )
    assert loader is not None

    vars_new = list(loader.family_variants_iterator())

    for nfv in vars_new:
        print(nfv)


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


@pytest.fixture
def inheritance_trio_denovo_omission_ped(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("inheritance_trio_denovo_omission_ped")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1		    mom1		0	    0	    2	1	    mom
    f1		    dad1		0	    0	    1	1	    dad
    f1		    ch1		    dad1	mom1	2	2	    prb
    """)

    return ped_path


@pytest.fixture
def inheritance_trio_denovo_omission_vcf(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("inheritance_trio_denovo_omission_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	mom1	dad1	ch1
    1	    11515	.	T	G	.	    .   	INH=OMI	GT	    0/0 	1/0 	1/1
    1	    11523	.	T	G	.	    .   	INH=DEN	GT	    1/1 	1/1 	1/0
    1	    11524	.	T	G	.	    .   	INH=DEN	GT	    1/1 	1/1 	0/1
    """)

    return vcf_path


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
    denovo_mode,
    total,
    unexpected_inheritance,
    inheritance_trio_denovo_omission_ped: Path,
    inheritance_trio_denovo_omission_vcf: Path,
    gpf_instance: GPFInstance,
) -> None:
    families = FamiliesLoader(
        f"{str(inheritance_trio_denovo_omission_ped)}"
    ).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_denovo_mode": denovo_mode,
    }
    vcf_loader = VcfLoader(
        families,
        [f"{str(inheritance_trio_denovo_omission_vcf)}"],
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
                fa.inheritance_in_members
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
    omission_mode,
    total,
    unexpected_inheritance,
    inheritance_trio_denovo_omission_ped: Path,
    inheritance_trio_denovo_omission_vcf: Path,
    gpf_instance: GPFInstance,
) -> None:
    families = FamiliesLoader(
        f"{inheritance_trio_denovo_omission_ped}"
    ).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_omission_mode": omission_mode,
    }
    vcf_loader = VcfLoader(
        families,
        [f"{inheritance_trio_denovo_omission_vcf}"],
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
                fa.inheritance_in_members
            ) & unexpected_inheritance == set([])


@pytest.fixture
def f1_test_ped(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("inheritance_trio_denovo_omission_ped")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1	        mom1	    0	    0	    2	1   	mom
    f1	        dad1	    0	    0	    1	1   	dad
    f1	        ch1	        dad1	mom1	2	2   	prb
    f1	        ch2	        dad1	mom1	1	1   	sib
    """)

    return ped_path


@pytest.fixture
def f1_test_vcf(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("inheritance_trio_denovo_omission_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	            FORMAT	mom1	dad1	ch1	  ch2
    1	    878152	.	C	T,A	.	    .	    EFF=SYN!MIS;INH=MIX	GT  	0/0 	0/1 	0/1	  0/2
    1	    901923	.	C	T,A	.	    .	    EFF=SYN!MIS;INH=UKN	GT  	./. 	./. 	./.	  ./.
    1	    905951	.	G	A,T	.	    .	    EFF=SYN!MIS;INH=MIX	GT	    0/0 	0/0	    ./.	  0/0
    1	    905957	.	C	T,A	.	    .	    EFF=SYN!MIS;INH=DEN	GT	    0/0 	0/0	    0/1	  0/0
    1	    905966	.	A	G,T	.	    .	    EFF=SYN!MIS;INH=OMI	GT	    1/1 	0/0 	0/1	  0/0
    1	    906086	.	G	A,T	.	    .	    EFF=SYN!MIS;INH=MIX	GT	    1/0 	0/0 	0/.	  0/2
    1	    906092	.	T	C,A	.	    .	    EFF=SYN!MIS;INH=OMI	GT	    1/1 	2/2 	1/1	  2/2
    """)

    return vcf_path


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
    vcf_variants_loaders: Any,
    f1_test_ped: Path,
    f1_test_vcf: Path,
    vcf_include_reference_genotypes: bool,
    vcf_include_unknown_family_genotypes: bool,
    vcf_include_unknown_person_genotypes: bool,
    count: bool,
) -> None:
    params = {
        "vcf_include_reference_genotypes":
        vcf_include_reference_genotypes,
        "vcf_include_unknown_family_genotypes":
        vcf_include_unknown_family_genotypes,
        "vcf_include_unknown_person_genotypes":
        vcf_include_unknown_person_genotypes,
    }

    config = vcf_loader_data("f1_test", f1_test_ped, f1_test_vcf)

    variants_loader = vcf_variants_loaders(
        config, params=params)[0]
    variants = list(variants_loader.family_variants_iterator())
    assert len(variants) == count


@pytest.fixture
def simple_family_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("simple_family")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    1	    11539	.	T	G,A	        .   	.   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    1	    11540	.	T	G,A	        .   	.   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    1	    11541	.	T	G,A	        .   	.   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    1	    11542	.	C	G,A	        .   	.   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    1	    11543	.	T	G,A	        .   	.   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    1	    11544	.	T	G	        .   	.   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    1	    11545	.	A	G	        .   	.   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    1	    11546	.	T	G	        .   	.   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    1	    11547	.	C	G	        .   	.   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    1	    11548	.	T	GA,AA,CA,CC	.   	.   	.   	GT  	2/3	2/2	2/1	2/2	2/2	2/2	2/2
    """)
    return vcf_path


@pytest.fixture
def simple_family_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
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
    return ped_path


def test_family_variants(
    simple_family_vcf: Path,
    simple_family_ped: Path,
    gpf_instance: GPFInstance
) -> None:
    ped_filename = str(simple_family_ped)
    vcf_filename = str(simple_family_vcf)
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

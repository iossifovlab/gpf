# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from pathlib import Path
from typing import Any, Callable
import pytest
import numpy as np
from dae.variants_loaders.vcf.loader import VcfLoader
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
def multivcf_split1_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("mutlivcf_split1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1
    1	    865582	.	C	T	.	    .	    EFF=SYN	GT	    1/1	    0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1
    1	    865583	.	G	A	.	    .	    EFF=SYN	GT	    0/0	    1/1 	0/1 	0/1 	0/0 	1/1 	1/0 	0/1 	0/0 	1/1 	0/1 	0/1
    1	    865624	.	G	A	.	    .	    EFF=MIS	GT	    1/0	    0/0 	0/1 	0/0 	1/0 	0/0 	0/1 	0/0 	1/0 	0/0 	0/1 	0/0
    1	    865627	.	G	A	.	    .	    EFF=MIS	GT	    0/0	    1/0 	0/1 	0/0 	0/0 	1/0 	0/1 	0/0 	0/0 	1/1 	0/1 	1/0
    1	    865664	.	G	A	.	    .	    EFF=SYN	GT	    0/1	    0/0 	0/1 	0/0 	0/1 	0/0 	0/0 	0/1 	0/1 	0/0 	0/1 	0/0
    1	    865691	.	C	T	.	    .	    EFF=MIS	GT	    1/0	    1/0 	0/1 	0/0 	1/0 	1/0 	0/1 	0/0 	1/0 	1/1 	0/1 	0/1
    """)

    return vcf_path


@pytest.fixture
def multivcf_split2_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("mutlivcf_split1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f4.mom	f4.dad	f4.p1	f4.s1	f5.mom	f5.dad	f5.p1	f5.s1	f3.s1
    1	    865582	.	C	T	.   	.   	EFF=SYN	GT  	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	1/0 	0/1 	./.
    1	    865583	.	G	A	.   	.   	EFF=SYN	GT  	0/0 	1/1 	0/1 	0/1 	0/0 	1/1 	1/0 	0/1 	./.
    1	    865624	.	G	A	.   	.   	EFF=MIS	GT  	1/0 	0/0 	1/0 	0/0 	1/0 	0/0 	1/0 	0/0 	./.
    1	    865627	.	G	A	.   	.   	EFF=MIS	GT  	0/0 	1/1 	1/0 	0/0 	0/0 	1/1 	1/0 	1/0 	./.
    1	    865664	.	G	A	.   	.   	EFF=SYN	GT  	0/1 	0/0 	0/1 	0/0 	0/1 	0/0 	0/0 	0/1 	./.
    1	    865691	.	C	T	.   	.   	EFF=MIS	GT  	1/0 	1/1 	1/0 	1/0 	1/0 	1/1 	0/1 	0/1 	./.
    """)

    return vcf_path


@pytest.fixture
def multivcf_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("multivcf")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role	phenotype
    f1	        f1.mom  	0   	0	    2	1	    mom 	unaffected
    f1	        f1.dad  	0	    0	    1	1	    dad 	unaffected
    f1	        f1.p1   	f1.dad	f1.mom	1	2	    prb 	autism
    f1	        f1.s1   	f1.dad	f1.mom	2	2	    sib	    autism
    f2	        f2.mom  	0	    0	    2	1	    mom 	unaffected
    f2	        f2.dad  	0	    0	    1	1	    dad 	unaffected
    f2	        f2.p1   	f2.dad	f2.mom	1	2	    prb	    autism
    f2	        f2.s1   	f2.dad	f2.mom	2	2	    sib	    autism
    f3	        f3.mom  	0	    0	    2	1	    mom 	unaffected
    f3	        f3.dad  	0	    0	    1	1	    dad 	unaffected
    f3	        f3.p1   	f3.dad	f3.mom	1	2	    prb	    autism
    f3	        f3.s1   	f3.dad	f3.mom	2	2	    sib	    autism
    f4	        f4.mom  	0	    0	    2	1	    mom 	unaffected
    f4	        f4.dad  	0	    0	    1	1	    dad 	unaffected
    f4	        f4.p1   	f4.dad	f4.mom	1	2	    prb 	autism
    f4	        f4.s1   	f4.dad	f4.mom	2	2	    sib 	autism
    f5	        f5.mom  	0	    0	    2	1	    mom 	unaffected
    f5	        f5.dad  	0	    0	    1	1	    dad 	unaffected
    f5	        f5.p1   	f5.dad	f5.mom	1	2	    prb 	autism
    f5	        f5.s1   	f5.dad	f5.mom	2	2	    sib	    autism
    """)

    return ped_path


@pytest.fixture
def simple_vcf_loader(gpf_instance: GPFInstance):
    def _split_all_ext(filename):
        res, ext = os.path.splitext(filename)
        while len(ext) > 0:
            res, ext = os.path.splitext(res)
        return res
    def ctor(ped: Path, vcf: Path, additional_params: Any):
        ped_filename = _split_all_ext(str(ped)) + ".ped"
        families_loader = FamiliesLoader(ped_filename)
        families = families_loader.load()
        params = additional_params
        vcf_filename = vcf

        return VcfLoader(
            families, [str(vcf_filename)],
            genome=gpf_instance.reference_genome, params=params,
        )
    return ctor


def test_simple_vcf_loader_multi(
    gpf_instance: GPFInstance,
    multivcf_split1_vcf: Path,
    multivcf_split2_vcf: Path,
    multivcf_ped: Path
) -> None:
    vcf_filenames = [
        str(multivcf_split1_vcf),
        str(multivcf_split2_vcf),
    ]
    assert all(os.path.exists(fn) for fn in vcf_filenames)
    assert os.path.exists(str(multivcf_ped))

    families = FamiliesLoader(multivcf_ped).load()

    vcf_loader = VcfLoader(
        families,
        vcf_filenames,
        gpf_instance.reference_genome,
        fill_missing_ref=False,
    )
    assert vcf_loader is not None
    variants = list(vcf_loader.full_variants_iterator())
    assert len(variants) == 6


@pytest.fixture
def multivcf_original_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("multivcf_original")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role	phenotype
    f1	        f1.mom	    0	    0	    2	1	    mom 	unaffected
    f1	        f1.dad	    0	    0	    1	1	    dad 	unaffected
    f1	        f1.p1	    f1.dad	f1.mom	1	2	    prb 	autism
    f1	        f1.s1	    f1.dad	f1.mom	2	2	    sib 	autism
    f2	        f2.mom	    0	    0	    2	1	    mom 	unaffected
    f2	        f2.dad	    0	    0	    1	1	    dad 	unaffected
    f2	        f2.p1	    f2.dad	f2.mom	1	2	    prb 	autism
    f2	        f2.s1	    f2.dad	f2.mom	2	2	    sib 	autism
    f3	        f3.mom	    0	    0	    2	1	    mom 	unaffected
    f3	        f3.dad	    0	    0	    1	1	    dad 	unaffected
    f3	        f3.p1	    f3.dad	f3.mom	1	2	    prb 	autism
    f3	        f3.s1	    f3.dad	f3.mom	2	2	    sib 	autism
    f4	        f4.mom	    0	    0	    2	1	    mom 	unaffected
    f4	        f4.dad	    0	    0	    1	1	    dad 	unaffected
    f4	        f4.p1	    f4.dad	f4.mom	1	2	    prb 	autism
    f4	        f4.s1	    f4.dad	f4.mom	2	2	    sib 	autism
    f5	        f5.mom	    0	    0	    2	1	    mom 	unaffected
    f5	        f5.dad	    0	    0	    1	1	    dad 	unaffected
    f5	        f5.p1	    f5.dad	f5.mom	1	2	    prb 	autism
    f5	        f5.s1	    f5.dad	f5.mom	2	2	    sib 	autism
    """)

    return ped_path


@pytest.fixture
def multivcf_original_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("multivcf_original")
    vcf_path = setup_vcf(root_path / "vcf_path" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS 	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1	f4.mom	f4.dad	f4.p1	f4.s1	f5.mom	f5.dad	f5.p1	f5.s1
    1	    865582	.	C	T	.	    .   	EFF=SYN	GT  	1/1 	0/0 	0/1	    0/1 	1/1 	0/0 	0/1 	0/1 	1/1 	0/0	    0/1 	0/1 	1/1 	0/0 	0/1	    0/1 	1/1	    0/0 	1/0	    0/1
    1	    865583	.	G	A	.	    .   	EFF=SYN	GT  	0/0 	1/1 	0/1	    0/1 	0/0 	1/1 	1/0 	0/1 	0/0 	1/1	    0/1 	0/1 	0/0 	1/1 	0/1	    0/1 	0/0	    1/1 	1/0	    0/1
    1	    865624	.	G	A	.	    .   	EFF=MIS	GT  	1/0 	0/0 	0/1	    0/0 	1/0 	0/0 	0/1 	0/0 	1/0 	0/0	    0/1 	0/0 	1/0 	0/0 	1/0	    0/0 	1/0	    0/0 	1/0	    0/0
    1	    865627	.	G	A	.	    .   	EFF=MIS	GT  	0/0 	1/0 	0/1	    0/0 	0/0 	1/0 	0/1 	0/0 	0/0 	1/1	    0/1 	1/0 	0/0 	1/1 	1/0	    0/0 	0/0	    1/1 	1/0	    1/0
    1	    865664	.	G	A	.	    .   	EFF=SYN	GT  	0/1 	0/0 	0/1	    0/0 	0/1 	0/0 	0/0 	0/1 	0/1 	0/0	    0/1 	0/0 	0/1 	0/0 	0/1	    0/0 	0/1	    0/0 	0/0	    0/1
    1	    865691	.	C	T	.	    .   	EFF=MIS	GT  	1/0 	1/0 	0/1	    0/0 	1/0 	1/0 	0/1 	0/0 	1/0 	1/1	    0/1 	0/1 	1/0 	1/1 	1/0	    1/0 	1/0	    1/1 	0/1	    0/1
    """)

    return vcf_path


@pytest.mark.parametrize(
    "multivcf_files",
    [
        ["multivcf_split1_vcf", "multivcf_split2_vcf"],
        ["multivcf_original_vcf"],
    ],
)
def test_vcf_loader_multi(
    request: pytest.FixtureRequest,
    multivcf_files: list[str],
    multivcf_original_vcf: Path,
    multivcf_original_ped: Path,
    gpf_instance: GPFInstance
) -> None:
    # pylint: disable=too-many-locals,invalid-name

    multivcf_files = [
        str(request.getfixturevalue(f)) for f in multivcf_files
    ]

    families = FamiliesLoader(str(multivcf_original_ped)).load()
    families_multi = FamiliesLoader(str(multivcf_original_ped)).load()

    multi_vcf_loader = VcfLoader(
        families_multi, multivcf_files,
        gpf_instance.reference_genome,
        fill_missing_ref=False
    )
    assert multi_vcf_loader is not None
    # for sv, fvs in multi_vcf_loader.full_variants_iterator():
    #     print(sv, fvs)

    single_vcf = str(multivcf_original_vcf)
    single_loader = VcfLoader(
        families, [single_vcf], gpf_instance.reference_genome
    )
    assert single_loader is not None

    single_it = single_loader.full_variants_iterator()
    multi_it = multi_vcf_loader.full_variants_iterator()

    for s, m in zip(single_it, multi_it):
        assert s[0] == m[0]
        assert len(s[1]) == 5
        assert len(m[1]) == 5

        s_gt_f1 = s[1][0].gt
        m_gt_f1 = m[1][0].gt
        assert all((s_gt_f1 == m_gt_f1).flatten())

        s_gt_f2 = s[1][0].gt
        m_gt_f2 = m[1][0].gt
        assert all((s_gt_f2 == m_gt_f2).flatten())

        s_gt_f3 = s[1][0].gt
        m_gt_f3 = m[1][0].gt
        assert all((s_gt_f3 == m_gt_f3).flatten())

        s_gt_f4 = s[1][0].gt
        m_gt_f4 = m[1][0].gt
        assert all((s_gt_f4 == m_gt_f4).flatten())

        s_gt_f5 = s[1][0].gt
        m_gt_f5 = m[1][0].gt
        assert all((s_gt_f5 == m_gt_f5).flatten())


@pytest.fixture
def multivcf_missing1(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("multivcf_missing1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1
    1	    865582	.	C	T	.	    .	    EFF=SYN	GT  	1/1 	0/0 	0/1 	0/1	    1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1
    1	    865627	.	G	A	.	    .	    EFF=MIS	GT  	0/0 	1/0 	0/1 	0/0	    0/0 	1/0 	0/1 	0/0 	0/0 	1/1 	0/1 	1/0
    1	    865664	.	G	A	.	    .	    EFF=SYN	GT  	0/1 	0/0 	0/1 	0/0	    0/1 	0/0 	0/0 	0/1 	0/1 	0/0 	0/1 	0/0
    1	    865691	.	C	T	.	    .	    EFF=MIS	GT  	1/0 	1/0 	0/1 	0/0	    1/0 	1/0 	0/1 	0/0 	1/0 	1/1 	0/1 	0/1
    """)
    return vcf_path


@pytest.fixture
def multivcf_missing2(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("multivcf_missing2")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS	      ID  REF	ALT	    QUAL	FILTER	INFO	FORMAT	f4.mom	f4.dad	f4.p1	f4.s1	f5.mom	f5.dad	f5.p1	f5.s1
    1	    865582	  .	  C	    T	    .   	.	    EFF=SYN	GT  	1/1 	0/0 	0/1	    0/1 	1/1	    0/0 	1/0	    0/1
    1	    865583	  .	  G	    A	    .   	.	    EFF=SYN	GT  	0/0 	1/1 	0/1	    0/1 	0/0	    1/1 	1/0 	0/1
    1	    865624	  .	  G	    A	    .   	.	    EFF=MIS	GT  	1/0 	0/0 	1/0	    0/0 	1/0	    0/0 	1/0	    0/0
    1	    865627	  .	  G	    A	    .   	.	    EFF=MIS	GT  	0/0 	1/1 	1/0	    0/0 	0/0	    1/1 	1/0	    1/0
    1	    865664	  .	  G	    A	    .   	.	    EFF=SYN	GT  	0/1 	0/0 	0/1	    0/0 	0/1	    0/0 	0/0 	0/1
    1	    865691	  .	  C     T	    .   	.	    EFF=MIS	GT  	1/0 	1/1 	1/0	    1/0 	1/0	    1/1 	0/1	    0/1
    """)
    return vcf_path


@pytest.mark.parametrize(
    "fill_mode, fill_value", [["reference", 0], ["unknown", -1]]
)
def test_multivcf_loader_fill_missing(
    fill_mode: list[str, int],
    fill_value: list[str, int],
    multivcf_ped: Path,
    multivcf_missing1: Path,
    multivcf_missing2: Path,
    gpf_instance: GPFInstance
) -> None:
    # pylint: disable=too-many-locals

    multivcf_files = [
        str(multivcf_missing1),
        str(multivcf_missing2),
    ]
    families = FamiliesLoader(multivcf_ped).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_multi_loader_fill_in_mode": fill_mode,
    }
    multi_vcf_loader = VcfLoader(
        families, multivcf_files, gpf_instance.reference_genome,
        params=params
    )

    assert multi_vcf_loader is not None
    multi_it = multi_vcf_loader.full_variants_iterator()
    svs_fvs = list(multi_it)
    print(svs_fvs)
    first_present = svs_fvs[0]
    second_missing = svs_fvs[1]
    assert next(multi_it, None) is None

    gt1_f1 = first_present[1][0].genotype
    gt1_f1_expected = np.array([[1, 1], [0, 0], [0, 1], [0, 1]], dtype=np.int8)
    gt1_f5 = first_present[1][4].genotype
    gt1_f5_expected = np.array([[1, 1], [0, 0], [1, 0], [0, 1]], dtype=np.int8)
    assert all((gt1_f1 == gt1_f1_expected).flatten())
    assert all((gt1_f5 == gt1_f5_expected).flatten())
    print(second_missing[1][0], " ", second_missing[1][0].genotype)
    print(second_missing[1][1], " ", second_missing[1][1].genotype)

    gt2_f1 = second_missing[1][0].genotype
    gt2_f2 = second_missing[1][1].genotype
    gt2_f3 = second_missing[1][2].genotype
    gt2_f5 = second_missing[1][4].genotype

    gt2_f1_f2_f3_expected = np.array([[fill_value] * 2] * 4, dtype=np.int8)
    gt2_f5_expected = np.array([[0, 0], [1, 1], [1, 0], [0, 1]], dtype=np.int8)

    assert all((gt2_f1 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f2 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f3 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f5 == gt2_f5_expected).flatten())
    assert svs_fvs[0][0].ref_allele.position == 865582
    assert svs_fvs[1][0].ref_allele.position == 865583
    assert svs_fvs[2][0].ref_allele.position == 865624
    assert svs_fvs[3][0].ref_allele.position == 865627
    assert svs_fvs[4][0].ref_allele.position == 865664
    assert svs_fvs[5][0].ref_allele.position == 865691


# @pytest.mark.parametrize(
#     "fill_mode, fill_value", [["reference", 0], ["unknown", -1]]
# )
# def test_multivcf_loader_handle_all_unknown(
#     fixture_dirname, fill_mode, fill_value, gpf_instance_2013
# ):
#     ped_file = fixture_dirname("backends/multivcf.ped")

#     multivcf_files = [
#         fixture_dirname("backends/multivcf_unknown1.vcf"),
#         fixture_dirname("backends/multivcf_unknown2.vcf"),
#     ]
#     families = FamiliesLoader(ped_file).load()
#     params = {
#         "vcf_include_reference_genotypes": True,
#         "vcf_include_unknown_family_genotypes": True,
#         "vcf_include_unknown_person_genotypes": True,
#         "vcf_multi_loader_fill_in_mode": fill_mode,
#     }
#     multi_vcf_loader = VcfLoader(
#         families, multivcf_files, gpf_instance_2013.reference_genome,
#         params=params
#     )

#     assert multi_vcf_loader is not None
#     vs = list(multi_vcf_loader.family_variants_iterator())
#     assert len(vs) == 30


def test_collect_filenames_local(
    multivcf_split1_vcf: Path,
    multivcf_split2_vcf: Path,
) -> None:
    vcf_filenames = [str(multivcf_split1_vcf), str(multivcf_split2_vcf)]

    params = {
        "vcf_chromosomes": "1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;X;Y"
    }

    all_filenames, _ = VcfLoader._collect_filenames(params, vcf_filenames)

    assert len(all_filenames) == 2
    assert all_filenames[0] == str(multivcf_split1_vcf)
    assert all_filenames[1] == str(multivcf_split2_vcf)


def test_collect_filenames_s3(
    multivcf_split1_vcf: Path,
    multivcf_split2_vcf: Path,
    s3_filesystem,
    s3_tmp_bucket_url,
    mocker
) -> None:
    s3_filesystem.put(str(multivcf_split1_vcf),
                      f"{s3_tmp_bucket_url}/dir/multivcf_split1.vcf")
    s3_filesystem.put(str(multivcf_split2_vcf),
                      f"{s3_tmp_bucket_url}/dir/multivcf_split2.vcf")

    mocker.patch("dae.variants_loaders.vcf.loader.url_to_fs",
                 return_value=(s3_filesystem, None))

    vcf_filenames = ["s3://test-bucket/dir/multivcf_split[vc].vcf"]

    params = {
        "vcf_chromosomes": "1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;X;Y"
    }
    all_filenames, _ = VcfLoader._collect_filenames(params, vcf_filenames)

    assert len(all_filenames) == 2
    assert all_filenames[0] == "s3://test-bucket/dir/multivcf_split1.vcf"
    assert all_filenames[1] == "s3://test-bucket/dir/multivcf_split2.vcf"

@pytest.fixture
def multi_contig_ped(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("multi_contig_ped")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1	        mom1	    0	    0	    2	1   	mom
    f1	        dad1	    0	    0	    1	1   	dad
    f1	        ch1	        dad1	mom1	2	2   	prb
    f1	        ch2	        dad1	mom1	1	1   	sib
    """)

    return ped_path


@pytest.fixture
def multi_contig_vcf(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("multi_contig_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    ##contig=<ID=2>
    ##contig=<ID=3>
    ##contig=<ID=4>
    #CHROM	POS	    ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    1   	11539	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    1   	11540	.	T	G,A	        .	    .   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    1   	11541	.	T	G,A	        .	    .   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    2   	11542	.	T	G,A	        .	    .   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    3   	11543	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    3   	11544	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    3   	11545	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    4   	11546	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    4   	11547	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    4   	11548	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3	2/2	2/2	2/2	2/2	2/2	2/2
    """)

    return vcf_path


@pytest.fixture
def multi_contig_vcf_gz(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("multi_contig_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    ##contig=<ID=2>
    ##contig=<ID=3>
    ##contig=<ID=4>
    #CHROM	POS	    ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    1   	11539	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    1   	11540	.	T	G,A	        .	    .   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    1   	11541	.	T	G,A	        .	    .   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    2   	11542	.	T	G,A	        .	    .   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    3   	11543	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    3   	11544	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    3   	11545	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    4   	11546	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    4   	11547	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    4   	11548	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3	2/2	2/2	2/2	2/2	2/2	2/2
    """)

    return vcf_path


@pytest.fixture
def multi_contig_chr_ped(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
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

    return ped_path


@pytest.fixture
def multi_contig_chr_vcf(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("multi_contig_chr_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    ##contig=<ID=chr3>
    ##contig=<ID=chr4>
    #CHROM	POS 	ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    chr1	11539	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	11540	.	T	G,A	        .	    .   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	11541	.	T	G,A	        .	    .   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    chr2	11542	.	T	G,A	        .	    .   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    chr3	11543	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	11544	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	11545	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    chr4	11546	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    chr4	11547	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    chr4	11548	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3	2/2	2/2	2/2	2/2	2/2	2/2

    """)

    return vcf_path


@pytest.fixture
def multi_contig_chr_vcf_gz(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("multi_contig_chr_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    ##contig=<ID=chr3>
    ##contig=<ID=chr4>
    #CHROM	POS 	ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    chr1	11539	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	11540	.	T	G,A	        .	    .   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	11541	.	T	G,A	        .	    .   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    chr2	11542	.	T	G,A	        .	    .   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    chr3	11543	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	11544	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	11545	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    chr4	11546	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    chr4	11547	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    chr4	11548	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3	2/2	2/2	2/2	2/2	2/2	2/2

    """)

    return vcf_path


@pytest.mark.parametrize("input_filename, params", [
    (["multi_contig_ped", "multi_contig_vcf"], {"add_chrom_prefix": "chr"}),
    (["multi_contig_chr_ped", "multi_contig_chr_vcf"], {"del_chrom_prefix": "chr"}),
])
def test_chromosomes_have_adjusted_chrom(
    request: pytest.FixtureRequest,
    simple_vcf_loader: Callable[[Path, Path, dict[str, str]], VcfLoader],
    input_filename: list[str],
    params: dict[str, str]
) -> None:
    ped = request.getfixturevalue(input_filename[0])
    vcf = request.getfixturevalue(input_filename[1])
    loader = simple_vcf_loader(ped, vcf, params)

    prefix = params.get("add_chrom_prefix", "")
    assert loader.chromosomes == [f"{prefix}1", f"{prefix}2", f"{prefix}3",
                                  f"{prefix}4"]


@pytest.mark.parametrize("input_filename, params", [
    (["multi_contig_ped", "multi_contig_vcf"], {"add_chrom_prefix": "chr"}),
    (["multi_contig_chr_ped", "multi_contig_chr_vcf"], {"del_chrom_prefix": "chr"}),
])
def test_variants_have_adjusted_chrom(
    request: pytest.FixtureRequest,
    simple_vcf_loader: Callable[[Path, Path, dict[str, str]], VcfLoader],
    input_filename: list[str],
    params: dict[str, str]
) -> None:
    ped = request.getfixturevalue(input_filename[0])
    vcf = request.getfixturevalue(input_filename[1])
    loader = simple_vcf_loader(ped, vcf, params)
    is_add = "add_chrom_prefix" in params

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    for summary_variant, _ in variants:
        if is_add:
            assert summary_variant.chromosome.startswith("chr")
        else:
            assert not summary_variant.chromosome.startswith("chr")


@pytest.mark.parametrize("input_filename, params", [
    (["multi_contig_ped", "multi_contig_vcf_gz"], {"add_chrom_prefix": "chr"}),
    (["multi_contig_chr_ped", "multi_contig_chr_vcf_gz"], {"del_chrom_prefix": "chr"}),
])
def test_reset_regions_with_adjusted_chrom(
    request: pytest.FixtureRequest,
    simple_vcf_loader: Callable[[Path, Path, dict[str, str]], VcfLoader],
    input_filename: list[str],
    params: dict[str, str]
) -> None:
    ped = request.getfixturevalue(input_filename[0])
    vcf = request.getfixturevalue(input_filename[1])

    loader = simple_vcf_loader(ped, vcf, params)
    prefix = params.get("add_chrom_prefix", "")
    regions = [f"{prefix}1", f"{prefix}2"]

    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    unique_chroms = np.unique([sv.chromosome for sv, _ in variants])
    assert (unique_chroms == regions).all()

# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

import numpy as np
import pytest

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.testing import (
    setup_pedigree,
    setup_vcf,
)
from dae.pedigrees.loader import FamiliesLoader
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture
def multivcf_split1_vcf(tmp_path_factory: pytest.TempPathFactory) -> str:
    root_path = tmp_path_factory.mktemp("mutlivcf_split1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    #CHROM	POS	 ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1
    chr1    4    .	C	T	.	    .	    EFF=SYN	GT	    1/1	    0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1
    chr1    13   .	G	A	.	    .	    EFF=SYN	GT	    0/0	    1/1 	0/1 	0/1 	0/0 	1/1 	1/0 	0/1 	0/0 	1/1 	0/1 	0/1
    chr1    15   .	G	A	.	    .	    EFF=MIS	GT	    1/0	    0/0 	0/1 	0/0 	1/0 	0/0 	0/1 	0/0 	1/0 	0/0 	0/1 	0/0
    chr1    23   .	G	A	.	    .	    EFF=MIS	GT	    0/0	    1/0 	0/1 	0/0 	0/0 	1/0 	0/1 	0/0 	0/0 	1/1 	0/1 	1/0
    chr1    44   .	G	A	.	    .	    EFF=SYN	GT	    0/1	    0/0 	0/1 	0/0 	0/1 	0/0 	0/0 	0/1 	0/1 	0/0 	0/1 	0/0
    chr1    55   .	C	T	.	    .	    EFF=MIS	GT	    1/0	    1/0 	0/1 	0/0 	1/0 	1/0 	0/1 	0/0 	1/0 	1/1 	0/1 	0/1
    """) # noqa

    return str(vcf_path)


@pytest.fixture
def multivcf_split2_vcf(tmp_path_factory: pytest.TempPathFactory) -> str:
    root_path = tmp_path_factory.mktemp("mutlivcf_split1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    #CHROM	POS	 ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f4.mom	f4.dad	f4.p1	f4.s1	f5.mom	f5.dad	f5.p1	f5.s1	f3.s1
    chr1    4 	 .	C	T	.   	.   	EFF=SYN	GT  	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	1/0 	0/1 	./.
    chr1    13   .	G	A	.   	.   	EFF=SYN	GT  	0/0 	1/1 	0/1 	0/1 	0/0 	1/1 	1/0 	0/1 	./.
    chr1    15	 .	G	A	.   	.   	EFF=MIS	GT  	1/0 	0/0 	1/0 	0/0 	1/0 	0/0 	1/0 	0/0 	./.
    chr1    23 	 .	G	A	.   	.   	EFF=MIS	GT  	0/0 	1/1 	1/0 	0/0 	0/0 	1/1 	1/0 	1/0 	./.
    chr1    44 	 .	G	A	.   	.   	EFF=SYN	GT  	0/1 	0/0 	0/1 	0/0 	0/1 	0/0 	0/0 	0/1 	./.
    chr1    55 	 .	C	T	.   	.   	EFF=MIS	GT  	1/0 	1/1 	1/0 	1/0 	1/0 	1/1 	0/1 	0/1 	./.
    """) # noqa

    return str(vcf_path)


@pytest.fixture
def multivcf_ped(tmp_path_factory: pytest.TempPathFactory) -> str:
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

    return str(ped_path)


def test_simple_vcf_loader_multi(
    acgt_genome: ReferenceGenome,
    multivcf_split1_vcf: str,
    multivcf_split2_vcf: str,
    multivcf_ped: str,
) -> None:
    vcf_filenames = [multivcf_split1_vcf, multivcf_split2_vcf]
    assert all(os.path.exists(fn) for fn in vcf_filenames)
    assert os.path.exists(str(multivcf_ped))

    families = FamiliesLoader(multivcf_ped).load()

    vcf_loader = VcfLoader(
        families,
        vcf_filenames,
        acgt_genome,
        fill_missing_ref=False,
    )
    assert vcf_loader is not None
    variants = list(vcf_loader.full_variants_iterator())
    assert len(variants) == 6


@pytest.fixture
def multivcf_original_vcf(tmp_path_factory: pytest.TempPathFactory) -> str:
    root_path = tmp_path_factory.mktemp("multivcf_original")
    vcf_path = setup_vcf(root_path / "vcf_path" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    #CHROM	POS 	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1	f4.mom	f4.dad	f4.p1	f4.s1	f5.mom	f5.dad	f5.p1	f5.s1
    chr1    4     	.	C	T	.	    .   	EFF=SYN	GT  	1/1 	0/0 	0/1	    0/1 	1/1 	0/0 	0/1 	0/1 	1/1 	0/0	    0/1 	0/1 	1/1 	0/0 	0/1	    0/1 	1/1	    0/0 	1/0	    0/1
    chr1    13   	.	G	A	.	    .   	EFF=SYN	GT  	0/0 	1/1 	0/1	    0/1 	0/0 	1/1 	1/0 	0/1 	0/0 	1/1	    0/1 	0/1 	0/0 	1/1 	0/1	    0/1 	0/0	    1/1 	1/0	    0/1
    chr1    15  	.	G	A	.	    .   	EFF=MIS	GT  	1/0 	0/0 	0/1	    0/0 	1/0 	0/0 	0/1 	0/0 	1/0 	0/0	    0/1 	0/0 	1/0 	0/0 	1/0	    0/0 	1/0	    0/0 	1/0	    0/0
    chr1    23   	.	G	A	.	    .   	EFF=MIS	GT  	0/0 	1/0 	0/1	    0/0 	0/0 	1/0 	0/1 	0/0 	0/0 	1/1	    0/1 	1/0 	0/0 	1/1 	1/0	    0/0 	0/0	    1/1 	1/0	    1/0
    chr1    44   	.	G	A	.	    .   	EFF=SYN	GT  	0/1 	0/0 	0/1	    0/0 	0/1 	0/0 	0/0 	0/1 	0/1 	0/0	    0/1 	0/0 	0/1 	0/0 	0/1	    0/0 	0/1	    0/0 	0/0	    0/1
    chr1    55   	.	C	T	.	    .   	EFF=MIS	GT  	1/0 	1/0 	0/1	    0/0 	1/0 	1/0 	0/1 	0/0 	1/0 	1/1	    0/1 	0/1 	1/0 	1/1 	1/0	    1/0 	1/0	    1/1 	0/1	    0/1
    """) # noqa

    return str(vcf_path)


def test_vcf_loader_multi(
    multivcf_split1_vcf: str,
    multivcf_split2_vcf: str,
    multivcf_original_vcf: str,
    multivcf_ped: str,
    acgt_genome: ReferenceGenome,
) -> None:
    # pylint: disable=too-many-locals,invalid-name

    families = FamiliesLoader(multivcf_ped).load()
    families_multi = FamiliesLoader(multivcf_ped).load()

    multi_vcf_loader = VcfLoader(
        families_multi, [multivcf_split1_vcf, multivcf_split2_vcf],
        acgt_genome,
        fill_missing_ref=False,
    )
    assert multi_vcf_loader is not None

    single_loader = VcfLoader(
        families, [multivcf_original_vcf], acgt_genome,
    )
    assert single_loader is not None

    single_it = single_loader.full_variants_iterator()
    multi_it = multi_vcf_loader.full_variants_iterator()

    for s, m in zip(single_it, multi_it, strict=True):
        assert s[0] == m[0]
        assert len(s[1]) == 5
        assert len(m[1]) == 5

        s_gt_f1 = s[1][0].gt
        m_gt_f1 = m[1][0].gt
        assert np.all(s_gt_f1 == m_gt_f1)

        s_gt_f2 = s[1][0].gt
        m_gt_f2 = m[1][0].gt
        assert np.all(s_gt_f2 == m_gt_f2)

        s_gt_f3 = s[1][0].gt
        m_gt_f3 = m[1][0].gt
        assert np.all(s_gt_f3 == m_gt_f3)

        s_gt_f4 = s[1][0].gt
        m_gt_f4 = m[1][0].gt
        assert np.all(s_gt_f4 == m_gt_f4)

        s_gt_f5 = s[1][0].gt
        m_gt_f5 = m[1][0].gt
        assert np.all(s_gt_f5 == m_gt_f5)


@pytest.fixture
def multivcf_missing1(tmp_path_factory: pytest.TempPathFactory) -> str:
    root_path = tmp_path_factory.mktemp("multivcf_missing1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1
    chr1	1   	.	C	T	.	    .	    EFF=SYN	GT  	1/1 	0/0 	0/1 	0/1	    1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1
    chr1	24  	.	G	A	.	    .	    EFF=MIS	GT  	0/0 	1/0 	0/1 	0/0	    0/0 	1/0 	0/1 	0/0 	0/0 	1/1 	0/1 	1/0
    chr1	44  	.	G	A	.	    .	    EFF=SYN	GT  	0/1 	0/0 	0/1 	0/0	    0/1 	0/0 	0/0 	0/1 	0/1 	0/0 	0/1 	0/0
    chr1	54  	.	C	T	.	    .	    EFF=MIS	GT  	1/0 	1/0 	0/1 	0/0	    1/0 	1/0 	0/1 	0/0 	1/0 	1/1 	0/1 	0/1
    """) # noqa
    return str(vcf_path)


@pytest.fixture
def multivcf_missing2(tmp_path_factory: pytest.TempPathFactory) -> str:
    root_path = tmp_path_factory.mktemp("multivcf_missing2")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    #CHROM	POS	      ID  REF	ALT	    QUAL	FILTER	INFO	FORMAT	f4.mom	f4.dad	f4.p1	f4.s1	f5.mom	f5.dad	f5.p1	f5.s1
    chr1    1     	  .	  C	    T	    .   	.	    EFF=SYN	GT  	1/1 	0/0 	0/1	    0/1 	1/1	    0/0 	1/0	    0/1
    chr1    4  	      .	  G	    A	    .   	.	    EFF=SYN	GT  	0/0 	1/1 	0/1	    0/1 	0/0	    1/1 	1/0 	0/1
    chr1    15  	  .	  G	    A	    .   	.	    EFF=MIS	GT  	1/0 	0/0 	1/0	    0/0 	1/0	    0/0 	1/0	    0/0
    chr1    24  	  .	  G	    A	    .   	.	    EFF=MIS	GT  	0/0 	1/1 	1/0	    0/0 	0/0	    1/1 	1/0	    1/0
    chr1    44   	  .	  G	    A	    .   	.	    EFF=SYN	GT  	0/1 	0/0 	0/1	    0/0 	0/1	    0/0 	0/0 	0/1
    chr1    54  	  .	  C     T	    .   	.	    EFF=MIS	GT  	1/0 	1/1 	1/0	    1/0 	1/0	    1/1 	0/1	    0/1
    """) # noqa
    return str(vcf_path)


@pytest.mark.parametrize(
    "fill_mode, fill_value", [
        ("reference", 0),
        ("unknown", -1),
    ],
)
def test_multivcf_loader_fill_missing(
    fill_mode: list[str | int],
    fill_value: list[str | int],
    multivcf_ped: str,
    multivcf_missing1: str,
    multivcf_missing2: str,
    acgt_genome: ReferenceGenome,
) -> None:
    # pylint: disable=too-many-locals

    multivcf_files = [multivcf_missing1, multivcf_missing2]
    families = FamiliesLoader(multivcf_ped).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_multi_loader_fill_in_mode": fill_mode,
    }
    multi_vcf_loader = VcfLoader(
        families, multivcf_files, acgt_genome,
        params=params,
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
    assert np.all(gt1_f1 == gt1_f1_expected)
    assert np.all(gt1_f5 == gt1_f5_expected)
    print(second_missing[1][0], " ", second_missing[1][0].genotype)
    print(second_missing[1][1], " ", second_missing[1][1].genotype)

    gt2_f1 = second_missing[1][0].genotype
    gt2_f2 = second_missing[1][1].genotype
    gt2_f3 = second_missing[1][2].genotype
    gt2_f5 = second_missing[1][4].genotype

    gt2_f1_f2_f3_expected = np.array([[fill_value] * 2] * 4, dtype=np.int8)
    gt2_f5_expected = np.array([[0, 0], [1, 1], [1, 0], [0, 1]], dtype=np.int8)

    assert np.all(gt2_f1 == gt2_f1_f2_f3_expected)
    assert np.all(gt2_f2 == gt2_f1_f2_f3_expected)
    assert np.all(gt2_f3 == gt2_f1_f2_f3_expected)
    assert np.all(gt2_f5 == gt2_f5_expected)
    assert svs_fvs[0][0].ref_allele.position == 1
    assert svs_fvs[1][0].ref_allele.position == 4
    assert svs_fvs[2][0].ref_allele.position == 15
    assert svs_fvs[3][0].ref_allele.position == 24
    assert svs_fvs[4][0].ref_allele.position == 44
    assert svs_fvs[5][0].ref_allele.position == 54

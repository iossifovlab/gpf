# pylint: disable=W0621,C0114,C0116,W0212,W0613

from pathlib import Path
from typing import List
import pytest
from dae.genomic_resources.testing import setup_pedigree, setup_vcf
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.loader import FamiliesLoader
from dae.testing.acgt_import import acgt_gpf
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture
def gpf_instance(
        tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("instance")
    gpf_instance = acgt_gpf(root_path)
    return gpf_instance


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
def multivcf_missing(
    tmp_path_factory: pytest.TempPathFactory
) -> List[str]:
    path_list = []

    root_path = tmp_path_factory.mktemp("multivcf_missing1_chr1")
    setup_vcf(root_path / "vcf_data" / "in_chr1.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1
    chr1	3   	.	C	T	.	    .   	EFF=SYN	GT	    1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1
    chr1    4   	.	G	A	.	    .   	EFF=MIS	GT	    0/0 	1/0 	0/1 	0/0 	0/0 	1/0 	0/1 	0/0 	0/0 	1/1 	0/1 	1/0
    chr1    7   	.	G	A	.	    .   	EFF=SYN	GT	    0/1 	0/0 	0/1 	0/0 	0/1 	0/0 	0/0 	0/1 	0/1 	0/0 	0/1 	0/0
    chr1	15      .	C	T	.	    .   	EFF=MIS	GT	    1/0 	1/0 	0/1 	0/0 	1/0 	1/0 	0/1 	0/0 	1/0 	1/1 	0/1 	0/1
    """)  # noqa

    setup_vcf(root_path / "vcf_data" / "in_chr2.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1
    chr1	16   	.	C	T	.	    .   	EFF=SYN	GT	    1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1
    chr1   	17  	.	G	A	.	    .   	EFF=MIS	GT	    0/0 	1/0 	0/1 	0/0 	0/0 	1/0 	0/1 	0/0 	0/0 	1/1 	0/1 	1/0
    chr1    21  	.	G	A	.	    .   	EFF=SYN	GT	    0/1 	0/0 	0/1 	0/0 	0/1 	0/0 	0/0 	0/1 	0/1 	0/0 	0/1 	0/0
    chr1    24  	.	C	T	.	    .   	EFF=MIS	GT	    1/0 	1/0 	0/1 	0/0 	1/0 	1/0 	0/1 	0/0 	1/0 	1/1 	0/1 	0/1
    """)  # noqa

    path_list.append(
        str(root_path / "vcf_data" / "in_chr[vc].vcf.gz")
    )

    root_path = tmp_path_factory.mktemp("multivcf_missing2_chr1")
    setup_vcf(root_path / "vcf_data" / "in_chr1.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1
    chr1	1   	.	C	T	.	    .   	EFF=SYN 	GT	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1
    chr1   	4   	.	G	A	.	    .   	EFF=MIS 	GT	0/0 	1/0 	0/1 	0/0 	0/0 	1/0 	0/1 	0/0 	0/0 	1/1 	0/1 	1/0
    chr1    7    	.	G	A	.	    .   	EFF=SYN 	GT	0/1 	0/0 	0/1 	0/0 	0/1 	0/0 	0/0 	0/1 	0/1 	0/0 	0/1 	0/0
    chr1	14  	.	C	T	.	    .   	EFF=MIS 	GT	1/0 	1/0 	0/1 	0/0 	1/0 	1/0 	0/1 	0/0 	1/0 	1/1 	0/1 	0/1
    """)  # noqa

    setup_vcf(root_path / "vcf_data" / "in_chr2.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1
    chr1    17   	.	C	T	.	    .   	EFF=SYN	GT	    1/1 	0/0	    0/1	    0/1	    1/1	    0/0	    0/1 	0/1 	1/1 	0/0 	0/1 	0/1
    chr1    21   	.	G	A	.	    .   	EFF=MIS	GT	    0/0	    1/0	    0/1	    0/0	    0/0 	1/0	    0/1 	0/0 	0/0 	1/1 	0/1 	1/0
    chr1    45   	.	G	A	.	    .   	EFF=SYN	GT	    0/1	    0/0	    0/1 	0/0	    0/1	    0/0	    0/0 	0/1 	0/1 	0/0 	0/1 	0/0
    chr1    65  	.	C	T	.	    .   	EFF=MIS	GT	    1/0 	1/0	    0/1 	0/0	    1/0	    1/0	    0/1 	0/0 	1/0 	1/1 	0/1 	0/1
    """)  # noqa

    path_list.append(
        str(root_path / "vcf_data" / "in_chr[vc].vcf.gz")
    )

    return path_list


def test_wild_vcf_loader_simple(
    multivcf_ped: Path,
    multivcf_missing: List[str],
    gpf_instance: GPFInstance
) -> None:
    ped_file = multivcf_ped

    families_loader = FamiliesLoader(ped_file)
    families = families_loader.load()

    variants_loader = VcfLoader(
        families,
        [multivcf_missing[0], multivcf_missing[1]],
        gpf_instance.reference_genome,
        params={"vcf_chromosomes": "1;2", },
    )
    assert variants_loader is not None

    assert len(variants_loader.vcf_loaders) == 2

    indexes = []
    for sv, _fvs in variants_loader.full_variants_iterator():
        indexes.append(sv.summary_index)

    assert indexes == list(range(len(indexes)))


@pytest.fixture
def multivcf_pedigree(
    tmp_path_factory: pytest.TempPathFactory
) -> List[str]:
    path_list = []

    root_path = tmp_path_factory.mktemp("multivcf_pedigree1_chr1")
    setup_vcf(root_path / "vcf_data" / "in_chr1.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.p1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1
    chr1	865582	.	C	T	.	    .   	EFF=SYN	GT  	1/1 	0/1 	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1
    chr1	865627	.	G	A	.	    .   	EFF=MIS	GT  	0/0 	0/1 	0/0 	1/0 	0/1 	0/0 	0/0 	1/1 	0/1 	1/0
    chr1	865664	.	G	A	.	    .   	EFF=SYN	GT  	0/1 	0/1 	0/1 	0/0 	0/0 	0/1 	0/1 	0/0 	0/1 	0/0
    chr1	865691	.	C	T	.	    .   	EFF=MIS	GT  	1/0 	0/1 	1/0 	1/0 	0/1 	0/0 	1/0 	1/1 	0/1 	0/1
    """) # noqa
    setup_vcf(root_path / "vcf_data" / "in_chr2.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.dad	f3.p1
    chr2	865582	.	C	T	.	    .   	EFF=SYN	GT  	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1 	0/0 	0/1
    chr2	865627	.	G	A	.	    .   	EFF=MIS	GT  	0/0 	1/0 	0/1 	0/0 	0/0 	1/0 	0/1 	0/0 	1/1 	0/1
    chr2	865664	.	G	A	.	    .   	EFF=SYN	GT  	0/1 	0/0 	0/1 	0/0 	0/1 	0/0 	0/0 	0/1 	0/0 	0/1
    chr2	865691	.	C	T	.	    .   	EFF=MIS	GT  	1/0 	1/0 	0/1 	0/0 	1/0 	1/0 	0/1 	0/0 	1/1 	0/1
    """) # noqa

    path_list.append(
        str(root_path / "vcf_data" / "in_chr[vc].vcf.gz")
    )
    root_path = tmp_path_factory.mktemp("multivcf_pedigree2_chr2")
    setup_vcf(root_path / "vcf_data" / "in_chr1.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f4.mom	f4.dad	f4.p1	f5.mom	f5.dad	f5.p1	f5.s1
    chr1	865582	.	C	T	.	    .   	EFF=SYN	GT  	1/1 	0/0 	0/1 	1/1 	0/0 	1/0 	0/1
    chr1	865583	.	G	A	.	    .   	EFF=SYN	GT  	0/0 	1/1 	0/1 	0/0 	1/1 	1/0 	0/1
    chr1	865624	.	G	A	.	    .   	EFF=MIS	GT  	1/0 	0/0 	1/0 	1/0 	0/0 	1/0 	0/0
    chr1	865627	.	G	A	.	    .   	EFF=MIS	GT  	0/0 	1/1 	1/0 	0/0 	1/1 	1/0 	1/0
    chr1	865664	.	G	A	.	    .   	EFF=SYN	GT  	0/1 	0/0 	0/1 	0/1 	0/0 	0/0 	0/1
    chr1	865691	.	C	T	.	    .   	EFF=MIS	GT  	1/0 	1/1 	1/0 	1/0 	1/1 	0/1 	0/1
    """) # noqa
    setup_vcf(root_path / "vcf_data" / "in_chr2.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f4.dad	f4.p1	f4.s1	f5.mom	f5.p1
    chr2	865582	.	C	T	.	    .   	EFF=SYN	GT	    0/0 	0/1 	0/1 	1/1 	1/0
    chr2	865583	.	G	A	.	    .   	EFF=SYN	GT	    1/1 	0/1 	0/1 	0/0 	1/0
    chr2	865624	.	G	A	.	    .   	EFF=MIS	GT	    0/0 	1/0 	0/0 	1/0 	1/0
    chr2	865627	.	G	A	.	    .   	EFF=MIS	GT	    1/1 	1/0 	0/0 	0/0 	1/0
    chr2	865664	.	G	A	.	    .   	EFF=SYN	GT	    0/0 	0/1 	0/0 	0/1 	0/0
    chr2	865691	.	C	T	.	    .   	EFF=MIS	GT	    1/1 	1/0 	1/0 	1/0 	0/1
    """) # noqa
    path_list.append(
        str(root_path / "vcf_data" / "in_chr[vc].vcf.gz")
    )
    return path_list


def test_wild_vcf_loader_pedigree(
    multivcf_pedigree: List[str],
    multivcf_ped: str,
    gpf_instance: GPFInstance
) -> None:

    vcf_file1 = multivcf_pedigree[0]
    vcf_file2 = multivcf_pedigree[1]
    ped_file = multivcf_ped

    families_loader = FamiliesLoader(ped_file)
    families = families_loader.load()

    variants_loader = VcfLoader(
        families,
        [vcf_file1, vcf_file2],
        gpf_instance.reference_genome,
        params={
            "vcf_chromosomes": "1;2",
            "vcf_pedigree_mode": "fixed",
            "vcf_include_unknown_person_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
        },
    )

    assert variants_loader is not None

    assert len(variants_loader.vcf_loaders) == 2
    for vcf_loader in variants_loader.vcf_loaders:
        assert vcf_loader.fixed_pedigree

    indexes = []
    for sv, fvs in variants_loader.full_variants_iterator():
        indexes.append(sv.summary_index)
        for fv in fvs:
            print(fv)

    assert indexes == list(range(len(indexes)))

    for vcf_loader in variants_loader.vcf_loaders:
        print(vcf_loader.families.persons)

    families1 = variants_loader.vcf_loaders[0].families
    families2 = variants_loader.vcf_loaders[1].families

    for person1, person2 in zip(
            families1.persons.values(), families2.persons.values()):
        assert person1 == person2

    for fid in families1.keys():

        fam1 = families1[fid]
        fam2 = families2[fid]
        assert fam1 == fam2


def test_wild_vcf_loader_pedigree_union(
    multivcf_pedigree: List[str],
    multivcf_ped: str,
    gpf_instance: GPFInstance
) -> None:

    # f1: f1.mom f1.dad f1.p1 f1.s1
    # f2: f2.mom f2.dad f2.p1 f2.s1
    # f3: f3.mom f3.dad f3.p1 f3.s1
    # f4: f4.mom f4.dad f4.p1 f4.s1
    # f5: f5.mom f5.dad f5.p1 f5.s1

    vcf_file1 = multivcf_pedigree[0]
    vcf_file2 = multivcf_pedigree[1]
    ped_file = multivcf_ped

    families_loader = FamiliesLoader(ped_file)
    families = families_loader.load()

    variants_loader = VcfLoader(
        families,
        [vcf_file1, vcf_file2],
        gpf_instance.reference_genome,
        params={
            "vcf_chromosomes": "1;2",
            "vcf_pedigree_mode": "union",
            "vcf_include_unknown_person_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
        },
    )

    assert variants_loader is not None

    assert len(variants_loader.vcf_loaders) == 2

    for vcf_loader in variants_loader.vcf_loaders:
        print(vcf_loader.families.persons)

    families = variants_loader.families
    families1 = variants_loader.vcf_loaders[0].families
    families2 = variants_loader.vcf_loaders[1].families

    for person1, person2 in zip(
            families1.persons.values(), families2.persons.values()):
        assert person1 == person2

    for fid in families1.keys():

        fam1 = families1[fid]
        fam2 = families2[fid]
        assert fam1 == fam2

    assert len(families.persons) == 20
    assert len(families1.persons) == 20
    assert len(families2.persons) == 20

    for person in families.persons.values():
        assert not person.missing, person

# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pytest

from dae.genomic_resources.testing import setup_directories, setup_vcf, \
    build_filesystem_test_resource
from dae.genomic_resources.genomic_scores import AlleleScore


@pytest.fixture
def vcf_info_clinvar(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("vcf_info_clinvar")
    setup_directories(
        root_path, {
            "genomic_resource.yaml": textwrap.dedent("""
                type: allele_score
                table:
                    filename: clinvar.vcf.gz
                    index_filename: clinvar.vcf.gz.tbi
                    desc: |
                        Example testing ClinVar.
        """)
        })
    setup_vcf(
        root_path / "clinvar.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.1
##fileDate=2022-10-15
##source=ClinVar
##ID=<Description="ClinVar Variation ID">
##INFO=<ID=AF_ESP,Number=1,Type=Float,Description="allele frequencies from GO-ESP">
##INFO=<ID=AF_EXAC,Number=1,Type=Float,Description="allele frequencies from ExAC">
##INFO=<ID=AF_TGP,Number=1,Type=Float,Description="allele frequencies from TGP">
##INFO=<ID=ALLELEID,Number=1,Type=Integer,Description="the ClinVar Allele ID">
##INFO=<ID=CLNDN,Number=.,Type=String,Description="ClinVar's preferred disease name for the concept specified by disease identifiers in CLNDISDB">
##INFO=<ID=CLNDNINCL,Number=.,Type=String,Description="For included Variant : ClinVar's preferred disease name for the concept specified by disease identifiers in CLNDISDB">
##INFO=<ID=CLNDISDB,Number=.,Type=String,Description="Tag-value pairs of disease database name and identifier, e.g. OMIM:NNNNNN">
##INFO=<ID=CLNDISDBINCL,Number=.,Type=String,Description="For included Variant: Tag-value pairs of disease database name and identifier, e.g. OMIM:NNNNNN">
##INFO=<ID=CLNHGVS,Number=.,Type=String,Description="Top-level (primary assembly, alt, or patch) HGVS expression.">
##INFO=<ID=CLNREVSTAT,Number=.,Type=String,Description="ClinVar review status for the Variation ID">
##INFO=<ID=CLNSIG,Number=.,Type=String,Description="Clinical significance for this single variant; multiple values are separated by a vertical bar">
##INFO=<ID=CLNSIGCONF,Number=.,Type=String,Description="Conflicting clinical significance for this single variant; multiple values are separated by a vertical bar">
##INFO=<ID=CLNSIGINCL,Number=.,Type=String,Description="Clinical significance for a haplotype or genotype that includes this variant. Reported as pairs of VariationID:clinical significance; multiple values are separated by a vertical bar">
##INFO=<ID=CLNVC,Number=1,Type=String,Description="Variant type">
##INFO=<ID=CLNVCSO,Number=1,Type=String,Description="Sequence Ontology id for variant type">
##INFO=<ID=CLNVI,Number=.,Type=String,Description="the variant's clinical sources reported as tag-value pairs of database and variant identifier">
##INFO=<ID=DBVARID,Number=.,Type=String,Description="nsv accessions from dbVar for the variant">
##INFO=<ID=GENEINFO,Number=1,Type=String,Description="Gene(s) for the variant reported as gene symbol:gene id. The gene symbol and id are delimited by a colon (:) and each pair is delimited by a vertical bar (|)">
##INFO=<ID=MC,Number=.,Type=String,Description="comma separated list of molecular consequence in the form of Sequence Ontology ID|molecular_consequence">
##INFO=<ID=ORIGIN,Number=.,Type=String,Description="Allele origin. One or more of the following values may be added: 0 - unknown; 1 - germline; 2 - somatic; 4 - inherited; 8 - paternal; 16 - maternal; 32 - de-novo; 64 - biparental; 128 - uniparental; 256 - not-tested; 512 - tested-inconclusive; 1073741824 - other">
##INFO=<ID=RS,Number=.,Type=String,Description="dbSNP ID (i.e. rs number)">
##INFO=<ID=SSR,Number=1,Type=Integer,Description="Variant Suspect Reason Codes. One or more of the following values may be added: 0 - unspecified, 1 - Paralog, 2 - byEST, 4 - oldAlign, 8 - Para_EST, 16 - 1kg_failed, 1024 - other">
#CHROM POS ID REF ALT QUAL FILTER  INFO
chrA   1   .  A   T   .    .       ALLELEID=1003021;CLNDISDB=MedGen:CN517202;CLNDN=not_provided;CLNHGVS=NC_000001.11:g.925952G>A;CLNREVSTAT=criteria_provided,_single_submitter;CLNSIG=Uncertain_significance;CLNVC=single_nucleotide_variant;CLNVCSO=SO:0001483;GENEINFO=SAMD11:148398;MC=SO:0001583|missense_variant;ORIGIN=1;RS=1640863258
chrA   2   .  A   T   .    .       ALLELEID=1632777;CLNDISDB=MedGen:CN517202;CLNDN=Combined_immunodeficiency_due_to_OX40_deficiency;CLNHGVS=NC_000001.11:g.925956C>T;CLNREVSTAT=criteria_provided,_single_submitter;CLNSIG=Likely_benign;CLNVC=single_nucleotide_variant;CLNVCSO=SO:0001483;GENEINFO=SAMD11:148398;MC=SO:0001819|synonymous_variant;ORIGIN=1
chrA   3   .  A   T   .    .       ALLELEID=1600580;CLNDISDB=MedGen:CN517202;CLNDN=not_provided;CLNHGVS=NC_000001.11:g.925969C>T;CLNREVSTAT=criteria_provided,_single_submitter;CLNSIG=Likely_benign;CLNVC=single_nucleotide_variant;CLNVCSO=SO:0001483;GENEINFO=SAMD11:148398;MC=SO:0001583|missense_variant;ORIGIN=1         
        """)  # noqa
    )
    res = build_filesystem_test_resource(root_path)
    return AlleleScore(res)


def test_clinvar_vcf_resource(vcf_info_clinvar):
    vcf_info_clinvar.open()
    scores = vcf_info_clinvar.score_definitions
    assert "CLNDN" in scores
    assert scores["CLNDN"].score_index == "CLNDN"
    assert scores["CLNDN"].desc == ("ClinVar's preferred disease name for the"
                                    " concept specified by disease identifiers"
                                    " in CLNDISDB")


def test_clinvar_get_all_chromosomes(vcf_info_clinvar):
    vcf_info_clinvar.open()
    assert vcf_info_clinvar.get_all_chromosomes() == ["chrA"]


def test_clinvar_score_columns(vcf_info_clinvar):
    vcf_info_clinvar.open()
    assert len(vcf_info_clinvar.get_all_scores()) == 22
    for score_def in vcf_info_clinvar.score_definitions.values():
        assert score_def.desc


@pytest.mark.parametrize("chrom,begin,end,scores,expected", [
    (
        "chrA", 1, 1, ["DBVARID"],
        [{"DBVARID": None}]
    ),
    (
        "chrA", 2, 3, ["DBVARID"],
        [{"DBVARID": None}, {"DBVARID": None}]
    ),

])
def test_clinvar_fetch_region(
    vcf_info_clinvar, chrom, begin, end, scores, expected
):
    vcf_info_clinvar.open()
    result = vcf_info_clinvar.fetch_region(chrom, begin, end, scores)
    assert list(result) == expected


@pytest.mark.parametrize("chrom,pos,ref,alt,scores,expected", [
    (
        "chrA", 1, "A", "T", ["CLNDN", "ALLELEID"],
        ["not_provided", 1003021]
    ),
    (
        "chrA", 1, "A", "G", ["CLNDN", "ALLELEID"],
        None
    ),
    (
        "chrA", 2, "A", "T", ["CLNDN", "CLNSIG"],
        ["Combined_immunodeficiency_due_to_OX40_deficiency",
         "Likely_benign"]
    ),
    (
        "chrA", 3, "A", "T", ["DBVARID"],
        [None]
    )
])
def test_clinvar_fetch_scores(
        vcf_info_clinvar, chrom, pos, ref, alt, scores, expected):
    result = vcf_info_clinvar\
        .open()\
        .fetch_scores(chrom, pos, ref, alt, scores)
    assert result == expected


@pytest.fixture
def vcf_info_gnomad(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("vcf_info_gnomad")
    setup_directories(
        root_path, {
            "genomic_resource.yaml": textwrap.dedent("""
                type: allele_score
                table:
                    filename: gnomad.vcf.gz
                    index_filename: gnomad.vcf.gz.tbi
                    desc: |
                        Example testing GnomAD.
            """)
        })
    setup_vcf(
        root_path / "gnomad.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.2
##hailversion=0.2.24-9cd88d97bedd
##FILTER=<ID=AC0,Description="Allele count is zero after filtering out low-confidence genotypes (GQ < 20; DP < 10; and AB < 0.2 for het calls)">
##FILTER=<ID=AS_VQSR,Description="Failed Allele-Specific Variant Quality Score Recalibration threshold">
##FILTER=<ID=InbreedingCoeff,Description="InbreedingCoeff < -0.3">
##FILTER=<ID=PASS,Description="Passed all variant filters">
##INFO=<ID=AC,Number=A,Type=Integer,Description="Alternate allele count for samples">
##INFO=<ID=AN,Number=1,Type=Integer,Description="Total number of alleles in samples">
##INFO=<ID=AF,Number=A,Type=Float,Description="Alternate allele frequency in samples">
##INFO=<ID=non_par,Number=0,Type=Flag,Description="">
##INFO=<ID=lcr,Number=0,Type=Flag,Description="Variant falls within a low complexity region">
##INFO=<ID=variant_type,Number=1,Type=String,Description="Variant type (snv, indel, multi-snv, multi-indel, or mixed)">
##INFO=<ID=n_alt_alleles,Number=A,Type=Integer,Description="Total number of alternate alleles observed at variant locus">
##INFO=<ID=ReadPosRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of alternate vs. reference read position bias">
##INFO=<ID=MQRankSum,Number=1,Type=Float,Description="Z-score from Wilcoxon rank sum test of alternate vs. reference read mapping qualities">
##INFO=<ID=RAW_MQ,Number=1,Type=Float,Description="">
##INFO=<ID=DP,Number=1,Type=Integer,Description="Depth of informative coverage for each sample; reads with MQ=255 or with bad mates are filtered">
##INFO=<ID=MQ_DP,Number=1,Type=Integer,Description="">
##INFO=<ID=VarDP,Number=1,Type=Integer,Description="">
##INFO=<ID=MQ,Number=1,Type=Float,Description="Root mean square of the mapping quality of reads across all samples">
##INFO=<ID=QD,Number=1,Type=Float,Description="Variant call confidence normalized by depth of sample reads supporting a variant">
##INFO=<ID=FS,Number=1,Type=Float,Description="Phred-scaled p-value of Fisher's exact test for strand bias">
##INFO=<ID=SB,Number=4,Type=Integer,Description="">
##INFO=<ID=InbreedingCoeff,Number=1,Type=Float,Description="Inbreeding coefficient as estimated from the genotype likelihoods per-sample when compared against the Hardy-Weinberg expectation">
##INFO=<ID=AS_VQSLOD,Number=1,Type=Float,Description="Log-odds ratio of being a true variant versus being a false positive under the trained allele-specific VQSR Gaussian mixture model">
##INFO=<ID=NEGATIVE_TRAIN_SITE,Number=0,Type=Flag,Description="Variant was used to build the negative training set of low-quality variants for VQSR">
##INFO=<ID=POSITIVE_TRAIN_SITE,Number=0,Type=Flag,Description="Variant was used to build the positive training set of high-quality variants for VQSR">
##INFO=<ID=culprit,Number=1,Type=String,Description="Worst-performing annotation in the VQSR Gaussian mixture model">
##INFO=<ID=SOR,Number=1,Type=Float,Description="Strand bias estimated by the symmetric odds ratio test">
##INFO=<ID=AC_asj_female,Number=A,Type=Integer,Description="Alternate allele count for female samples of Ashkenazi Jewish ancestry">
##INFO=<ID=AN_asj_female,Number=1,Type=Integer,Description="Total number of alleles in female samples of Ashkenazi Jewish ancestry">
##INFO=<ID=AF_asj_female,Number=A,Type=Float,Description="Alternate allele frequency in female samples of Ashkenazi Jewish ancestry">
##INFO=<ID=nhomalt_asj_female,Number=A,Type=Integer,Description="Count of homozygous individuals in female samples of Ashkenazi Jewish ancestry">
##INFO=<ID=AC_eas_female,Number=A,Type=Integer,Description="Alternate allele count for female samples of East Asian ancestry">
##INFO=<ID=AN_eas_female,Number=1,Type=Integer,Description="Total number of alleles in female samples of East Asian ancestry">
##INFO=<ID=AF_eas_female,Number=A,Type=Float,Description="Alternate allele frequency in female samples of East Asian ancestry">
##INFO=<ID=nhomalt_eas_female,Number=A,Type=Integer,Description="Count of homozygous individuals in female samples of East Asian ancestry">
##INFO=<ID=AC_afr_male,Number=A,Type=Integer,Description="Alternate allele count for male samples of African-American/African ancestry">
##INFO=<ID=AN_afr_male,Number=1,Type=Integer,Description="Total number of alleles in male samples of African-American/African ancestry">
##INFO=<ID=AF_afr_male,Number=A,Type=Float,Description="Alternate allele frequency in male samples of African-American/African ancestry">
##INFO=<ID=nhomalt_afr_male,Number=A,Type=Integer,Description="Count of homozygous individuals in male samples of African-American/African ancestry">
##INFO=<ID=AC_female,Number=A,Type=Integer,Description="Alternate allele count for female samples">
##INFO=<ID=AN_female,Number=1,Type=Integer,Description="Total number of alleles in female samples">
##INFO=<ID=AF_female,Number=A,Type=Float,Description="Alternate allele frequency in female samples">
##INFO=<ID=nhomalt_female,Number=A,Type=Integer,Description="Count of homozygous individuals in female samples">
##INFO=<ID=AC_fin_male,Number=A,Type=Integer,Description="Alternate allele count for male samples of Finnish ancestry">
##INFO=<ID=AN_fin_male,Number=1,Type=Integer,Description="Total number of alleles in male samples of Finnish ancestry">
##INFO=<ID=AF_fin_male,Number=A,Type=Float,Description="Alternate allele frequency in male samples of Finnish ancestry">
##INFO=<ID=nhomalt_fin_male,Number=A,Type=Integer,Description="Count of homozygous individuals in male samples of Finnish ancestry">
##INFO=<ID=AC_oth_female,Number=A,Type=Integer,Description="Alternate allele count for female samples of Other ancestry">
##INFO=<ID=AN_oth_female,Number=1,Type=Integer,Description="Total number of alleles in female samples of Other ancestry">
##INFO=<ID=AF_oth_female,Number=A,Type=Float,Description="Alternate allele frequency in female samples of Other ancestry">
##INFO=<ID=nhomalt_oth_female,Number=A,Type=Integer,Description="Count of homozygous individuals in female samples of Other ancestry">
##INFO=<ID=AC_ami,Number=A,Type=Integer,Description="Alternate allele count for samples of Amish ancestry">
##INFO=<ID=AN_ami,Number=1,Type=Integer,Description="Total number of alleles in samples of Amish ancestry">
##INFO=<ID=AF_ami,Number=A,Type=Float,Description="Alternate allele frequency in samples of Amish ancestry">
##INFO=<ID=nhomalt_ami,Number=A,Type=Integer,Description="Count of homozygous individuals in samples of Amish ancestry">
##INFO=<ID=AC_oth,Number=A,Type=Integer,Description="Alternate allele count for samples of Other ancestry">
##INFO=<ID=AN_oth,Number=1,Type=Integer,Description="Total number of alleles in samples of Other ancestry">
##INFO=<ID=AF_oth,Number=A,Type=Float,Description="Alternate allele frequency in samples of Other ancestry">
##INFO=<ID=nhomalt_oth,Number=A,Type=Integer,Description="Count of homozygous individuals in samples of Other ancestry">
##INFO=<ID=AC_male,Number=A,Type=Integer,Description="Alternate allele count for male samples">
##INFO=<ID=AN_male,Number=1,Type=Integer,Description="Total number of alleles in male samples">
##INFO=<ID=AF_male,Number=A,Type=Float,Description="Alternate allele frequency in male samples">
##INFO=<ID=nhomalt_male,Number=A,Type=Integer,Description="Count of homozygous individuals in male samples">
##INFO=<ID=AC_ami_female,Number=A,Type=Integer,Description="Alternate allele count for female samples of Amish ancestry">
##INFO=<ID=AN_ami_female,Number=1,Type=Integer,Description="Total number of alleles in female samples of Amish ancestry">
##INFO=<ID=AF_ami_female,Number=A,Type=Float,Description="Alternate allele frequency in female samples of Amish ancestry">
##INFO=<ID=nhomalt_ami_female,Number=A,Type=Integer,Description="Count of homozygous individuals in female samples of Amish ancestry">
##INFO=<ID=AC_afr,Number=A,Type=Integer,Description="Alternate allele count for samples of African-American/African ancestry">
##INFO=<ID=AN_afr,Number=1,Type=Integer,Description="Total number of alleles in samples of African-American/African ancestry">
##INFO=<ID=AF_afr,Number=A,Type=Float,Description="Alternate allele frequency in samples of African-American/African ancestry">
##INFO=<ID=nhomalt_afr,Number=A,Type=Integer,Description="Count of homozygous individuals in samples of African-American/African ancestry">
##INFO=<ID=AC_eas_male,Number=A,Type=Integer,Description="Alternate allele count for male samples of East Asian ancestry">
##INFO=<ID=AN_eas_male,Number=1,Type=Integer,Description="Total number of alleles in male samples of East Asian ancestry">
##INFO=<ID=AF_eas_male,Number=A,Type=Float,Description="Alternate allele frequency in male samples of East Asian ancestry">
##INFO=<ID=nhomalt_eas_male,Number=A,Type=Integer,Description="Count of homozygous individuals in male samples of East Asian ancestry">
##INFO=<ID=AC_sas,Number=A,Type=Integer,Description="Alternate allele count for samples of South Asian ancestry">
##INFO=<ID=AN_sas,Number=1,Type=Integer,Description="Total number of alleles in samples of South Asian ancestry">
##INFO=<ID=AF_sas,Number=A,Type=Float,Description="Alternate allele frequency in samples of South Asian ancestry">
##INFO=<ID=nhomalt_sas,Number=A,Type=Integer,Description="Count of homozygous individuals in samples of South Asian ancestry">
##INFO=<ID=AC_nfe_female,Number=A,Type=Integer,Description="Alternate allele count for female samples of Non-Finnish European ancestry">
##INFO=<ID=AN_nfe_female,Number=1,Type=Integer,Description="Total number of alleles in female samples of Non-Finnish European ancestry">
##INFO=<ID=AF_nfe_female,Number=A,Type=Float,Description="Alternate allele frequency in female samples of Non-Finnish European ancestry">
##INFO=<ID=nhomalt_nfe_female,Number=A,Type=Integer,Description="Count of homozygous individuals in female samples of Non-Finnish European ancestry">
##INFO=<ID=AC_asj_male,Number=A,Type=Integer,Description="Alternate allele count for male samples of Ashkenazi Jewish ancestry">
##INFO=<ID=AN_asj_male,Number=1,Type=Integer,Description="Total number of alleles in male samples of Ashkenazi Jewish ancestry">
##INFO=<ID=AF_asj_male,Number=A,Type=Float,Description="Alternate allele frequency in male samples of Ashkenazi Jewish ancestry">
##INFO=<ID=nhomalt_asj_male,Number=A,Type=Integer,Description="Count of homozygous individuals in male samples of Ashkenazi Jewish ancestry">
##INFO=<ID=AC_raw,Number=A,Type=Integer,Description="Alternate allele count for samples, before removing low-confidence genotypes">
##INFO=<ID=AN_raw,Number=1,Type=Integer,Description="Total number of alleles in samples, before removing low-confidence genotypes">
##INFO=<ID=AF_raw,Number=A,Type=Float,Description="Alternate allele frequency in samples, before removing low-confidence genotypes">
##INFO=<ID=nhomalt_raw,Number=A,Type=Integer,Description="Count of homozygous individuals in samples, before removing low-confidence genotypes">
##INFO=<ID=AC_oth_male,Number=A,Type=Integer,Description="Alternate allele count for male samples of Other ancestry">
##INFO=<ID=AN_oth_male,Number=1,Type=Integer,Description="Total number of alleles in male samples of Other ancestry">
##INFO=<ID=AF_oth_male,Number=A,Type=Float,Description="Alternate allele frequency in male samples of Other ancestry">
##INFO=<ID=nhomalt_oth_male,Number=A,Type=Integer,Description="Count of homozygous individuals in male samples of Other ancestry">
##INFO=<ID=AC_nfe_male,Number=A,Type=Integer,Description="Alternate allele count for male samples of Non-Finnish European ancestry">
##INFO=<ID=AN_nfe_male,Number=1,Type=Integer,Description="Total number of alleles in male samples of Non-Finnish European ancestry">
##INFO=<ID=AF_nfe_male,Number=A,Type=Float,Description="Alternate allele frequency in male samples of Non-Finnish European ancestry">
##INFO=<ID=nhomalt_nfe_male,Number=A,Type=Integer,Description="Count of homozygous individuals in male samples of Non-Finnish European ancestry">
##INFO=<ID=AC_asj,Number=A,Type=Integer,Description="Alternate allele count for samples of Ashkenazi Jewish ancestry">
##INFO=<ID=AN_asj,Number=1,Type=Integer,Description="Total number of alleles in samples of Ashkenazi Jewish ancestry">
##INFO=<ID=AF_asj,Number=A,Type=Float,Description="Alternate allele frequency in samples of Ashkenazi Jewish ancestry">
##INFO=<ID=nhomalt_asj,Number=A,Type=Integer,Description="Count of homozygous individuals in samples of Ashkenazi Jewish ancestry">
##INFO=<ID=AC_amr_male,Number=A,Type=Integer,Description="Alternate allele count for male samples of Latino ancestry">
##INFO=<ID=AN_amr_male,Number=1,Type=Integer,Description="Total number of alleles in male samples of Latino ancestry">
##INFO=<ID=AF_amr_male,Number=A,Type=Float,Description="Alternate allele frequency in male samples of Latino ancestry">
##INFO=<ID=nhomalt_amr_male,Number=A,Type=Integer,Description="Count of homozygous individuals in male samples of Latino ancestry">
##INFO=<ID=nhomalt,Number=A,Type=Integer,Description="Count of homozygous individuals in samples">
##INFO=<ID=AC_amr_female,Number=A,Type=Integer,Description="Alternate allele count for female samples of Latino ancestry">
##INFO=<ID=AN_amr_female,Number=1,Type=Integer,Description="Total number of alleles in female samples of Latino ancestry">
##INFO=<ID=AF_amr_female,Number=A,Type=Float,Description="Alternate allele frequency in female samples of Latino ancestry">
##INFO=<ID=nhomalt_amr_female,Number=A,Type=Integer,Description="Count of homozygous individuals in female samples of Latino ancestry">
##INFO=<ID=AC_sas_female,Number=A,Type=Integer,Description="Alternate allele count for female samples of South Asian ancestry">
##INFO=<ID=AN_sas_female,Number=1,Type=Integer,Description="Total number of alleles in female samples of South Asian ancestry">
##INFO=<ID=AF_sas_female,Number=A,Type=Float,Description="Alternate allele frequency in female samples of South Asian ancestry">
##INFO=<ID=nhomalt_sas_female,Number=A,Type=Integer,Description="Count of homozygous individuals in female samples of South Asian ancestry">
##INFO=<ID=AC_fin,Number=A,Type=Integer,Description="Alternate allele count for samples of Finnish ancestry">
##INFO=<ID=AN_fin,Number=1,Type=Integer,Description="Total number of alleles in samples of Finnish ancestry">
##INFO=<ID=AF_fin,Number=A,Type=Float,Description="Alternate allele frequency in samples of Finnish ancestry">
##INFO=<ID=nhomalt_fin,Number=A,Type=Integer,Description="Count of homozygous individuals in samples of Finnish ancestry">
##INFO=<ID=AC_afr_female,Number=A,Type=Integer,Description="Alternate allele count for female samples of African-American/African ancestry">
##INFO=<ID=AN_afr_female,Number=1,Type=Integer,Description="Total number of alleles in female samples of African-American/African ancestry">
##INFO=<ID=AF_afr_female,Number=A,Type=Float,Description="Alternate allele frequency in female samples of African-American/African ancestry">
##INFO=<ID=nhomalt_afr_female,Number=A,Type=Integer,Description="Count of homozygous individuals in female samples of African-American/African ancestry">
##INFO=<ID=AC_sas_male,Number=A,Type=Integer,Description="Alternate allele count for male samples of South Asian ancestry">
##INFO=<ID=AN_sas_male,Number=1,Type=Integer,Description="Total number of alleles in male samples of South Asian ancestry">
##INFO=<ID=AF_sas_male,Number=A,Type=Float,Description="Alternate allele frequency in male samples of South Asian ancestry">
##INFO=<ID=nhomalt_sas_male,Number=A,Type=Integer,Description="Count of homozygous individuals in male samples of South Asian ancestry">
##INFO=<ID=AC_amr,Number=A,Type=Integer,Description="Alternate allele count for samples of Latino ancestry">
##INFO=<ID=AN_amr,Number=1,Type=Integer,Description="Total number of alleles in samples of Latino ancestry">
##INFO=<ID=AF_amr,Number=A,Type=Float,Description="Alternate allele frequency in samples of Latino ancestry">
##INFO=<ID=nhomalt_amr,Number=A,Type=Integer,Description="Count of homozygous individuals in samples of Latino ancestry">
##INFO=<ID=AC_nfe,Number=A,Type=Integer,Description="Alternate allele count for samples of Non-Finnish European ancestry">
##INFO=<ID=AN_nfe,Number=1,Type=Integer,Description="Total number of alleles in samples of Non-Finnish European ancestry">
##INFO=<ID=AF_nfe,Number=A,Type=Float,Description="Alternate allele frequency in samples of Non-Finnish European ancestry">
##INFO=<ID=nhomalt_nfe,Number=A,Type=Integer,Description="Count of homozygous individuals in samples of Non-Finnish European ancestry">
##INFO=<ID=AC_eas,Number=A,Type=Integer,Description="Alternate allele count for samples of East Asian ancestry">
##INFO=<ID=AN_eas,Number=1,Type=Integer,Description="Total number of alleles in samples of East Asian ancestry">
##INFO=<ID=AF_eas,Number=A,Type=Float,Description="Alternate allele frequency in samples of East Asian ancestry">
##INFO=<ID=nhomalt_eas,Number=A,Type=Integer,Description="Count of homozygous individuals in samples of East Asian ancestry">
##INFO=<ID=AC_ami_male,Number=A,Type=Integer,Description="Alternate allele count for male samples of Amish ancestry">
##INFO=<ID=AN_ami_male,Number=1,Type=Integer,Description="Total number of alleles in male samples of Amish ancestry">
##INFO=<ID=AF_ami_male,Number=A,Type=Float,Description="Alternate allele frequency in male samples of Amish ancestry">
##INFO=<ID=nhomalt_ami_male,Number=A,Type=Integer,Description="Count of homozygous individuals in male samples of Amish ancestry">
##INFO=<ID=AC_fin_female,Number=A,Type=Integer,Description="Alternate allele count for female samples of Finnish ancestry">
##INFO=<ID=AN_fin_female,Number=1,Type=Integer,Description="Total number of alleles in female samples of Finnish ancestry">
##INFO=<ID=AF_fin_female,Number=A,Type=Float,Description="Alternate allele frequency in female samples of Finnish ancestry">
##INFO=<ID=nhomalt_fin_female,Number=A,Type=Integer,Description="Count of homozygous individuals in female samples of Finnish ancestry">
##INFO=<ID=faf95_afr,Number=A,Type=Float,Description="Filtering allele frequency (using Poisson 95% CI) for samples of African-American/African ancestry">
##INFO=<ID=faf99_afr,Number=A,Type=Float,Description="Filtering allele frequency (using Poisson 99% CI) for samples of African-American/African ancestry">
##INFO=<ID=faf95_sas,Number=A,Type=Float,Description="Filtering allele frequency (using Poisson 95% CI) for samples of South Asian ancestry">
##INFO=<ID=faf99_sas,Number=A,Type=Float,Description="Filtering allele frequency (using Poisson 99% CI) for samples of South Asian ancestry">
##INFO=<ID=faf95_adj,Number=1,Type=Float,Description="">
##INFO=<ID=faf99_adj,Number=1,Type=Float,Description="">
##INFO=<ID=faf95_amr,Number=A,Type=Float,Description="Filtering allele frequency (using Poisson 95% CI) for samples of Latino ancestry">
##INFO=<ID=faf99_amr,Number=A,Type=Float,Description="Filtering allele frequency (using Poisson 99% CI) for samples of Latino ancestry">
##INFO=<ID=faf95_nfe,Number=A,Type=Float,Description="Filtering allele frequency (using Poisson 95% CI) for samples of Non-Finnish European ancestry">
##INFO=<ID=faf99_nfe,Number=A,Type=Float,Description="Filtering allele frequency (using Poisson 99% CI) for samples of Non-Finnish European ancestry">
##INFO=<ID=faf95_eas,Number=A,Type=Float,Description="Filtering allele frequency (using Poisson 95% CI) for samples of East Asian ancestry">
##INFO=<ID=faf99_eas,Number=A,Type=Float,Description="Filtering allele frequency (using Poisson 99% CI) for samples of East Asian ancestry">
##INFO=<ID=vep,Number=.,Type=String,Description="Allele|Consequence|IMPACT|SYMBOL|Gene|Feature_type|Feature|BIOTYPE|EXON|INTRON|">
#CHROM POS ID REF ALT QUAL   FILTER      INFO
chrA   1   .  A   C   77.00  AC0;AS_VQSR AC=0;AN=53780;AF=0.00000e+00;lcr;variant_type=snv;n_alt_alleles=1;ReadPosRankSum=-1.38000e+00;MQRankSum=-5.72000e-01;RAW_MQ=6.39630e+04;DP=26;MQ_DP=52;VarDP=26;MQ=3.50722e+01;QD=2.96154e+00;FS=5.09715e+00;SB=21,6,3,3;InbreedingCoeff=-1.72592e-05;AS_VQSLOD=-9.41040e+00;NEGATIVE_TRAIN_SITE;culprit=AS_MQ;SOR=9.60000e-02;AC_asj_female=0;AN_asj_female=776;AF_asj_female=0.00000e+00;nhomalt_asj_female=0;AC_eas_female=0;AN_eas_female=558;AF_eas_female=0.00000e+00;nhomalt_eas_female=0;AC_afr_male=0;AN_afr_male=6700;AF_afr_male=0.00000e+00;nhomalt_afr_male=0;AC_female=0;AN_female=27974;AF_female=0.00000e+00;nhomalt_female=0;AC_fin_male=0;AN_fin_male=3278;AF_fin_male=0.00000e+00;nhomalt_fin_male=0;AC_oth_female=0;AN_oth_female=430;AF_oth_female=0.00000e+00;nhomalt_oth_female=0;AC_ami=0;AN_ami=350;AF_ami=0.00000e+00;nhomalt_ami=0;AC_oth=0;AN_oth=802;AF_oth=0.00000e+00;nhomalt_oth=0;AC_male=0;AN_male=25806;AF_male=0.00000e+00;nhomalt_male=0;AC_ami_female=0;AN_ami_female=150;AF_ami_female=0.00000e+00;nhomalt_ami_female=0;AC_afr=0;AN_afr=14854;AF_afr=0.00000e+00;nhomalt_afr=0;AC_eas_male=0;AN_eas_male=612;AF_eas_male=0.00000e+00;nhomalt_eas_male=0;AC_sas=0;AN_sas=606;AF_sas=0.00000e+00;nhomalt_sas=0;AC_nfe_female=0;AN_nfe_female=14256;AF_nfe_female=0.00000e+00;nhomalt_nfe_female=0;AC_asj_male=0;AN_asj_male=720;AF_asj_male=0.00000e+00;nhomalt_asj_male=0;AC_raw=2;AN_raw=115882;AF_raw=1.72589e-05;nhomalt_raw=0;AC_oth_male=0;AN_oth_male=372;AF_oth_male=0.00000e+00;nhomalt_oth_male=0;AC_nfe_male=0;AN_nfe_male=10036;AF_nfe_male=0.00000e+00;nhomalt_nfe_male=0;AC_asj=0;AN_asj=1496;AF_asj=0.00000e+00;nhomalt_asj=0;AC_amr_male=0;AN_amr_male=3392;AF_amr_male=0.00000e+00;nhomalt_amr_male=0;nhomalt=0;AC_amr_female=0;AN_amr_female=2454;AF_amr_female=0.00000e+00;nhomalt_amr_female=0;AC_sas_female=0;AN_sas_female=110;AF_sas_female=0.00000e+00;nhomalt_sas_female=0;AC_fin=0;AN_fin=4364;AF_fin=0.00000e+00;nhomalt_fin=0;AC_afr_female=0;AN_afr_female=8154;AF_afr_female=0.00000e+00;nhomalt_afr_female=0;AC_sas_male=0;AN_sas_male=496;AF_sas_male=0.00000e+00;nhomalt_sas_male=0;AC_amr=0;AN_amr=5846;AF_amr=0.00000e+00;nhomalt_amr=0;AC_nfe=0;AN_nfe=24292;AF_nfe=0.00000e+00;nhomalt_nfe=0;AC_eas=0;AN_eas=1170;AF_eas=0.00000e+00;nhomalt_eas=0;AC_ami_male=0;AN_ami_male=200;AF_ami_male=0.00000e+00;nhomalt_ami_male=0;AC_fin_female=0;AN_fin_female=1086;AF_fin_female=0.00000e+00;nhomalt_fin_female=0;faf95_afr=0.00000e+00;faf99_afr=0.00000e+00;faf95_sas=0.00000e+00;faf99_sas=0.00000e+00;faf95_adj=0.00000e+00;faf99_adj=0.00000e+00;faf95_amr=0.00000e+00;faf99_amr=0.00000e+00;faf95_nfe=0.00000e+00;faf99_nfe=0.00000e+00;faf95_eas=0.00000e+00;faf99_eas=0.00000e+00;vep=C|upstream_gene_variant|MODIFIER|DDX11L1|ENSG00000223972|Transcript|ENST00000450305|transcribed_unprocessed_pseudogene|||,C|upstream_gene_variant|MODIFIER|DDX11L1|ENSG00000223972|Transcript|ENST00000456328|processed_transcript|||,C|downstream_gene_variant|MODIFIER|WASH7P|ENSG00000227232|Transcript|ENST00000488147|unprocessed_pseudogene|||
chrA   2   .  A   C   180.00 AS_VQSR     AC=2;AN=72762;AF=2.74869e-05;lcr;variant_type=snv;n_alt_alleles=1;ReadPosRankSum=-4.80000e-01;MQRankSum=1.37100e+00;RAW_MQ=2.02552e+05;DP=82;MQ_DP=138;VarDP=82;MQ=3.83115e+01;QD=2.19512e+00;FS=8.58284e+00;SB=49,12,13,8;InbreedingCoeff=-3.30912e-05;AS_VQSLOD=-7.92200e+00;NEGATIVE_TRAIN_SITE;culprit=AS_MQ;SOR=1.51000e-01;AC_asj_female=0;AN_asj_female=1048;AF_asj_female=0.00000e+00;nhomalt_asj_female=0;AC_eas_female=1;AN_eas_female=806;AF_eas_female=1.24069e-03;nhomalt_eas_female=0;AC_afr_male=0;AN_afr_male=9296;AF_afr_male=0.00000e+00;nhomalt_afr_male=0;AC_female=1;AN_female=38278;AF_female=2.61247e-05;nhomalt_female=0;AC_fin_male=1;AN_fin_male=4236;AF_fin_male=2.36072e-04;nhomalt_fin_male=0;AC_oth_female=0;AN_oth_female=560;AF_oth_female=0.00000e+00;nhomalt_oth_female=0;AC_ami=0;AN_ami=484;AF_ami=0.00000e+00;nhomalt_ami=0;AC_oth=0;AN_oth=1032;AF_oth=0.00000e+00;nhomalt_oth=0;AC_male=1;AN_male=34484;AF_male=2.89990e-05;nhomalt_male=0;AC_ami_female=0;AN_ami_female=234;AF_ami_female=0.00000e+00;nhomalt_ami_female=0;AC_afr=0;AN_afr=20736;AF_afr=0.00000e+00;nhomalt_afr=0;AC_eas_male=0;AN_eas_male=848;AF_eas_male=0.00000e+00;nhomalt_eas_male=0;AC_sas=0;AN_sas=946;AF_sas=0.00000e+00;nhomalt_sas=0;AC_nfe_female=0;AN_nfe_female=19400;AF_nfe_female=0.00000e+00;nhomalt_nfe_female=0;AC_asj_male=0;AN_asj_male=938;AF_asj_male=0.00000e+00;nhomalt_asj_male=0;AC_raw=4;AN_raw=120882;AF_raw=3.30901e-05;nhomalt_raw=0;AC_oth_male=0;AN_oth_male=472;AF_oth_male=0.00000e+00;nhomalt_oth_male=0;AC_nfe_male=0;AN_nfe_male=13398;AF_nfe_male=0.00000e+00;nhomalt_nfe_male=0;AC_asj=0;AN_asj=1986;AF_asj=0.00000e+00;nhomalt_asj=0;AC_amr_male=0;AN_amr_male=4278;AF_amr_male=0.00000e+00;nhomalt_amr_male=0;nhomalt=0;AC_amr_female=0;AN_amr_female=3270;AF_amr_female=0.00000e+00;nhomalt_amr_female=0;AC_sas_female=0;AN_sas_female=178;AF_sas_female=0.00000e+00;nhomalt_sas_female=0;AC_fin=1;AN_fin=5578;AF_fin=1.79276e-04;nhomalt_fin=0;AC_afr_female=0;AN_afr_female=11440;AF_afr_female=0.00000e+00;nhomalt_afr_female=0;AC_sas_male=0;AN_sas_male=768;AF_sas_male=0.00000e+00;nhomalt_sas_male=0;AC_amr=0;AN_amr=7548;AF_amr=0.00000e+00;nhomalt_amr=0;AC_nfe=0;AN_nfe=32798;AF_nfe=0.00000e+00;nhomalt_nfe=0;AC_eas=1;AN_eas=1654;AF_eas=6.04595e-04;nhomalt_eas=0;AC_ami_male=0;AN_ami_male=250;AF_ami_male=0.00000e+00;nhomalt_ami_male=0;AC_fin_female=0;AN_fin_female=1342;AF_fin_female=0.00000e+00;nhomalt_fin_female=0;faf95_afr=0.00000e+00;faf99_afr=0.00000e+00;faf95_sas=0.00000e+00;faf99_sas=0.00000e+00;faf95_adj=4.56000e-06;faf99_adj=4.71000e-06;faf95_amr=0.00000e+00;faf99_amr=0.00000e+00;faf95_nfe=0.00000e+00;faf99_nfe=0.00000e+00;faf95_eas=0.00000e+00;faf99_eas=0.00000e+00;vep=C|upstream_gene_variant|MODIFIER|DDX11L1|ENSG00000223972|Transcript|ENST00000450305|transcribed_unprocessed_pseudogene|||,C|upstream_gene_variant|MODIFIER|DDX11L1|ENSG00000223972|Transcript|ENST00000456328|processed_transcript|||,C|downstream_gene_variant|MODIFIER|WASH7P|ENSG00000227232|Transcript|ENST00000488147|unprocessed_pseudogene|||
chrA   3   .  A   C   97.00  AS_VQSR     AC=1;AN=81114;AF=1.23283e-05;lcr;variant_type=snv;n_alt_alleles=1;ReadPosRankSum=-8.96000e-01;MQRankSum=1.23100e+00;RAW_MQ=8.17480e+04;DP=35;MQ_DP=66;VarDP=35;MQ=3.51938e+01;QD=2.77143e+00;FS=3.10999e+01;SB=25,0,5,5;InbreedingCoeff=-8.65599e-06;AS_VQSLOD=-2.38139e+01;NEGATIVE_TRAIN_SITE;culprit=AS_FS;SOR=1.00000e-03;AC_asj_female=0;AN_asj_female=1162;AF_asj_female=0.00000e+00;nhomalt_asj_female=0;AC_eas_female=0;AN_eas_female=904;AF_eas_female=0.00000e+00;nhomalt_eas_female=0;AC_afr_male=0;AN_afr_male=10408;AF_afr_male=0.00000e+00;nhomalt_afr_male=0;AC_female=1;AN_female=42834;AF_female=2.33459e-05;nhomalt_female=0;AC_fin_male=0;AN_fin_male=4530;AF_fin_male=0.00000e+00;nhomalt_fin_male=0;AC_oth_female=0;AN_oth_female=644;AF_oth_female=0.00000e+00;nhomalt_oth_female=0;AC_ami=0;AN_ami=566;AF_ami=0.00000e+00;nhomalt_ami=0;AC_oth=0;AN_oth=1206;AF_oth=0.00000e+00;nhomalt_oth=0;AC_male=0;AN_male=38280;AF_male=0.00000e+00;nhomalt_male=0;AC_ami_female=0;AN_ami_female=288;AF_ami_female=0.00000e+00;nhomalt_ami_female=0;AC_afr=1;AN_afr=23210;AF_afr=4.30849e-05;nhomalt_afr=0;AC_eas_male=0;AN_eas_male=1026;AF_eas_male=0.00000e+00;nhomalt_eas_male=0;AC_sas=0;AN_sas=1312;AF_sas=0.00000e+00;nhomalt_sas=0;AC_nfe_female=0;AN_nfe_female=22048;AF_nfe_female=0.00000e+00;nhomalt_nfe_female=0;AC_asj_male=0;AN_asj_male=1028;AF_asj_male=0.00000e+00;nhomalt_asj_male=0;AC_raw=1;AN_raw=115528;AF_raw=8.65591e-06;nhomalt_raw=0;AC_oth_male=0;AN_oth_male=562;AF_oth_male=0.00000e+00;nhomalt_oth_male=0;AC_nfe_male=0;AN_nfe_male=15116;AF_nfe_male=0.00000e+00;nhomalt_nfe_male=0;AC_asj=0;AN_asj=2190;AF_asj=0.00000e+00;nhomalt_asj=0;AC_amr_male=0;AN_amr_male=4260;AF_amr_male=0.00000e+00;nhomalt_amr_male=0;nhomalt=0;AC_amr_female=0;AN_amr_female=3444;AF_amr_female=0.00000e+00;nhomalt_amr_female=0;AC_sas_female=0;AN_sas_female=240;AF_sas_female=0.00000e+00;nhomalt_sas_female=0;AC_fin=0;AN_fin=5832;AF_fin=0.00000e+00;nhomalt_fin=0;AC_afr_female=1;AN_afr_female=12802;AF_afr_female=7.81128e-05;nhomalt_afr_female=0;AC_sas_male=0;AN_sas_male=1072;AF_sas_male=0.00000e+00;nhomalt_sas_male=0;AC_amr=0;AN_amr=7704;AF_amr=0.00000e+00;nhomalt_amr=0;AC_nfe=0;AN_nfe=37164;AF_nfe=0.00000e+00;nhomalt_nfe=0;AC_eas=0;AN_eas=1930;AF_eas=0.00000e+00;nhomalt_eas=0;AC_ami_male=0;AN_ami_male=278;AF_ami_male=0.00000e+00;nhomalt_ami_male=0;AC_fin_female=0;AN_fin_female=1302;AF_fin_female=0.00000e+00;nhomalt_fin_female=0;faf95_afr=0.00000e+00;faf99_afr=0.00000e+00;faf95_sas=0.00000e+00;faf99_sas=0.00000e+00;faf95_adj=0.00000e+00;faf99_adj=0.00000e+00;faf95_amr=0.00000e+00;faf99_amr=0.00000e+00;faf95_nfe=0.00000e+00;faf99_nfe=0.00000e+00;faf95_eas=0.00000e+00;faf99_eas=0.00000e+00;vep=C|upstream_gene_variant|MODIFIER|DDX11L1|ENSG00000223972|Transcript|ENST00000450305|transcribed_unprocessed_pseudogene|||,C|upstream_gene_variant|MODIFIER|DDX11L1|ENSG00000223972|Transcript|ENST00000456328|processed_transcript|||,C|downstream_gene_variant|MODIFIER|WASH7P|ENSG00000227232|Transcript|ENST00000488147|unprocessed_pseudogene|||
chrA   4   .  A   C   75.00  AS_VQSR     AC=1;AN=89638;AF=1.11560e-05;lcr;variant_type=snv;n_alt_alleles=1;ReadPosRankSum=-1.10600e+00;MQRankSum=7.15000e-01;RAW_MQ=1.14150e+05;DP=62;MQ_DP=94;VarDP=62;MQ=3.48477e+01;QD=1.20968e+00;FS=6.89797e+00;SB=47,22,6,7;InbreedingCoeff=-3.89810e-05;AS_VQSLOD=-7.93550e+00;NEGATIVE_TRAIN_SITE;culprit=AS_QD;SOR=4.29000e-01;AC_asj_female=0;AN_asj_female=1166;AF_asj_female=0.00000e+00;nhomalt_asj_female=0;AC_eas_female=0;AN_eas_female=882;AF_eas_female=0.00000e+00;nhomalt_eas_female=0;AC_afr_male=0;AN_afr_male=12040;AF_afr_male=0.00000e+00;nhomalt_afr_male=0;AC_female=1;AN_female=47502;AF_female=2.10517e-05;nhomalt_female=0;AC_fin_male=0;AN_fin_male=4522;AF_fin_male=0.00000e+00;nhomalt_fin_male=0;AC_oth_female=0;AN_oth_female=704;AF_oth_female=0.00000e+00;nhomalt_oth_female=0;AC_ami=0;AN_ami=688;AF_ami=0.00000e+00;nhomalt_ami=0;AC_oth=0;AN_oth=1330;AF_oth=0.00000e+00;nhomalt_oth=0;AC_male=0;AN_male=42136;AF_male=0.00000e+00;nhomalt_male=0;AC_ami_female=0;AN_ami_female=352;AF_ami_female=0.00000e+00;nhomalt_ami_female=0;AC_afr=0;AN_afr=26658;AF_afr=0.00000e+00;nhomalt_afr=0;AC_eas_male=0;AN_eas_male=1156;AF_eas_male=0.00000e+00;nhomalt_eas_male=0;AC_sas=0;AN_sas=1802;AF_sas=0.00000e+00;nhomalt_sas=0;AC_nfe_female=0;AN_nfe_female=24944;AF_nfe_female=0.00000e+00;nhomalt_nfe_female=0;AC_asj_male=0;AN_asj_male=1094;AF_asj_male=0.00000e+00;nhomalt_asj_male=0;AC_raw=4;AN_raw=102618;AF_raw=3.89795e-05;nhomalt_raw=0;AC_oth_male=0;AN_oth_male=626;AF_oth_male=0.00000e+00;nhomalt_oth_male=0;AC_nfe_male=0;AN_nfe_male=17104;AF_nfe_male=0.00000e+00;nhomalt_nfe_male=0;AC_asj=0;AN_asj=2260;AF_asj=0.00000e+00;nhomalt_asj=0;AC_amr_male=0;AN_amr_male=3814;AF_amr_male=0.00000e+00;nhomalt_amr_male=0;nhomalt=0;AC_amr_female=0;AN_amr_female=3438;AF_amr_female=0.00000e+00;nhomalt_amr_female=0;AC_sas_female=0;AN_sas_female=358;AF_sas_female=0.00000e+00;nhomalt_sas_female=0;AC_fin=1;AN_fin=5562;AF_fin=1.79791e-04;nhomalt_fin=0;AC_afr_female=0;AN_afr_female=14618;AF_afr_female=0.00000e+00;nhomalt_afr_female=0;AC_sas_male=0;AN_sas_male=1444;AF_sas_male=0.00000e+00;nhomalt_sas_male=0;AC_amr=0;AN_amr=7252;AF_amr=0.00000e+00;nhomalt_amr=0;AC_nfe=0;AN_nfe=42048;AF_nfe=0.00000e+00;nhomalt_nfe=0;AC_eas=0;AN_eas=2038;AF_eas=0.00000e+00;nhomalt_eas=0;AC_ami_male=0;AN_ami_male=336;AF_ami_male=0.00000e+00;nhomalt_ami_male=0;AC_fin_female=1;AN_fin_female=1040;AF_fin_female=9.61538e-04;nhomalt_fin_female=0;faf95_afr=0.00000e+00;faf99_afr=0.00000e+00;faf95_sas=0.00000e+00;faf99_sas=0.00000e+00;faf95_adj=0.00000e+00;faf99_adj=0.00000e+00;faf95_amr=0.00000e+00;faf99_amr=0.00000e+00;faf95_nfe=0.00000e+00;faf99_nfe=0.00000e+00;faf95_eas=0.00000e+00;faf99_eas=0.00000e+00;vep=C|upstream_gene_variant|MODIFIER|DDX11L1|ENSG00000223972|Transcript|ENST00000450305|transcribed_unprocessed_pseudogene|||,C|upstream_gene_variant|MODIFIER|DDX11L1|ENSG00000223972|Transcript|ENST00000456328|processed_transcript|||,C|downstream_gene_variant|MODIFIER|WASH7P|ENSG00000227232|Transcript|ENST00000488147|unprocessed_pseudogene|||
chrA   5   .  A   C   264.00 AS_VQSR     AC=3;AN=107374;AF=2.79397e-05;lcr;variant_type=snv;n_alt_alleles=1;ReadPosRankSum=-6.84000e-01;MQRankSum=7.88000e-01;RAW_MQ=2.27886e+05;DP=128;MQ_DP=175;VarDP=128;MQ=3.60861e+01;QD=2.06250e+00;FS=3.78704e+01;SB=97,29,13,19;InbreedingCoeff=-2.55009e-05;AS_VQSLOD=-2.48174e+01;culprit=AS_FS;SOR=7.58000e-01;AC_asj_female=0;AN_asj_female=1436;AF_asj_female=0.00000e+00;nhomalt_asj_female=0;AC_eas_female=0;AN_eas_female=1112;AF_eas_female=0.00000e+00;nhomalt_eas_female=0;AC_afr_male=1;AN_afr_male=14218;AF_afr_male=7.03334e-05;nhomalt_afr_male=0;AC_female=2;AN_female=56570;AF_female=3.53544e-05;nhomalt_female=0;AC_fin_male=0;AN_fin_male=5358;AF_fin_male=0.00000e+00;nhomalt_fin_male=0;AC_oth_female=0;AN_oth_female=832;AF_oth_female=0.00000e+00;nhomalt_oth_female=0;AC_ami=0;AN_ami=736;AF_ami=0.00000e+00;nhomalt_ami=0;AC_oth=0;AN_oth=1600;AF_oth=0.00000e+00;nhomalt_oth=0;AC_male=1;AN_male=50804;AF_male=1.96835e-05;nhomalt_male=0;AC_ami_female=0;AN_ami_female=382;AF_ami_female=0.00000e+00;nhomalt_ami_female=0;AC_afr=1;AN_afr=31312;AF_afr=3.19366e-05;nhomalt_afr=0;AC_eas_male=0;AN_eas_male=1384;AF_eas_male=0.00000e+00;nhomalt_eas_male=0;AC_sas=0;AN_sas=2250;AF_sas=0.00000e+00;nhomalt_sas=0;AC_nfe_female=2;AN_nfe_female=29570;AF_nfe_female=6.76361e-05;nhomalt_nfe_female=0;AC_asj_male=0;AN_asj_male=1208;AF_asj_male=0.00000e+00;nhomalt_asj_male=0;AC_raw=3;AN_raw=117646;AF_raw=2.55002e-05;nhomalt_raw=0;AC_oth_male=0;AN_oth_male=768;AF_oth_male=0.00000e+00;nhomalt_oth_male=0;AC_nfe_male=0;AN_nfe_male=20634;AF_nfe_male=0.00000e+00;nhomalt_nfe_male=0;AC_asj=0;AN_asj=2644;AF_asj=0.00000e+00;nhomalt_asj=0;AC_amr_male=0;AN_amr_male=5044;AF_amr_male=0.00000e+00;nhomalt_amr_male=0;nhomalt=0;AC_amr_female=0;AN_amr_female=4286;AF_amr_female=0.00000e+00;nhomalt_amr_female=0;AC_sas_female=0;AN_sas_female=414;AF_sas_female=0.00000e+00;nhomalt_sas_female=0;AC_fin=0;AN_fin=6802;AF_fin=0.00000e+00;nhomalt_fin=0;AC_afr_female=0;AN_afr_female=17094;AF_afr_female=0.00000e+00;nhomalt_afr_female=0;AC_sas_male=0;AN_sas_male=1836;AF_sas_male=0.00000e+00;nhomalt_sas_male=0;AC_amr=0;AN_amr=9330;AF_amr=0.00000e+00;nhomalt_amr=0;AC_nfe=2;AN_nfe=50204;AF_nfe=3.98375e-05;nhomalt_nfe=0;AC_eas=0;AN_eas=2496;AF_eas=0.00000e+00;nhomalt_eas=0;AC_ami_male=0;AN_ami_male=354;AF_ami_male=0.00000e+00;nhomalt_ami_male=0;AC_fin_female=0;AN_fin_female=1444;AF_fin_female=0.00000e+00;nhomalt_fin_female=0;faf95_afr=0.00000e+00;faf99_afr=0.00000e+00;faf95_sas=0.00000e+00;faf99_sas=0.00000e+00;faf95_adj=7.42000e-06;faf99_adj=7.06000e-06;faf95_amr=0.00000e+00;faf99_amr=0.00000e+00;faf95_nfe=6.61000e-06;faf99_nfe=6.47000e-06;faf95_eas=0.00000e+00;faf99_eas=0.00000e+00;vep=C|upstream_gene_variant|MODIFIER|DDX11L1|ENSG00000223972|Transcript|ENST00000450305|transcribed_unprocessed_pseudogene|||,C|upstream_gene_variant|MODIFIER|DDX11L1|ENSG00000223972|Transcript|ENST00000456328|processed_transcript|||,C|downstream_gene_variant|MODIFIER|WASH7P|ENSG00000227232|Transcript|ENST00000488147|unprocessed_pseudogene|||
        """)  # noqa
    )
    res = build_filesystem_test_resource(root_path)
    return AlleleScore(res).open()


def test_gnomad_vcf_resource(vcf_info_gnomad):
    vcf_info_gnomad.open()
    scores = vcf_info_gnomad.score_definitions

    assert "AF" in scores
    info = scores["AF"]

    assert info.score_index == "AF"
    assert info.desc is not None

    info = scores["AN"]
    assert info.score_index == "AN"


@pytest.mark.parametrize("chrom,start,end,scores,expected", [
    (
        "chrA", 1, 2, ["AN", "AC"],
        [
            {"AN": 53780, "AC": 0},
            {"AN": 72762, "AC": 2},
        ]
    ),
    (
        "chrA", 1, 3, ["AN", "AC"],
        [
            {"AN": 53780, "AC": 0},
            {"AN": 72762, "AC": 2},
            {"AN": 81114, "AC": 1},
        ]
    ),
    (
        "chrA", 1, 2, ["lcr", "non_par", "variant_type"],
        [
            {"lcr": True, "non_par": False, "variant_type": "snv"},
            {"lcr": True, "non_par": False, "variant_type": "snv"},
        ]
    ),
    (
        "chrA", 4, 5, ["culprit", "NEGATIVE_TRAIN_SITE", "AN_asj_female"],
        [
            {"culprit": "AS_QD", "NEGATIVE_TRAIN_SITE": True,
             "AN_asj_female": 1166},
            {"culprit": "AS_FS", "NEGATIVE_TRAIN_SITE": False,
             "AN_asj_female": 1436},
        ]
    ),
    (
        "chrA", 4, 5, ["SB"],
        [
            {"SB": "47,22,6,7"},
            {"SB": "97,29,13,19"},
        ]
    ),
])
def test_gnomad_vcf_fetch_region(
        vcf_info_gnomad, chrom, start, end, scores, expected):
    result = list(vcf_info_gnomad.fetch_region(chrom, start, end, scores))
    assert result == expected


@pytest.mark.parametrize("chrom,pos,ref,alt,scores,expected", [
    (
        "chrA", 1, "A", "C", ["AN", "AC"],
        [53780, 0],
    ),
    (
        "chrA", 1, "A", "G", ["AN", "AC"],
        None,
    ),
    (
        "chrA", 4, "A", "C", ["AN", "AC"],
        [89638, 1],
    ),
])
def test_gnomad_vcf_fetch_rscores(
        vcf_info_gnomad, chrom, pos, ref, alt, scores, expected):
    result = vcf_info_gnomad.fetch_scores(chrom, pos, ref, alt, scores)
    assert result == expected

# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest

from dae.genomic_resources.gene_models import (
    GeneModels,
    build_gene_models_from_resource,
    models_to_gtf,
)
from dae.genomic_resources.testing import (
    build_inmemory_test_resource,
    convert_to_tab_separated,
)


@pytest.fixture()
def ensembl_gtf_example() -> GeneModels:
    # Example from: https://ftp.ensembl.org/pub/current/gtf/homo_sapiens/README
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": convert_to_tab_separated(textwrap.dedent("""
#!genome-build GRCh38
11  ensembl_havana  gene        5422111  5423206  .  +  .  gene_id||"ENSG00000167360";gene_version||"4";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";
11  ensembl_havana  transcript  5422111  5423206  .  +  .  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";
11  ensembl_havana  exon        5422111  5423206  .  +  .  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";exon_number||"1";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";exon_id||"ENSE00001276439";exon_version||"4";
11  ensembl_havana  CDS         5422201  5423151  .  +  0  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";exon_number||"1";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";protein_id||"ENSP00000300778";protein_version||"4";
11  ensembl_havana  start_codon 5422201  5422203  .  +  0  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";exon_number||"1";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";
11  ensembl_havana  stop_codon  5423152  5423154  .  +  0  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";exon_number||"1";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";
11  ensembl_havana  UTR         5422111  5422200  .  +  .  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";
11  ensembl_havana  UTR         5423155  5423206  .  +  .  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";tag||"a||b||c";
""")),  # noqa: E501
        })
    return build_gene_models_from_resource(res)


@pytest.fixture()
def ensembl_gtf_example_shh() -> GeneModels:
    # SHH = Sonic hedgehog gene
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": convert_to_tab_separated(textwrap.dedent("""
chr7    HAVANA  gene    155799980       155812463       .       -       .       gene_id||"ENSG00000164690.8";||gene_type||"protein_coding";||gene_name||"SHH";||level||2;||hgnc_id||"HGNC:10848";||havana_gene||"OTTHUMG00000151349.3";
chr7    HAVANA  transcript      155799980       155812463       .       -       .       gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7    HAVANA  exon    155811823       155812463       .       -       .       gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||1;||exon_id||"ENSE00001086614.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7    HAVANA  CDS     155811823       155812122       .       -       0       gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||1;||exon_id||"ENSE00001086614.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7    HAVANA  start_codon     155812120       155812122       .       -       0       gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||1;||exon_id||"ENSE00001086614.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7    HAVANA  exon    155806296       155806557       .       -       .       gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||2;||exon_id||"ENSE00001086617.1";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7    HAVANA  CDS     155806296       155806557       .       -       0       gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||2;||exon_id||"ENSE00001086617.1";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7    HAVANA  exon    155799980       155803726       .       -       .       gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||3;||exon_id||"ENSE00001149618.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7    HAVANA  CDS     155802903       155803726       .       -       2       gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||3;||exon_id||"ENSE00001149618.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7    HAVANA  stop_codon      155802900       155802902       .       -       0       gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||3;||exon_id||"ENSE00001149618.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7    HAVANA  UTR     155812123       155812463       .       -       .       gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||1;||exon_id||"ENSE00001086614.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7    HAVANA  UTR     155799980       155802902       .       -       .       gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||3;||exon_id||"ENSE00001149618.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
"""))})  # noqa: E501
    return build_gene_models_from_resource(res)


@pytest.fixture()
def gencode_46_calml6_example() -> GeneModels:
    # CALML6
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": convert_to_tab_separated(textwrap.dedent("""
chr1        HAVANA      gene        1915108     1917296     .           +           .           gene_id||"ENSG00000169885.10";||gene_type||"protein_coding";||gene_name||"CALML6";||level||1;||hgnc_id||"HGNC:24193";||havana_gene||"OTTHUMG00000000943.3";
chr1        HAVANA      transcript  1915260     1917296     .           +           .           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      exon        1915260     1915307     .           +           .           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      CDS         1915281     1915307     .           +           0           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      start_codon 1915281     1915283     .           +           0           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      exon        1915685     1915735     .           +           .           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      CDS         1915685     1915735     .           +           0           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      exon        1916441     1916615     .           +           .           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      CDS         1916441     1916615     .           +           0           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      exon        1916752     1916896     .           +           .           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      CDS         1916752     1916896     .           +           2           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      exon        1916974     1917074     .           +           .           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      CDS         1916974     1917074     .           +           1           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      exon        1917147     1917296     .           +           .           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      CDS         1917147     1917190     .           +           2           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      stop_codon  1917191     1917193     .           +           0           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      UTR         1915260     1915280     .           +           .           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
chr1        HAVANA      UTR         1917191     1917296     .           +           .           gene_id||"ENSG00000169885.10";||transcript_id||"ENST00000307786.8";||gene_type||"protein_coding";||gene_name||"CALML6";||transcript_type||"protein_coding";
"""))})  # noqa: E501
    return build_gene_models_from_resource(res)


@pytest.fixture()
def ensembl_gtf_example_noncoding() -> GeneModels:
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": convert_to_tab_separated(textwrap.dedent("""
chr1    HAVANA    gene    89295    133566    .    -    .    gene_id||"ENSG00000238009.7";||gene_type||"lncRNA";||gene_name||"ENSG00000238009";||level||2;||tag||"overlapping_locus";||havana_gene||"OTTHUMG00000001096.2";
chr1    HAVANA    transcript    89295    120932    .    -    .    gene_id||"ENSG00000238009.7";||transcript_id||"ENST00000466430.5";||gene_type||"lncRNA";||gene_name||"ENSG00000238009";||transcript_type||"lncRNA";||transcript_name||"ENST00000466430";||level||2;||transcript_support_level||"5";||tag||"not_best_in_genome_evidence";||tag||"basic";||havana_gene||"OTTHUMG00000001096.2";||havana_transcript||"OTTHUMT00000003225.1";
chr1    HAVANA    exon    120775    120932    .    -    .    gene_id||"ENSG00000238009.7";||transcript_id||"ENST00000466430.5";||gene_type||"lncRNA";||gene_name||"ENSG00000238009";||transcript_type||"lncRNA";||transcript_name||"ENST00000466430";||exon_number||1;||exon_id||"ENSE00001606755.2";||level||2;||transcript_support_level||"5";||tag||"not_best_in_genome_evidence";||tag||"basic";||havana_gene||"OTTHUMG00000001096.2";||havana_transcript||"OTTHUMT00000003225.1";
chr1    HAVANA    exon    112700    112804    .    -    .    gene_id||"ENSG00000238009.7";||transcript_id||"ENST00000466430.5";||gene_type||"lncRNA";||gene_name||"ENSG00000238009";||transcript_type||"lncRNA";||transcript_name||"ENST00000466430";||exon_number||2;||exon_id||"ENSE00001957285.1";||level||2;||transcript_support_level||"5";||tag||"not_best_in_genome_evidence";||tag||"basic";||havana_gene||"OTTHUMG00000001096.2";||havana_transcript||"OTTHUMT00000003225.1";
chr1    HAVANA    exon    92091    92240    .    -    .    gene_id||"ENSG00000238009.7";||transcript_id||"ENST00000466430.5";||gene_type||"lncRNA";||gene_name||"ENSG00000238009";||transcript_type||"lncRNA";||transcript_name||"ENST00000466430";||exon_number||3;||exon_id||"ENSE00001944529.1";||level||2;||transcript_support_level||"5";||tag||"not_best_in_genome_evidence";||tag||"basic";||havana_gene||"OTTHUMG00000001096.2";||havana_transcript||"OTTHUMT00000003225.1";
chr1    HAVANA    exon    89295    91629    .    -    .    gene_id||"ENSG00000238009.7";||transcript_id||"ENST00000466430.5";||gene_type||"lncRNA";||gene_name||"ENSG00000238009";||transcript_type||"lncRNA";||transcript_name||"ENST00000466430";||exon_number||4;||exon_id||"ENSE00001846804.1";||level||2;||transcript_support_level||"5";||tag||"not_best_in_genome_evidence";||tag||"basic";||havana_gene||"OTTHUMG00000001096.2";||havana_transcript||"OTTHUMT00000003225.1";
"""))})  # noqa: E501
    return build_gene_models_from_resource(res)


@pytest.fixture()
def gtf_example_no_exons() -> GeneModels:
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": convert_to_tab_separated(textwrap.dedent("""
chr1    HAVANA    gene    89295    133566    .    -    .    gene_id||"ENSG00000238009.7";||gene_type||"lncRNA";||gene_name||"ENSG00000238009";||level||2;||tag||"overlapping_locus";||havana_gene||"OTTHUMG00000001096.2";
chr1    HAVANA    transcript    89295    120932    .    -    .    gene_id||"ENSG00000238009.7";||transcript_id||"ENST00000466430.5";||gene_type||"lncRNA";||gene_name||"ENSG00000238009";||transcript_type||"lncRNA";||transcript_name||"ENST00000466430";||level||2;||transcript_support_level||"5";||tag||"not_best_in_genome_evidence";||tag||"basic";||havana_gene||"OTTHUMG00000001096.2";||havana_transcript||"OTTHUMT00000003225.1";
"""))})  # noqa: E501
    return build_gene_models_from_resource(res)


def test_save_as_gtf_simple(ensembl_gtf_example: GeneModels) -> None:
    reference = ensembl_gtf_example
    reference.load()
    serialized = models_to_gtf(reference)

    gene_models = build_gene_models_from_resource(build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": serialized,
    }))
    gene_models.load()

    assert len(gene_models.gene_models) == 1
    assert len(gene_models.transcript_models) == 1
    assert "OR51Q1" in gene_models.gene_models

    assert "ENST00000300778" in gene_models.transcript_models
    tm = gene_models.transcript_models["ENST00000300778"]

    assert tm.tr_id == "ENST00000300778"
    assert tm.cds == (5422201, 5423154)
    assert tm.tx == (5422111, 5423206)
    assert len(tm.exons) == 1
    assert tm.strand == "+"


def test_save_as_gtf_complex(ensembl_gtf_example_shh: GeneModels) -> None:
    example_models = ensembl_gtf_example_shh
    example_models.load()
    serialized = models_to_gtf(example_models)

    assert "start_codon\t155812120\t155812122" in serialized
    assert "stop_codon\t155802900\t155802902" in serialized

    gene_models = build_gene_models_from_resource(build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": serialized,
    }))
    gene_models.load()

    assert len(gene_models.gene_models) == 1
    assert len(gene_models.transcript_models) == 1
    assert "SHH" in gene_models.gene_models

    assert "ENST00000297261.7" in gene_models.transcript_models
    tm = gene_models.transcript_models["ENST00000297261.7"]

    assert tm.tr_id == "ENST00000297261.7"
    assert tm.cds == (155802900, 155812122)
    assert tm.tx == (155799980, 155812463)
    assert len(tm.exons) == 3
    assert tm.strand == "-"


def test_save_as_gtf_noncoding(
    ensembl_gtf_example_noncoding: GeneModels,
) -> None:
    example_models = ensembl_gtf_example_noncoding
    example_models.load()
    serialized = models_to_gtf(example_models)

    gene_models = build_gene_models_from_resource(build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": serialized,
    }))
    gene_models.load()
    assert len(gene_models.gene_models) == 1
    assert len(gene_models.transcript_models) == 1
    assert "ENSG00000238009" in gene_models.gene_models
    assert "ENST00000466430.5" in gene_models.transcript_models
    tm = gene_models.transcript_models["ENST00000466430.5"]

    assert tm.tr_id == "ENST00000466430.5"
    assert tm.cds == (120932, 89295)
    assert tm.tx == (89295, 120932)
    assert tm.is_coding() is False
    assert len(tm.exons) == 4
    assert tm.strand == "-"


def test_save_as_gtf_no_exons(
    gtf_example_no_exons: GeneModels,
) -> None:
    example_models = gtf_example_no_exons
    example_models.load()
    serialized = models_to_gtf(example_models)

    gene_models = build_gene_models_from_resource(build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": serialized,
    }))
    gene_models.load()
    assert len(gene_models.gene_models) == 1
    assert len(gene_models.transcript_models) == 1
    assert "ENSG00000238009" in gene_models.gene_models
    assert "ENST00000466430.5" in gene_models.transcript_models
    tm = gene_models.transcript_models["ENST00000466430.5"]

    assert tm.tr_id == "ENST00000466430.5"
    assert tm.cds == (120932, 89295)
    assert tm.tx == (89295, 120932)
    assert tm.is_coding() is False
    assert len(tm.exons) == 0
    assert tm.strand == "-"

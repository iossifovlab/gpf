# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from collections.abc import Callable

import pytest

from dae.genomic_resources.gene_models import (
    Exon,
    GeneModels,
    TranscriptModel,
    build_gene_models_from_resource,
)
from dae.genomic_resources.gene_models.serialization import (
    calc_frame_for_gtf_cds_feature,
    collect_gtf_cds_regions,
    collect_gtf_start_codon_regions,
    collect_gtf_stop_codon_regions,
    find_exon_cds_region_for_gtf_cds_feature,
    gene_models_to_gtf,
)
from dae.genomic_resources.testing import (
    build_inmemory_test_resource,
    convert_to_tab_separated,
)
from dae.utils.regions import BedRegion


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
chr7  HAVANA  gene         155799980  155812463  .  -  .  gene_id||"ENSG00000164690.8";||gene_type||"protein_coding";||gene_name||"SHH";||level||2;||hgnc_id||"HGNC:10848";||havana_gene||"OTTHUMG00000151349.3";
chr7  HAVANA  transcript   155799980  155812463  .  -  .  gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7  HAVANA  exon         155811823  155812463  .  -  .  gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||1;||exon_id||"ENSE00001086614.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7  HAVANA  CDS          155811823  155812122  .  -  0  gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||1;||exon_id||"ENSE00001086614.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7  HAVANA  start_codon  155812120  155812122  .  -  0  gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||1;||exon_id||"ENSE00001086614.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7  HAVANA  exon         155806296  155806557  .  -  .  gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||2;||exon_id||"ENSE00001086617.1";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7  HAVANA  CDS          155806296  155806557  .  -  0  gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||2;||exon_id||"ENSE00001086617.1";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7  HAVANA  exon         155799980  155803726  .  -  .  gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||3;||exon_id||"ENSE00001149618.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7  HAVANA  CDS          155802903  155803726  .  -  2  gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||3;||exon_id||"ENSE00001149618.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7  HAVANA  stop_codon   155802900  155802902  .  -  0  gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||3;||exon_id||"ENSE00001149618.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7  HAVANA  UTR          155812123  155812463  .  -  .  gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||1;||exon_id||"ENSE00001086614.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
chr7  HAVANA  UTR          155799980  155802902  .  -  .  gene_id||"ENSG00000164690.8";||transcript_id||"ENST00000297261.7";||gene_type||"protein_coding";||gene_name||"SHH";||transcript_type||"protein_coding";||transcript_name||"SHH-201";||exon_number||3;||exon_id||"ENSE00001149618.3";||level||2;||protein_id||"ENSP00000297261.2";||transcript_support_level||"1";||hgnc_id||"HGNC:10848";||tag||"basic";||tag||"Ensembl_canonical";||tag||"GENCODE_Primary";||tag||"MANE_Select";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS5942.1";||havana_gene||"OTTHUMG00000151349.3";||havana_transcript||"OTTHUMT00000322327.2";
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


@pytest.fixture()
def gtf_example_split_start_stop_codons() -> GeneModels:
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": convert_to_tab_separated(textwrap.dedent("""
chr1    TEST    gene          1    100    .    +    .    gene_id||"GENE";||gene_name||"GENE";
chr1    TEST    transcript    1    100    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    exon          21    21    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    CDS           21    21    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    exon          24    24    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    CDS           24    24    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    exon          27    40    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    CDS           27    40    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    start_codon   21    21    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    start_codon   24    24    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    start_codon   27    27    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    exon          50    73    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    CDS           50    73    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    exon          74    74    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    exon          78   100    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    stop_codon    74    74    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    stop_codon    78    79    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    UTR           1     20    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    UTR           74    74    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
chr1    TEST    UTR           78   100    .    +    .    gene_id||"GENE";||transcript_id||"TRANSCRIPT";||gene_name||"GENE";
"""))})  # noqa: E501
    return build_gene_models_from_resource(res)


def test_save_as_gtf_simple(ensembl_gtf_example: GeneModels) -> None:
    reference = ensembl_gtf_example
    reference.load()
    serialized = gene_models_to_gtf(reference)

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
    serialized = gene_models_to_gtf(example_models)

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
    serialized = gene_models_to_gtf(example_models)

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
    serialized = gene_models_to_gtf(example_models)

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


def test_save_as_gtf_split_start_stop_codons(
    gtf_example_split_start_stop_codons: GeneModels,
) -> None:
    example_models = gtf_example_split_start_stop_codons
    example_models.load()
    serialized = gene_models_to_gtf(example_models)

    gene_models = build_gene_models_from_resource(build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": serialized,
    }))
    gene_models.load()

    assert "start_codon\t21\t21" in serialized
    assert "start_codon\t24\t24" in serialized
    assert "start_codon\t27\t27" in serialized

    assert "stop_codon\t74\t74" in serialized
    assert "stop_codon\t78\t79" in serialized

    tm = gene_models.transcript_models["TRANSCRIPT"]
    assert tm.cds == (21, 79)
    assert tm.tx == (1, 100)
    assert tm.is_coding() is True
    assert len(tm.exons) == 6
    assert tm.strand == "+"
    assert tm.cds_regions() == [
        BedRegion("chr1", 21, 21),
        BedRegion("chr1", 24, 24),
        BedRegion("chr1", 27, 40),
        BedRegion("chr1", 50, 73),
        BedRegion("chr1", 74, 74),
        BedRegion("chr1", 78, 79),
    ]


@pytest.mark.parametrize(
    "expected", [
        [
            ".", ".", ".", ".", "0", "0", ".", "0", ".",
            "0", ".", "2", ".", "1", ".", "2", "0", ".",
        ],
    ],
)
def test_phase_field_serialization_positive_strand(
    gencode_46_calml6_example: GeneModels,
    expected: list[str],
) -> None:
    example_models = gencode_46_calml6_example
    example_models.load()
    serialized = gene_models_to_gtf(example_models)

    # [4:] skips auto-generated comment lines
    line_phases = [
        line.split("\t")[:8]
        for line in serialized.strip().split("\n")[4:]
    ]

    for idx, line in enumerate(line_phases):
        print(line, expected[idx])
        phase = line[7]
        assert phase == expected[idx]


@pytest.mark.parametrize(
    "expected", [
        [
            ("stop_codon", "0"),
            ("CDS", "2"),
            ("CDS", "0"),
            ("CDS", "0"),
            ("start_codon", "0"),
        ],
    ],
)
def test_phase_field_serialization_negative_strand(
    ensembl_gtf_example_shh: GeneModels,
    expected: list[tuple[str, str]],
) -> None:
    example_models = ensembl_gtf_example_shh
    example_models.load()
    serialized = gene_models_to_gtf(example_models)

    line_phases = [
        line.split("\t")[:8]
        for line in serialized.strip().split("\n")[4:]
    ]
    line_phases = [
        ln for ln in line_phases
        if ln[2] in {"CDS", "start_codon", "stop_codon"}
    ]

    assert expected == [(ln[2], ln[7]) for ln in line_phases]


@pytest.mark.parametrize(
    "strand,regions,expected", [
        (
            "+",
            [(1, 5)],
            [(1, 3)],
        ),
        (
            "+",
            [(1, 2), (10, 15)],
            [(1, 2), (10, 10)],
        ),
        (
            "+",
            [(1, 1), (10, 10), (20, 25)],
            [(1, 1), (10, 10), (20, 20)],
        ),
        (
            "-",
            [(1, 5)],
            [(3, 5)],
        ),
        (
            "-",
            [(1, 5), (10, 10)],
            [(4, 5), (10, 10)],
        ),
        (
            "-",
            [(1, 5), (10, 11)],
            [(5, 5), (10, 11)],
        ),
        (
            "-",
            [(1, 5), (10, 10), (20, 20)],
            [(5, 5), (10, 10), (20, 20)],
        ),
    ],
)
def test_collect_gtf_start_codon_regions(
    strand: str,
    regions: list[tuple[int, int]],
    expected: list[tuple[int, int]],
) -> None:
    cds_regions = [
        BedRegion("chr1", start, end)
        for start, end in regions
    ]
    start_codons = collect_gtf_start_codon_regions(strand, cds_regions)
    assert len(start_codons) == len(expected)
    assert [(sc.start, sc.end) for sc in start_codons] == expected


@pytest.mark.parametrize(
    "strand,regions,expected", [
        (
            "+",
            [(1, 5)],
            [(3, 5)],
        ),
        (
            "+",
            [(1, 5), (10, 10)],
            [(4, 5), (10, 10)],
        ),
        (
            "+",
            [(1, 5), (10, 10), (20, 20)],
            [(5, 5), (10, 10), (20, 20)],
        ),
        (
            "-",
            [(1, 5)],
            [(1, 3)],
        ),
        (
            "-",
            [(1, 1), (10, 15)],
            [(1, 1), (10, 11)],
        ),
        (
            "-",
            [(1, 1), (10, 10), (20, 25)],
            [(1, 1), (10, 10), (20, 20)],
        ),
    ],
)
def test_collect_gtf_stop_codon_regions(
    strand: str,
    regions: list[tuple[int, int]],
    expected: list[tuple[int, int]],
) -> None:
    cds_regions = [
        BedRegion("chr1", start, end)
        for start, end in regions
    ]
    start_codons = collect_gtf_stop_codon_regions(strand, cds_regions)
    assert len(start_codons) == len(expected)
    assert [(sc.start, sc.end) for sc in start_codons] == expected


@pytest.mark.parametrize(
    "strand,regions,expected", [
        (
            "+",
            [(1, 5)],
            [(1, 2)],
        ),
        (
            "+",
            [(1, 5), (10, 10)],
            [(1, 3)],
        ),
        (
            "+",
            [(1, 5), (10, 10), (20, 20)],
            [(1, 4)],
        ),
        (
            "-",
            [(1, 5)],
            [(4, 5)],
        ),
        (
            "-",
            [(1, 1), (10, 15)],
            [(12, 15)],
        ),
        (
            "-",
            [(1, 1), (10, 10), (20, 25)],
            [(21, 25)],
        ),
    ],
)
def test_collect_gtf_cds_regions(
    strand: str,
    regions: list[tuple[int, int]],
    expected: list[tuple[int, int]],
) -> None:
    cds_regions = [
        BedRegion("chr1", start, end)
        for start, end in regions
    ]
    start_codons = collect_gtf_cds_regions(strand, cds_regions)
    assert len(start_codons) == len(expected)
    assert [(sc.start, sc.end) for sc in start_codons] == expected


def test_find_exon_for_gtf_cds_feature(
    gencode_46_calml6_example: GeneModels,
) -> None:
    example_models = gencode_46_calml6_example
    example_models.load()
    transcript = example_models.transcript_models["ENST00000307786.8"]
    assert transcript is not None

    cds_regions = transcript.cds_regions()

    start_codons = collect_gtf_start_codon_regions(
        transcript.strand, cds_regions)
    assert len(start_codons) == 1
    start_codon = start_codons[0]
    exon, _ = find_exon_cds_region_for_gtf_cds_feature(transcript, start_codon)
    assert exon is not None
    assert exon.frame == 0

    stop_codons = collect_gtf_stop_codon_regions(
        transcript.strand, cds_regions)
    assert stop_codons
    assert len(stop_codons) == 1
    stop_codon = stop_codons[0]
    exon, _ = find_exon_cds_region_for_gtf_cds_feature(transcript, stop_codon)
    assert exon is not None
    assert exon.frame == 1

    cds = collect_gtf_cds_regions(
        transcript.strand, cds_regions)
    assert cds


@pytest.fixture()
def transcript_builder() -> Callable[
    [list[tuple[int, int]], tuple[int, int], str],
    TranscriptModel,
]:
    def _builder(
        regions: list[tuple[int, int]],
        cds: tuple[int, int],
        strand: str,
    ) -> TranscriptModel:
        exons = [Exon(start, stop) for start, stop in regions]  # noqa: FURB140
        tx = (exons[0].start, exons[-1].stop)

        transcript = TranscriptModel(
            "test_gene_1",
            "test_transcript_1",
            "test_transcript_1",
            "chr1",
            strand,
            tx,
            cds,
            exons,
        )
        transcript.update_frames()
        return transcript

    return _builder


@pytest.mark.parametrize(
    "tr_data,expected_exons,expected_exon_frames", [
        (
            ("+", [(10, 39)], (10, 39)),
            [(10, 39)],
            [0],
        ),
        (
            ("+", [(10, 50)], (10, 39)),
            [(10, 50)],
            [0],
        ),
        (
            ("+", [(10, 11), (20, 49)], (10, 49)),
            [(10, 11), (20, 49)],
            [0, 2],
        ),
        (
            ("+", [(10, 10), (21, 21), (32, 59)], (10, 59)),
            [(10, 10), (21, 21), (32, 59)],
            [0, 1, 2],
        ),
        (
            ("-", [(10, 39)], (10, 39)),
            [(10, 39)],
            [0],
        ),
        (
            ("-", [(10, 38), (40, 40)], (10, 40)),
            [(10, 38), (40, 40)],
            [1, 0],
        ),
        (
            ("-", [(10, 37), (41, 41), (50, 50)], (10, 50)),
            [(10, 37), (41, 41), (50, 50)],
            [2, 1, 0],
        ),
    ],
)
def test_find_exon_for_gtf_start_codons(
    transcript_builder: Callable[
        [list[tuple[int, int]], tuple[int, int], str],
        TranscriptModel,
    ],
    tr_data: tuple[str, list[tuple[int, int]], tuple[int, int]],
    expected_exons: list[tuple[int, int]],
    expected_exon_frames: list[int],
) -> None:
    strand, exons, cds = tr_data
    transcript = transcript_builder(exons, cds, strand)
    start_codons = collect_gtf_start_codon_regions(
        transcript.strand, transcript.cds_regions())
    assert len(start_codons) == len(expected_exons)
    sc_exons = []
    sc_frames = []
    for start_codon in start_codons:
        exon, _ = find_exon_cds_region_for_gtf_cds_feature(
            transcript, start_codon)
        assert exon is not None
        sc_exons.append((exon.start, exon.stop))
        sc_frames.append(exon.frame)

    assert len(sc_exons) == len(expected_exons)
    assert sc_exons == expected_exons

    assert len(sc_frames) == len(expected_exon_frames)
    assert sc_frames == expected_exon_frames


@pytest.mark.parametrize(
    "tr_data,expected_gtf_features,expected_gtf_frames", [
        (
            ("+", [(10, 39)], (10, 39)),
            [(10, 12)],
            [0],
        ),
        (
            ("+", [(10, 10), (21, 49)], (10, 49)),
            [(10, 10), (21, 22)],
            [0, 1],
        ),
        (
            ("+", [(10, 10), (21, 21), (32, 59)], (10, 59)),
            [(10, 10), (21, 21), (32, 32)],
            [0, 1, 2],
        ),

        (
            ("-", [(10, 39)], (10, 39)),
            [(37, 39)],
            [0],
        ),
        (
            ("-", [(10, 38), (49, 49)], (10, 49)),
            [(37, 38), (49, 49)],
            [1, 0],
        ),
        (
            ("-", [(10, 37), (48, 48), (59, 59)], (10, 59)),
            [(37, 37), (48, 48), (59, 59)],
            [2, 1, 0],
        ),
    ],
)
def test_calc_gtf_frame_for_start_codons(
    transcript_builder: Callable[
        [list[tuple[int, int]], tuple[int, int], str],
        TranscriptModel,
    ],
    tr_data: tuple[str, list[tuple[int, int]], tuple[int, int]],
    expected_gtf_features: list[tuple[int, int]],
    expected_gtf_frames: list[int],
) -> None:
    strand, exons, cds = tr_data
    transcript = transcript_builder(exons, cds, strand)
    start_codons = collect_gtf_start_codon_regions(
        transcript.strand, transcript.cds_regions())
    assert len(start_codons) == len(expected_gtf_features)
    assert [(sc.start, sc.stop) for sc in start_codons] == expected_gtf_features

    sc_frames = []
    for start_codon in start_codons:
        frame = calc_frame_for_gtf_cds_feature(transcript, start_codon)
        sc_frames.append(frame)

    assert len(sc_frames) == len(expected_gtf_frames)
    assert sc_frames == expected_gtf_frames


@pytest.mark.parametrize(
    "tr_data,expected_gtf_features,expected_gtf_frames", [
        (
            ("+", [(10, 39)], (10, 39)),
            [(37, 39)],
            [0],
        ),
        (
            ("+", [(10, 37), (48, 49)], (10, 49)),
            [(37, 37), (48, 49)],
            [0, 1],
        ),
        (
            ("+", [(10, 37), (48, 48), (59, 59)], (10, 59)),
            [(37, 37), (48, 48), (59, 59)],
            [0, 1, 2],
        ),

        (
            ("-", [(10, 39)], (10, 39)),
            [(10, 12)],
            [0],
        ),
        (
            ("-", [(10, 11), (22, 49)], (10, 49)),
            [(10, 11), (22, 22)],
            [1, 0],
        ),
        (
            ("-", [(10, 10), (21, 21), (32, 59)], (10, 59)),
            [(10, 10), (21, 21), (32, 32)],
            [2, 1, 0],
        ),
    ],
)
def test_calc_gtf_frame_for_stop_codons(
    transcript_builder: Callable[
        [list[tuple[int, int]], tuple[int, int], str],
        TranscriptModel,
    ],
    tr_data: tuple[str, list[tuple[int, int]], tuple[int, int]],
    expected_gtf_features: list[tuple[int, int]],
    expected_gtf_frames: list[int],
) -> None:
    strand, exons, cds = tr_data
    transcript = transcript_builder(exons, cds, strand)

    stop_codons = collect_gtf_stop_codon_regions(
        transcript.strand, transcript.cds_regions())
    assert len(stop_codons) == len(expected_gtf_features)
    assert [(sc.start, sc.stop) for sc in stop_codons] == expected_gtf_features

    sc_frames = []
    for start_codon in stop_codons:
        frame = calc_frame_for_gtf_cds_feature(transcript, start_codon)
        sc_frames.append(frame)

    assert len(sc_frames) == len(expected_gtf_frames)
    assert sc_frames == expected_gtf_frames


@pytest.mark.parametrize(
    "tr_data,expected_gtf_features,expected_gtf_frames", [
        (
            ("+", [(10, 39)], (10, 39)),
            [(10, 36)],
            [0],
        ),
        (
            ("+", [(10, 10), (21, 49)], (10, 49)),
            [(10, 10), (21, 46)],
            [0, 1],
        ),
        (
            ("+", [(10, 10), (21, 21), (32, 59)], (10, 59)),
            [(10, 10), (21, 21), (32, 56)],
            [0, 1, 2],
        ),

        (
            ("+", [(10, 13), (24, 49)], (10, 49)),
            [(10, 13), (24, 46)],
            [0, 1],
        ),
        (
            ("+", [(10, 12), (23, 49)], (10, 49)),
            [(10, 12), (23, 46)],
            [0, 0],
        ),

        (
            ("+", [(10, 12), (23, 26), (37, 59)], (10, 59)),
            [(10, 12), (23, 26), (37, 56)],
            [0, 0, 1],
        ),
        (
            ("+", [(10, 12), (23, 26), (37, 40), (51, 69)], (10, 69)),
            [(10, 12), (23, 26), (37, 40), (51, 66)],
            [0, 0, 1, 2],
        ),

        (
            ("-", [(10, 39)], (10, 39)),
            [(13, 39)],
            [0],
        ),
        (
            ("-", [(10, 38), (49, 49)], (10, 49)),
            [(13, 38), (49, 49)],
            [1, 0],
        ),
        (
            ("-", [(10, 36), (47, 49)], (10, 49)),
            [(13, 36), (47, 49)],
            [0, 0],
        ),
        (
            ("-", [(10, 35), (46, 49)], (10, 49)),
            [(13, 35), (46, 49)],
            [1, 0],
        ),
        (
            ("-", [(10, 34), (45, 49)], (10, 49)),
            [(13, 34), (45, 49)],
            [2, 0],
        ),

        (  # SHH gene
            (
                "-",
                [
                    (155799980, 155803726),
                    (155806296, 155806557),
                    (155811823, 155812463),
                ],
                (155802900, 155812122),
            ),
            [
                (155802903, 155803726),
                (155806296, 155806557),
                (155811823, 155812122),
            ],
            [1, 0, 0],
        ),
    ],
)
def test_calc_gtf_frame_for_cds(
    transcript_builder: Callable[
        [list[tuple[int, int]], tuple[int, int], str],
        TranscriptModel,
    ],
    tr_data: tuple[str, list[tuple[int, int]], tuple[int, int]],
    expected_gtf_features: list[tuple[int, int]],
    expected_gtf_frames: list[int],
) -> None:
    strand, exons, cds = tr_data
    transcript = transcript_builder(exons, cds, strand)

    regions = collect_gtf_cds_regions(
        transcript.strand, transcript.cds_regions())
    assert len(regions) == len(expected_gtf_features)
    assert [(r.start, r.stop) for r in regions] == expected_gtf_features

    frames = []
    for reg in regions:
        frame = calc_frame_for_gtf_cds_feature(transcript, reg)
        frames.append(frame)

    assert len(frames) == len(expected_gtf_frames)
    assert frames == expected_gtf_frames


def test_explore_shh_gene(
    ensembl_gtf_example_shh: GeneModels,
) -> None:
    gene_models = ensembl_gtf_example_shh
    gene_models.load()

    transcript = ensembl_gtf_example_shh.transcript_models["ENST00000297261.7"]
    assert transcript is not None

    assert transcript.strand == "-"
    assert transcript.cds == (155802900, 155812122)

    assert len(transcript.exons) == 3
    assert [
        (ex.start, ex.stop) for ex in transcript.exons
    ] == [
        (155799980, 155803726),
        (155806296, 155806557),
        (155811823, 155812463),
    ]

    cds_regions = transcript.cds_regions()
    assert len(cds_regions) == 3

    start_codons = collect_gtf_start_codon_regions(
        transcript.strand, cds_regions)
    assert len(start_codons) == 1

    assert [(sc.start, sc.stop) for sc in start_codons] == [
        (155812120, 155812122),
    ]

    stop_codons = collect_gtf_stop_codon_regions(
        transcript.strand, cds_regions)
    assert len(stop_codons) == 1
    assert [(sc.start, sc.stop) for sc in stop_codons] == [
        (155802900, 155802902),
    ]

    gtf_cds_regions = collect_gtf_cds_regions(transcript.strand, cds_regions)
    assert len(gtf_cds_regions) == 3

    assert [(r.start, r.stop) for r in gtf_cds_regions] == [
        (155802903, 155803726),
        (155806296, 155806557),
        (155811823, 155812122),
    ]

    frame = calc_frame_for_gtf_cds_feature(transcript, start_codons[0])
    assert frame == 0

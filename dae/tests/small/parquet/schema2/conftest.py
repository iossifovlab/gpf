from typing import Any

import pytest

from dae.variants.variant import SummaryVariant, SummaryVariantFactory

SUMMARY_SCHEMA = {
    "bucket_index": "int32",
    "summary_index": "int32",
    "allele_index": "int32",
    "allele_count": "int32",
    "sj_index": "int64",
    "chrom": "string",
    "position": "int32",
    "end_position": "int32",
    "reference": "string",
    "alternative": "string",
    "cshl_position": "int32",
    "cshl_variant": "string",
    "variant_type": "int8",
    "transmission_type": "int8",
    "effects": "string",
    "hw": "float",
    "af_allele_count": "int32",
    "af_allele_freq": "float",
    "af_parents_called_count": "int32",
    "af_parents_called_percent": "float",
    "seen_as_denovo": "bool",
    "seen_in_status": "int8",
    "family_variants_count": "int32",
    "family_alleles_count": "int32",
    "summary_variant_data": "string",
    "phylop100way": "float",
    "phylop30way": "float",
    "phylop20way": "float",
    "phylop7way": "float",
    "phastcons100way": "float",
    "phastcons30way": "float",
    "phastcons20way": "float",
    "phastcons7way": "float",
    "cadd_raw": "float",
    "cadd_phred": "float",
    "fitcons_i6_merged": "float",
    "linsight": "float",
    "fitcons2_e067": "float",
    "fitcons2_e068": "float",
    "fitcons2_e069": "float",
    "fitcons2_e070": "float",
    "fitcons2_e071": "float",
    "fitcons2_e072": "float",
    "fitcons2_e073": "float",
    "fitcons2_e074": "float",
    "fitcons2_e081": "float",
    "fitcons2_e082": "float",
    "mpc": "float",
    "ssc_freq": "float",
    "exome_gnomad_v2_1_1_af_percent": "float",
    "exome_gnomad_v2_1_1_ac": "int32",
    "exome_gnomad_v2_1_1_af": "float",
    "exome_gnomad_v2_1_1_an": "int32",
    "exome_gnomad_v2_1_1_controls_ac": "int32",
    "exome_gnomad_v2_1_1_controls_an": "int32",
    "exome_gnomad_v2_1_1_non_neuro_ac": "int32",
    "exome_gnomad_v2_1_1_non_neuro_an": "int32",
    "exome_gnomad_v2_1_1_controls_af_percent": "float",
    "exome_gnomad_v2_1_1_non_neuro_af_percent": "float",
    "genome_gnomad_v2_1_1_af_percent": "float",
    "genome_gnomad_v2_1_1_ac": "int32",
    "genome_gnomad_v2_1_1_af": "float",
    "genome_gnomad_v2_1_1_an": "int32",
    "genome_gnomad_v2_1_1_controls_ac": "int32",
    "genome_gnomad_v2_1_1_controls_an": "int32",
    "genome_gnomad_v2_1_1_non_neuro_ac": "int32",
    "genome_gnomad_v2_1_1_non_neuro_an": "int32",
    "genome_gnomad_v2_1_1_controls_af_percent": "float",
    "genome_gnomad_v2_1_1_non_neuro_af_percent": "float",
    "genome_gnomad_v3_af_percent": "float",
    "genome_gnomad_v3_ac": "int32",
    "genome_gnomad_v3_an": "int32",
    "region_bin": "string",
    "frequency_bin": "int8",
    "coding_bin": "int8",
}


@pytest.fixture
def sv1_records() -> list[dict[str, Any]]:
    return [{
        "af_allele_count": 137,
        "af_allele_freq": 4.07,
        "af_parents_called_count": 1684,
        "af_parents_called_percent": 98.02,
        "allele_count": 2,
        "allele_index": 1,
        "alternative": "T",
        "bucket_index": 200042,
        "cadd_phred": 1.336142857142857,
        "cadd_raw": -0.03555357142857143,
        "chrom": "chr1",
        "cshl_position": 213094430,
        "cshl_variant": "del(5)",
        "effects": "intron!"
        "RPS6KC1:intron|"
        "RPS6KC1:5'UTR-intron|"
        "RPS6KC1:non-coding-intron!"
        "NM_001136138_1:RPS6KC1:intron:2/13[10019]|"
        "NM_001287218_1:RPS6KC1:5'UTR-intron:3/14[10019]|"
        "NM_001287219_1:RPS6KC1:5'UTR-intron:4/14[10019]|"
        "NM_001287220_1:RPS6KC1:5'UTR-intron:3/12[10019]|"
        "NM_001287221_1:RPS6KC1:5'UTR-intron:2/13[10019]|"
        "NM_001349646_1:RPS6KC1:intron:3/13[10019]|"
        "NM_001349647_1:RPS6KC1:intron:3/13[10019]|"
        "NM_001349648_1:RPS6KC1:5'UTR-intron:4/15[6399]|"
        "NM_001349649_1:RPS6KC1:5'UTR-intron:4/15[10019]|"
        "NM_001349650_1:RPS6KC1:5'UTR-intron:4/16[10019]|"
        "NM_001349651_1:RPS6KC1:5'UTR-intron:4/17[10019]|"
        "NM_001349652_1:RPS6KC1:5'UTR-intron:3/16[10019]|"
        "NM_001349653_1:RPS6KC1:5'UTR-intron:3/15[10019]|"
        "NM_001349654_1:RPS6KC1:5'UTR-intron:4/15[10019]|"
        "NM_001349657_1:RPS6KC1:5'UTR-intron:3/12[10019]|"
        "NM_001349658_1:RPS6KC1:5'UTR-intron:4/14[10019]|"
        "NM_001349659_1:RPS6KC1:5'UTR-intron:3/16[10019]|"
        "NM_001349660_1:RPS6KC1:5'UTR-intron:4/17[10019]|"
        "NM_001349661_1:RPS6KC1:5'UTR-intron:2/14[10019]|"
        "NM_001349662_1:RPS6KC1:5'UTR-intron:3/15[10019]|"
        "NM_001349663_1:RPS6KC1:5'UTR-intron:3/9[10019]|"
        "NM_001349664_1:RPS6KC1:5'UTR-intron:4/12[10019]|"
        "NM_001349665_1:RPS6KC1:5'UTR-intron:2/10[10019]|"
        "NM_001349666_1:RPS6KC1:5'UTR-intron:4/13[10019]|"
        "NM_001349667_1:RPS6KC1:5'UTR-intron:2/11[10019]|"
        "NM_001349668_1:RPS6KC1:5'UTR-intron:3/13[10019]|"
        "NM_001349669_1:RPS6KC1:5'UTR-intron:4/14[10019]|"
        "NM_001349670_1:RPS6KC1:5'UTR-intron:3/11[10019]|"
        "NM_001349671_1:RPS6KC1:5'UTR-intron:4/12[6399]|"
        "NM_001349672_1:RPS6KC1:5'UTR-intron:2/10[10019]|"
        "NM_012424_1:RPS6KC1:intron:3/14[10019]|"
        "NR_146207_1:RPS6KC1:non-coding-intron:None/None[None]|"
        "NR_146208_1:RPS6KC1:non-coding-intron:None/None[None]|"
        "NR_146209_1:RPS6KC1:non-coding-intron:None/None[None]|"
        "NR_146210_1:RPS6KC1:non-coding-intron:None/None[None]",
        "end_position": 213094434,
        "exome_gnomad_v2_1_1_ac": None,
        "exome_gnomad_v2_1_1_af": None,
        "exome_gnomad_v2_1_1_af_percent": None,
        "exome_gnomad_v2_1_1_an": None,
        "exome_gnomad_v2_1_1_controls_ac": None,
        "exome_gnomad_v2_1_1_controls_af_percent": None,
        "exome_gnomad_v2_1_1_controls_an": None,
        "exome_gnomad_v2_1_1_non_neuro_ac": None,
        "exome_gnomad_v2_1_1_non_neuro_af_percent": None,
        "exome_gnomad_v2_1_1_non_neuro_an": None,
        "family_alleles_count": 134,
        "family_variants_count": 134,
        "fitcons2_e067": 0.132653,
        "fitcons2_e068": 0.08748,
        "fitcons2_e069": 0.08748,
        "fitcons2_e070": 0.132653,
        "fitcons2_e071": 0.08143714285714286,
        "fitcons2_e072": 0.08748,
        "fitcons2_e073": 0.08748,
        "fitcons2_e074": 0.08143714285714286,
        "fitcons2_e081": 0.07901999999999999,
        "fitcons2_e082": 0.0943437142857143,
        "fitcons_i6_merged": 0.08850599999999999,
        "genome_gnomad_v2_1_1_ac": 900,
        "genome_gnomad_v2_1_1_af": 0.028766900300979614,
        "genome_gnomad_v2_1_1_af_percent": 2.8766900300979614,
        "genome_gnomad_v2_1_1_an": 31286,
        "genome_gnomad_v2_1_1_controls_ac": 276,
        "genome_gnomad_v2_1_1_controls_af_percent": 2.552719973027706,
        "genome_gnomad_v2_1_1_controls_an": 10812,
        "genome_gnomad_v2_1_1_non_neuro_ac": 713,
        "genome_gnomad_v2_1_1_non_neuro_af_percent": 3.365429863333702,
        "genome_gnomad_v2_1_1_non_neuro_an": 21186,
        "genome_gnomad_v3_ac": 4836,
        "genome_gnomad_v3_af_percent": 3.376759961247444,
        "genome_gnomad_v3_an": 143214,
        "hw": 0.5321,
        "linsight": None,
        "mpc": None,
        "phastcons100way": 0.00028571428571428574,
        "phastcons20way": 0.0032857142857142855,
        "phastcons30way": 0.027571428571428573,
        "phastcons7way": 0.4502857142857143,
        "phylop100way": -0.059285714285714275,
        "phylop20way": -0.05671428571428572,
        "phylop30way": 0.16071428571428573,
        "phylop7way": 0.3985714285714286,
        "position": 213094429,
        "reference": "TTAATC",
        "seen_as_denovo": False,
        "seen_in_status": 3,
        "sj_index": 2000420000763910001,
        "ssc_freq": 4.71,
        "summary_index": 12,
        "transmission_type": 1,
        "variant_type": 4,
    }]


@pytest.fixture
def sv(sv1_records: list[dict[str, Any]]) -> SummaryVariant:
    return SummaryVariantFactory.summary_variant_from_records(sv1_records)


@pytest.fixture
def summary_schema() -> dict[str, str]:
    return SUMMARY_SCHEMA

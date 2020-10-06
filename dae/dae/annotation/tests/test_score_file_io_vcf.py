import os
import logging

from box import Box

from dae.annotation.tools.score_file_io_vcf import VcfInfoAccess
from dae.annotation.tools.score_file_io import ScoreFile
from dae.annotation.tools.vcf_info_annotator import VcfInfoAnnotator
from dae.annotation.tools.annotator_config import AnnotationConfigParser

from dae.pedigrees.loader import FamiliesLoader
from dae.backends.vcf.loader import VcfLoader


logger = logging.getLogger(__name__)


def test_simple(fixture_dirname):

    vcf_filename = fixture_dirname(
        "vcf_scores/gnomad.genomes.r2.1.1.sites.21.1_622.vcf.gz")
    assert os.path.exists(vcf_filename), vcf_filename

    options = Box({
        "score_names": (
            "AC", "AN", "AF", "controls_AC", "controls_AN", "controls_AF", 
            "non_neuro_AC", "non_neuro_AN", "non_neuro_AF", "AF_percent",
            "controls_AF_percent", "non_neuro_AF_percent")
    }, frozen_box=True)

    vcf_access = VcfInfoAccess(options, vcf_filename)

    vcf_access._fetch("21", 1, 9411323)

    vcf_access._cleanup()


def test_vcf_info_score_file(fixture_dirname):

    vcf_filename = fixture_dirname(
        "vcf_scores/gnomad.genomes.r2.1.1.sites.21.1_622.vcf.gz")
    assert os.path.exists(vcf_filename), vcf_filename

    score_file = ScoreFile(vcf_filename)
    assert score_file is not None

    assert score_file.chr_name == "CHROM"
    assert score_file.pos_begin_name == "POS"
    logger.debug(score_file.score_names)
    assert "AF_percent" in score_file.score_names
    assert "AF" in score_file.score_names

    res = score_file.fetch_scores("21", 9411296, 9411296)
    print(res)
    assert len(res["CHROM"]) == 2


def test_vcf_info_annotator(fixture_dirname, genomes_db_2013):
    score_filename = fixture_dirname(
        "vcf_scores/gnomad.genomes.r2.1.1.sites.21.1_622.vcf.gz")

    columns = {
        "AC": "genome_gnomad_ac",
        "AF": "genome_gnomad_af",
        "AF_percent": "genome_gnomad_af_percent",
    }

    options = {
        "vcf": True,
        "c": "chrom",
        "p": "position",
        "r": "reference",
        "a": "alternative",
        "scores_file": score_filename,
    }

    config = AnnotationConfigParser.parse_section({
            "options": options,
            "columns": columns,
            "annotator": "vcf_info_annotator.VcfInfoAnnotator",
            "virtual_columns": [],
        }
    )

    annotator = VcfInfoAnnotator(config, genomes_db_2013)
    assert annotator is not None

    vcf_filename = fixture_dirname(
        "vcf_scores/gnomad.genomes.r2.1.1.sites.21.trio.vcf.gz")
    pedigree_filename = fixture_dirname(
        "vcf_scores/trio.ped")
    assert os.path.exists(vcf_filename)
    assert os.path.exists(pedigree_filename)

    families_loader = FamiliesLoader(pedigree_filename)
    families = families_loader.load()

    loader = VcfLoader(
        families,
        [vcf_filename],
        genomes_db_2013.get_genome())
    assert loader is not None

    for summary_variant, _ in loader.full_variants_iterator():
        annotator.annotate_summary_variant(summary_variant)

        for aa in summary_variant.alt_alleles:
            af = aa.get_attribute("genome_gnomad_af_percent")
            logger.debug(f"summary variant: {aa}; gnomad AF {af}%")
            assert af is not None

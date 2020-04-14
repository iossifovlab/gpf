import numpy as np

from dae.backends.cnv.loader import CNVLoader
from dae.pedigrees.loader import FamiliesLoader

from .conftest import relative_to_this_test_folder

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.score_annotator import NPScoreAnnotator


def test_cnv_variant_score_annotation(fixture_dirname, genomes_db_2013):
    options = GPFConfigParser._dict_to_namedtuple(
        {
            "vcf": False,
            "x": "location",
            "v": "variant",
            "mode": "overwrite",
            "scores_file": relative_to_this_test_folder(
                "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz"
            ),
        }
    )

    columns = {
        "TESTphastCons100way": "RESULT_phastCons100way",
    }

    config = AnnotationConfigParser.parse_section(
        GPFConfigParser._dict_to_namedtuple(
            {
                "options": options,
                "columns": columns,
                "annotator": "score_annotator.VariantScoreAnnotator",
                "virtual_columns": [],
            }
        )
    )

    score_annotator = NPScoreAnnotator(config, genomes_db_2013)
    assert score_annotator is not None

    families_file = fixture_dirname("backends/cnv_ped.txt")
    families = FamiliesLoader.load_simple_families_file(families_file)
    assert families is not None
    variants_file = fixture_dirname("annotation_pipeline/cnv_annotation_variants.txt")

    loader = CNVLoader(families, variants_file, genomes_db_2013.get_genome())
    assert loader is not None

    result = []
    for sv, _ in loader.full_variants_iterator():
        score_annotator.annotate_summary_variant(sv)
        result.append(sv.alt_alleles[0].attributes["RESULT_phastCons100way"])

    assert np.allclose(result, [0.253, 0.24, 0.253, 0.014])

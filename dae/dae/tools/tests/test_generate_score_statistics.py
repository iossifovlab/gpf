import os
from dae.tools.generate_score_statistics import main


def test_generate_position_score_statistics(
    fixture_dirname, temp_dirname_scores
):
    args = [
        "hg38/TESTphastCons100way",
        "--repository-path", fixture_dirname("genomic_resources"),
        "--output-dir", temp_dirname_scores
    ]
    main(args)
    assert os.path.exists(
        os.path.join(temp_dirname_scores, "phastCons100way.yaml")
    )

# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import textwrap

import pytest

from dae.testing import convert_to_tab_separated, setup_directories, \
    setup_genome, setup_empty_gene_models, setup_gpf_instance
from dae.genomic_resources.testing import build_inmemory_test_repository

from dae.annotation.annotate_columns import cli as cli_columns
from dae.genomic_resources.genomic_context import register_context
from dae.gpf_instance_plugin.gpf_instance_context_plugin import \
    GPFInstanceGenomicContext


def get_file_content_as_string(file):
    with open(file, "rt", encoding="utf8") as infile:
        return "".join(infile.readlines())


@pytest.fixture
def scores_repo(tmp_path):
    repo = build_inmemory_test_repository({
        "one": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: position_score
                table:
                  filename: data.tsv
                scores:
                - id: score
                  type: float
                  desc: |
                      The phastCons computed over the tree of 100
                      verterbarte species
                  name: s1
            """),

            "data.tsv": convert_to_tab_separated("""
                    chrom  pos_begin  s1
                    chrA   10         0.01
                    chrA   11         0.2
                """)
        }
    })
    return repo


@pytest.fixture
def annotation_gpf(scores_repo, tmp_path_factory):
    root_path = tmp_path_factory.mktemp("genomic_scores_db_gpf")

    setup_directories(root_path / "gpf_instance", {
        "gpf_instance.yaml": textwrap.dedent("""
        annotation:
            conf_file: annotation.yaml
        """),
        "annotation.yaml": textwrap.dedent("""
        - position_score: one
        """)
    })
    genome = setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )
    empty_gene_models = setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=empty_gene_models,
        grr=scores_repo
    )
    register_context(GPFInstanceGenomicContext(gpf_instance))
    return gpf_instance


def test_basic_setup(tmp_path, annotation_gpf, capsys):
    # Given
    in_content = convert_to_tab_separated("""
            location  variant
            chrA:10   sub(A->C)
            chrA:11   sub(A->T)
        """)

    setup_directories(tmp_path, {
        "in.txt": in_content,
    })
    in_file = tmp_path / "in.txt"
    annotation_file = os.path.join(annotation_gpf.dae_dir, "annotation.yaml")

    # When
    cli_columns([
        str(a) for a in [
            in_file, annotation_file
        ]
    ])

    # Then
    out, _err = capsys.readouterr()
    assert out == convert_to_tab_separated("""
            location  variant   score
            chrA:10   sub(A->C) 0.01
            chrA:11   sub(A->T) 0.2
        """)

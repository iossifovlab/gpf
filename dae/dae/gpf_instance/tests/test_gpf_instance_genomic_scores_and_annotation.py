# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pytest

from dae.testing import setup_gpf_instance, setup_genome, \
    setup_empty_gene_models, setup_directories


@pytest.fixture
def gpf_fixture(tmp_path_factory):
    def builder(instance_config):
        root_path = tmp_path_factory.mktemp("genomic_scores_db")

        genome = setup_genome(
            root_path / "alla_gpf" / "genome" / "allChr.fa",
            f"""
            >chrA
            {100 * "A"}
            """
        )
        empty_gene_models = setup_empty_gene_models(
            root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
        setup_directories(
            root_path / "gpf_instance",
            instance_config
        )
        return setup_gpf_instance(
            root_path / "gpf_instance",
            reference_genome=genome,
            gene_models=empty_gene_models,
        )

    return builder


def test_genomic_scores_db_with_config(gpf_fixture):
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
            genomic_scores_db:
            - resource: hg19/scores/MPC
              score: mpc
            annotation:
              conf_file: annotation.yaml
        """),
        "annotation.yaml": textwrap.dedent("""
            - np_score: hg19/scores/MPC
        """)
    })
    assert len(gpf_instance.genomic_scores_db) == 1


def test_genomic_scores_db_without_config_with_annotation(gpf_fixture):
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
            annotation:
              conf_file: annotation.yaml
        """),
        "annotation.yaml": textwrap.dedent("""
            - np_score: hg19/scores/MPC
        """)
    })
    assert len(gpf_instance.genomic_scores_db) == 1


def test_genomic_scores_db_without_config_without_annotation(gpf_fixture):
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
        """),
    })
    assert len(gpf_instance.genomic_scores_db) == 0


def test_annotation_pipeline_with_config(gpf_fixture):
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
            annotation:
              conf_file: annotation.yaml
        """),
        "annotation.yaml": textwrap.dedent("""
            - np_score: hg19/scores/MPC
        """)
    })
    assert gpf_instance.get_annotation_pipeline() is not None
    assert len(gpf_instance.get_annotation_pipeline().annotators) == 1


def test_annotation_pipeline_without_config(gpf_fixture):
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
        """),
    })
    assert gpf_instance.get_annotation_pipeline() is not None
    assert len(gpf_instance.get_annotation_pipeline().annotators) == 0


def test_annotation_pipeline_with_bad_config(gpf_fixture):
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
            annotation:
              conf_file: annotation.yaml
        """),
    })
    with pytest.raises(
            ValueError,
            match="missing annotaiton config file"):
        gpf_instance.get_annotation_pipeline()

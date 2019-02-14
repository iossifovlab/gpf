import os
import pytest

from configurable_entities.configuration import ConfigSectionDefinition, \
    AnnotatorDefinition, DAEConfig


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture
def fixturedir():
    return relative_to_this_test_folder("fixtures")


@pytest.fixture
def dae_config(fixturedir):
    filename = "dae_test.conf"
    config = DAEConfig(dae_data_dir=fixturedir, dae_conf_filename=filename)
    return config


def test_configuration_sections_simple(fixturedir):
    definitions = ConfigSectionDefinition(
        "test_config.conf", work_dir=fixturedir
    )
    assert definitions is not None

    genomes_config = definitions.get_section_config("genomes")
    assert genomes_config is not None

    assert genomes_config.conf_file is not None
    assert "genomes.conf" in genomes_config.conf_file

    assert genomes_config.confFile is not None
    assert "genomes.conf" in genomes_config.confFile

    gene_info = definitions.get_section_config("geneInfo")
    assert gene_info is not None

    assert gene_info.conf_file is not None
    assert "geneInfo.conf" in gene_info.conf_file


def test_annotation_config_simple(fixturedir):

    annotators = AnnotatorDefinition(
        "annotation.conf", work_dir=fixturedir
    )
    assert annotators is not None
    print(annotators.get_all_annotator_configs())


def test_dae_config_simple(fixturedir, dae_config):
    assert dae_config is not None

    assert dae_config.dae_data_dir == fixturedir

    assert dae_config.pheno_section() is not None
    print(dae_config.pheno_section())

    assert dae_config.pheno_dir == os.path.join(fixturedir, "pheno")
    assert dae_config.pheno_conf == os.path.join(fixturedir, "phenoDB.conf")

    assert dae_config.gene_info_dir == os.path.join(fixturedir, "geneInfo")
    assert dae_config.gene_info_conf == \
        os.path.join(fixturedir, "geneInfoDB.conf")

    assert dae_config.genomes_dir == \
        os.path.join(fixturedir, "genomes")
    assert dae_config.genomes_conf == \
        os.path.join(fixturedir, "genomesDB.conf")

    assert dae_config.genomic_scores_dir == \
        os.path.join(fixturedir, "genomicScores")
    assert dae_config.genomic_scores_conf == \
        os.path.join(fixturedir, "genomicScores.conf")

    assert dae_config.common_reports_dir == \
        os.path.join(fixturedir, "commonReports")
    assert dae_config.common_reports_conf == \
        os.path.join(fixturedir, "commonReports.conf")


def test_dae_config_genomic_scores_dirs(dae_config):

    assert dae_config.genomic_scores_hg19_dir is not None
    assert os.path.exists(dae_config.genomic_scores_hg19_dir)
    assert os.path.isdir(dae_config.genomic_scores_hg19_dir)

    assert dae_config.genomic_scores_hg38_dir is not None
    assert os.path.exists(dae_config.genomic_scores_hg38_dir)
    assert os.path.isdir(dae_config.genomic_scores_hg38_dir)


def test_dae_config_annotation_defaults(fixturedir, dae_config):
    defaults = dae_config.annotation_defaults
    assert defaults is not None

    assert defaults['wd'] == fixturedir
    assert defaults['data_dir'] == fixturedir
    assert defaults['scores_hg19_dir'] == \
        os.path.join(fixturedir, 'genomic_scores_db')
    assert defaults['scores_hg38_dir'] == \
        os.path.join(fixturedir, 'genomic_scores_db')

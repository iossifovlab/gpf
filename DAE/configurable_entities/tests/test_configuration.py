import os
from configurable_entities.configuration import ConfigSectionDefinition, \
    AnnotatorDefinition, DAEConfig


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


def test_configuration_sections_simple():
    dirname = relative_to_this_test_folder("fixtures/")
    definitions = ConfigSectionDefinition(
        "test_config.conf", work_dir=dirname
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


def test_annotation_config_simple():

    dirname = relative_to_this_test_folder("fixtures")
    annotators = AnnotatorDefinition(
        "annotation.conf", work_dir=dirname
    )
    assert annotators is not None
    print(annotators.get_all_annotator_configs())


def test_dae_config_simple():
    dirname = relative_to_this_test_folder("fixtures")
    filename = "dae_test.conf"
    dae_config = DAEConfig(dae_data_dir=dirname, dae_conf_filename=filename)
    assert dae_config is not None

    assert dae_config.dae_data_dir == dirname

    assert dae_config.pheno_section() is not None
    print(dae_config.pheno_section())

    assert dae_config.pheno_dir == os.path.join(dirname, "pheno")
    assert dae_config.pheno_conf == os.path.join(dirname, "phenoDB.conf")

    assert dae_config.gene_info_dir == os.path.join(dirname, "geneInfo")
    assert dae_config.gene_info_conf == \
        os.path.join(dirname, "geneInfoDB.conf")

    assert dae_config.genomes_dir == \
        os.path.join(dirname, "genomes")
    assert dae_config.genomes_conf == \
        os.path.join(dirname, "genomesDB.conf")

    assert dae_config.genomic_scores_dir == \
        os.path.join(dirname, "genomicScores")
    assert dae_config.genomic_scores_conf == \
        os.path.join(dirname, "genomicScores.conf")

    assert dae_config.common_reports_dir == \
        os.path.join(dirname, "commonReports")
    assert dae_config.common_reports_conf == \
        os.path.join(dirname, "commonReports.conf")

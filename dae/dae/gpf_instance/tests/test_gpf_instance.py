# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import textwrap

import pytest
from utils.testing import setup_t4c8_grr

from dae.genomic_resources.testing import setup_directories
from dae.gpf_instance import GPFInstance
from dae.testing.setup_helpers import setup_gpf_instance


def test_init(t4c8_instance: GPFInstance) -> None:
    assert t4c8_instance

    assert t4c8_instance.dae_config
    assert t4c8_instance.reference_genome
    assert t4c8_instance.gene_models
    assert t4c8_instance._pheno_registry
    assert t4c8_instance.gene_scores_db
    assert t4c8_instance.genomic_scores is not None
    assert t4c8_instance._variants_db
    assert t4c8_instance.gene_sets_db is not None
    assert t4c8_instance.denovo_gene_sets_db is not None


def test_eager_init(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    root_path = tmp_path_factory.mktemp("sample_t4c8_instance_for_test")
    instance_path = root_path / "gpf_instance"
    t4c8_grr = setup_t4c8_grr(root_path)
    setup_directories(
        instance_path, {
            "gpf_instance.yaml": textwrap.dedent("""
                instance_id: t4c8_instance
                annotation:
                  conf_file: annotation.yaml
                reference_genome:
                  resource_id: t4c8_genome
                gene_models:
                  resource_id: t4c8_genes
                gene_scores_db:
                  gene_scores:
                  - "gene_scores/t4c8_score"
                gene_sets_db:
                  gene_set_collections:
                  - gene_sets/main
            """),
            "annotation.yaml": textwrap.dedent("""
               - position_score: genomic_scores/score_one
            """),
        },
    )
    instance = setup_gpf_instance(instance_path, grr=t4c8_grr)
    instance.load()

    assert instance

    assert instance.dae_config
    assert instance.reference_genome
    assert instance.gene_models
    assert instance._pheno_registry
    assert instance.gene_scores_db is not None
    assert instance.genomic_scores
    assert instance._variants_db
    assert instance.gene_sets_db
    assert instance.denovo_gene_sets_db is not None


def test_dae_config(tmp_path_factory: pytest.TempPathFactory) -> None:
    root_path = tmp_path_factory.mktemp("sample_t4c8_instance_for_test")
    instance = setup_gpf_instance(root_path)
    assert instance.dae_config.conf_dir == str(root_path)


def test_variants_db(t4c8_instance: GPFInstance) -> None:
    variants_db = t4c8_instance._variants_db
    assert len(variants_db.get_all_genotype_data()) == 4

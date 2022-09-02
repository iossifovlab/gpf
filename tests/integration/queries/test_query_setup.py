# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest
import pysam

from dae.import_tools.import_tools import ImportProject, run_with_project
from dae.genomic_resources import build_genomic_resource_repository

from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_file
from dae.genomic_resources.gene_models import build_gene_models_from_file

from dae.genomic_resources.testing import convert_to_tab_separated, \
    setup_directories

from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.variant import Variant

from dae.gpf_instance import GPFInstance


@pytest.fixture
def minimal_reference_genome(tmp_path):
    content = {
        "grr": {
            "ref_genome": {
                "chrAll.fa": convert_to_tab_separated("""
                        >foo
                        NNACCCAAAC
                        GGGCCTTCCN
                        NNNA
                        >bar
                        NNGGGCCTTC
                        CACGACCCAA
                        NN
                """),
                "chrAll.fa.fai": convert_to_tab_separated("""
                    foo  24  5  10  11
                    bar  22  36 10  11
                """),
                "genomic_resource.yaml": textwrap.dedent("""
                    type: genome
                    filename: chrAll.fa
                """)
            }
        }
    }
    setup_directories(tmp_path, content)
    ref = build_reference_genome_from_file(
        tmp_path / "grr" / "ref_genome" / "chrAll.fa")

    ref.open()
    return ref


# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
g1        tx1  foo   +      3       15    3        13     2         3,7        6,13
g1        tx2  foo   +      3       9     3        6      1         3          6
g2        tx3  bar   -      10      20    12       18     1         12         18
"""  # noqa


@pytest.fixture
def minimal_gene_models(tmp_path):
    content = {
        "grr": {
            "gene_models": {
                "genes.txt": convert_to_tab_separated(GMM_CONTENT),
                "genomic_resource.yaml": textwrap.dedent("""
                    type: gene_models
                    filename: genes.txt
                """)
            }
        }
    }
    setup_directories(tmp_path, content)
    gene_models = build_gene_models_from_file(
        tmp_path / "grr" / "gene_models" / "genes.txt")
    gene_models.load()
    return gene_models


def test_minimal_reference_genome(minimal_reference_genome):
    ref = minimal_reference_genome
    assert ref.get_chrom_length("foo") == 24
    assert ref.get_sequence("foo", 1, 12) == "NNACCCAAACGG"

    assert ref.get_chrom_length("bar") == 22
    assert ref.get_sequence("bar", 1, 12) == "NNGGGCCTTCCA"


def test_minimal_gene_models(minimal_gene_models):

    assert set(minimal_gene_models.gene_names()) == {"g1", "g2"}
    assert len(minimal_gene_models.transcript_models) == 3


@pytest.mark.parametrize("loc,ref,alt,ecount,etypes", [
    ("foo:10", "C", "G", 1, {"missense"}),
    ("foo:9", "A", "C", 1, {"missense"}),
    ("foo:7", "A", "C", 1, {"splice-site"}),
    ("foo:4", "C", "G", 2, {"noStart"})
])
def test_minimal_effect_annotator(
        minimal_reference_genome, minimal_gene_models,
        loc, ref, alt, ecount, etypes):

    annotator = EffectAnnotator(minimal_reference_genome, minimal_gene_models)
    variant = Variant(loc=loc, ref=ref, alt=alt)
    effects = annotator.annotate(variant)
    assert len(effects) == ecount
    assert {eff.effect for eff in effects} == etypes


@pytest.fixture
def minimal_grr(tmp_path, minimal_reference_genome, minimal_gene_models):
    grr = build_genomic_resource_repository({
        "id": "minimal",
        "type": "file",
        "directory": str(tmp_path / "grr")
    })
    return grr


def test_minimal_grr(minimal_grr):

    assert minimal_grr.get_resource("gene_models").get_type() == "gene_models"
    assert minimal_grr.get_resource("ref_genome").get_type() == "genome"


@pytest.fixture
def minimal_gpf_instance(
        tmp_path, minimal_grr):
    setup_directories(tmp_path, {
        "gpf_instance": {
            "gpf_instance.yaml": textwrap.dedent(f"""
                grr:
                    id: "minimal"
                    type: "file"
                    directory: {tmp_path / "grr"}

                reference_genome:
                    resource_id: "ref_genome"

                gene_models:
                    resource_id: "gene_models"

                genotype_storage:
                  default: genotype_impala
                storage:
                  genotype_impala:
                    storage_type: impala
                    dir: "work/"
                    hdfs:
                      base_dir: /tmp/test_data
                      host: localhost
                      port: 8020
                      replication: 1
                    impala:
                      db: "test_schema1"
                      hosts:
                      - localhost
                      pool_size: 3
                      port: 21050

                  genotype_impala_2:
                    storage_type: impala
                    dir: "work/"
                    hdfs:
                      base_dir: /tmp/test_data
                      host: localhost
                      port: 8020
                      replication: 1
                    impala:
                      db: "test_schema1"
                      hosts:
                      - localhost
                      pool_size: 3
                      port: 21050
                    schema_version: 2
            """)
        }
    })

    gpf_instance = GPFInstance(
        work_dir=str(tmp_path / "gpf_instance"),
        grr=minimal_grr)

    return gpf_instance


def test_minimal_gpf_instance(minimal_gpf_instance):
    assert minimal_gpf_instance is not None
    grr = minimal_gpf_instance.grr
    assert grr.get_resource("ref_genome").get_type() == "genome"


@pytest.fixture
def minimal_vcf(tmp_path):
    in_vcf = convert_to_tab_separated("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1
        foo    10  .  C   G   .    .      .    GT     0/0 0/1 0/1
        """)

    in_ped = convert_to_tab_separated(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   2      prb
        """)

    setup_directories(tmp_path, {
        "input": {
            "in.vcf": in_vcf,
            "in.ped": in_ped
        }
    })

    # pylint: disable=no-member
    pysam.tabix_compress(
        str(tmp_path / "input" / "in.vcf"),
        str(tmp_path / "input" / "in.vcf.gz"))
    pysam.tabix_index(
        str(tmp_path / "input" / "in.vcf.gz"), preset="vcf")


def test_minimal_vcf(tmp_path, minimal_reference_genome, minimal_vcf):

    assert (tmp_path / "grr" / "ref_genome" / "chrAll.fa").exists()
    assert (tmp_path / "input" / "in.vcf.gz").exists()
    assert (tmp_path / "input" / "in.vcf.gz.tbi").exists()
    assert (tmp_path / "input" / "in.ped").exists()


@pytest.fixture
def minimal_project(tmp_path, minimal_gpf_instance, minimal_vcf):
    def build(storage_id):
        config = textwrap.dedent(f"""
            id: minimal_vcf
            processing_config:
              work_dir: {tmp_path / "work"}
            input:
              pedigree:
                file: in.ped
              vcf:
                files:
                 - in.vcf.gz
                denovo_mode: ignore
                omission_mode: ignore
            gpf_instance:
              path: {tmp_path / "gpf_instance"}
            destination:
              storage_id: {storage_id}
            """)
        setup_directories(tmp_path, {
            "input": {
                "import_project.yaml": config
            },
        })
        project = ImportProject.build_from_file(
            tmp_path / "input" / "import_project.yaml")
        return project
    return build


@pytest.mark.parametrize("storage_id", [
    "genotype_impala",
    "genotype_impala_2",
])
def test_minimal_project(tmp_path, minimal_project, storage_id):

    project: ImportProject = minimal_project(storage_id)
    assert project is not None
    assert project.get_genotype_storage().storage_id == storage_id

    run_with_project(project)
    print(project.stats)

    assert (tmp_path / "gpf_instance/studies/minimal_vcf/minimal_vcf.conf")\
        .exists()

    gpf_instance: GPFInstance = project.get_gpf_instance()
    gpf_instance.reload()

    assert gpf_instance.get_genotype_data_ids() == ["minimal_vcf"]

    study = gpf_instance.get_genotype_data("minimal_vcf")
    vs = list(study.query_variants())

    assert len(vs) == 2

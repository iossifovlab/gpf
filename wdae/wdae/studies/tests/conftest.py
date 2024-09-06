# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest

from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing import (
    setup_directories,
    setup_gpf_instance,
    setup_pedigree,
    setup_vcf,
    vcf_study,
)
from dae.testing.t4c8_import import t4c8_genes, t4c8_genome
from studies.study_wrapper import (
    StudyWrapper,
)


@pytest.fixture(scope="module")
def t4c8_grr(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceRepo:
    repo_path = tmp_path_factory.mktemp("t4c8_grr")
    t4c8_genome(repo_path)
    t4c8_genes(repo_path)

    setup_directories(
        repo_path / "gene_scores" / "t4c8_score",
        {
            GR_CONF_FILE_NAME:
            """
                type: gene_score
                filename: t4c8_gene_score.csv
                scores:
                - id: t4c8_score
                  desc: t4c8 gene score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "t4c8_gene_score.csv": textwrap.dedent("""
                gene,t4c8_score
                t4,10.123456789
                c8,20.0
            """),
        },
    )
    return build_genomic_resource_repository({
        "id": "t4c8_local",
        "type": "directory",
        "directory": str(repo_path),
    })


@pytest.fixture(scope="module")
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
    t4c8_grr: GenomicResourceRepo,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_wgpf_instance")
    instance_path = root_path / "gpf_instance"

    _t4c8_default_study_config(instance_path)

    setup_directories(
        instance_path, {
            "gpf_instance.yaml": textwrap.dedent("""
                instance_id: test_instance
                gene_scores_db:
                    gene_scores:
                    - "gene_scores/t4c8_score"
                default_study_config:
                  conf_file: default_study_configuration.yaml

            """),
        },
    )

    gpf_instance = setup_gpf_instance(
        instance_path,
        reference_genome_id="t4c8_genome",
        gene_models_id="t4c8_genes",
        grr=t4c8_grr,
    )

    storage_path = root_path / "duckdb_storage"
    storage_config = {
        "id": "duckdb_wgpf_test",
        "storage_type": "duckdb_parquet",
        "base_dir": str(storage_path),
    }
    gpf_instance.genotype_storages.register_storage_config(storage_config)
    _t4c8_study_1(gpf_instance)

    gpf_instance.reload()

    return gpf_instance


def _t4c8_study_1(
    t4c8_instance: GPFInstance,
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "t4c8_study_1" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role phenotype
f1.1     mom1     0     0     2   1      mom  unaffected
f1.1     dad1     0     0     1   1      dad  unaffected
f1.1     p1       dad1  mom1  2   2      prb  autism
f1.1     s1       dad1  mom1  1   1      sib  unaffected
f1.3     mom3     0     0     2   1      mom  unaffected
f1.3     dad3     0     0     1   1      dad  unaffected
f1.3     p3       dad3  mom3  2   2      prb  autism
f1.3     s3       dad3  mom3  2   1      sib  unaffected
        """)
    vcf_path1 = setup_vcf(
        root_path / "t4c8_study_1" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT mom1 dad1 p1  s1  mom3 dad3 p3  s3
chr1   4   .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/0 0/1  0/2  0/2 0/0
chr1   54  .  T   C    .    .      .    GT     0/1  0/1  0/1 0/1 0/0  0/0  0/1 0/1
chr1   90  .  G   C,GA .    .      .    GT     0/1  0/2  0/2 0/2 0/1  0/2  0/1 0/2
chr1   100 .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/0 0/2  0/0  0/0 0/0
chr1   119 .  A   G,C  .    .      .    GT     0/0  0/0  0/2 0/2 0/1  0/2  0/1 0/2
chr1   122 .  A   C,AC .    .      .    GT     0/1  0/1  0/1 0/1 0/2  0/2  0/2 0/1
        """)  # noqa: E501

    vcf_study(
        root_path,
        "t4c8_study_1", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update={
            "input": {
                "vcf": {
                    "denovo_mode": "denovo",
                    "omission_mode": "omission",
                },
            },
        },
    )


@pytest.fixture(scope="module")
def t4c8_study_1(t4c8_instance: GPFInstance) -> GenotypeData:
    return t4c8_instance.get_genotype_data("t4c8_study_1")


@pytest.fixture(scope="module")
def t4c8_study_1_wrapper(
    t4c8_instance: GPFInstance,
) -> StudyWrapper:

    data_study = t4c8_instance.get_genotype_data("t4c8_study_1")

    return StudyWrapper(
        data_study,
        t4c8_instance._pheno_registry,  # noqa: SLF001
        t4c8_instance.gene_scores_db,
        t4c8_instance,
    )


def _t4c8_default_study_config(instance_path: pathlib.Path) -> None:
    setup_directories(
        instance_path, {
            "default_study_configuration.yaml": textwrap.dedent("""
phenotype_browser: false
phenotype_tool: false
study_type:
- WE
study_phenotype: autism
has_transmitted: true
has_denovo: true
has_complex: true
has_cnv: false
genome: hg38
chr_prefix: true

person_set_collections:
  selected_person_set_collections:
  - phenotype
  phenotype:
    id: phenotype
    name: Phenotype
    sources:
    - from: pedigree
      source: status
    domain:
    - id: autism
      name: autism
      values:
      - affected
      color: '#ff2121'
    - id: unaffected
      name: unaffected
      values:
      - unaffected
      color: '#ffffff'
    default:
      id: unspecified
      name: unspecified
      values:
      - unspecified
      color: '#aaaaaa'
genotype_browser:
  enabled: true
  has_family_filters: true
  has_person_filters: true
  has_study_filters: false
  has_present_in_child: true
  has_present_in_parent: true
  has_pedigree_selector: true
  preview_columns:
  - family
  - variant
  - genotype
  - effect
  - gene_scores
  - phylop
  - freq
  download_columns:
  - family
  - study_phenotype
  - variant
  - variant_extra
  - family_person_ids
  - family_structure
  - best
  - family_genotype
  - carriers
  - inheritance
  - phenotypes
  - par_called
  - allele_freq
  - effect
  - geneeffect
  - effectdetails
  - gene_scores

  summary_preview_columns:
  - variant
  - seen_as_denovo
  - seen_in_affected
  - seen_in_unaffected
  - par_called
  - allele_freq
  - effect
  - count
  - geneeffect
  - effectdetails
  - gene_scores
  summary_download_columns:
  - variant
  - seen_as_denovo
  - seen_in_affected
  - seen_in_unaffected
  - par_called
  - allele_freq
  - effect
  - count
  - geneeffect
  - effectdetails
  - gene_scores
  column_groups:
    genotype:
      name: genotype
      columns:
      - pedigree
      - carrier_person_attributes
      - family_person_attributes
    effect:
      name: effect
      columns:
      - worst_effect
      - genes
    gene_scores:
      name: vulnerability/intolerance
      columns:
      - t4c8_score
    family:
      name: family
      columns:
      - family_id
      - study
    variant:
      name: variant
      columns:
      - location
      - variant
    variant_extra:
      name: variant
      columns:
      - chrom
      - position
      - reference
      - alternative
    carriers:
      name: carriers
      columns:
      - carrier_person_ids
      - carrier_person_attributes
    phenotypes:
      name: phenotypes
      columns:
      - family_phenotypes
      - carrier_phenotypes
    freq:
      name: Frequency
      columns:
      - freq_ssc
      - freq_exome_gnomad
      - freq_genome_gnomad
  columns:
    genotype:
      pedigree:
        name: pedigree
        source: pedigree
      worst_effect:
        name: worst effect
        source: worst_effect
      genes:
        name: genes
        source: genes
      t4c8_score:
        name: t4c8 score
        source: t4c8_score
        format: '%%f'
      family_id:
        name: family id
        source: family
      study:
        name: study
        source: study_name
      family_person_ids:
        name: family person ids
        source: family_person_ids
      location:
        name: location
        source: location
      variant:
        name: variant
        source: variant
      chrom:
        name: CHROM
        source: chrom
      position:
        name: POS
        source: position
      reference:
        name: REF
        source: reference
      alternative:
        name: ALT
        source: alternative
      carrier_person_ids:
        name: carrier person ids
        source: carrier_person_ids
      carrier_person_attributes:
        name: carrier person attributes
        source: carrier_person_attributes
      family_person_attributes:
        name: family person attributes
        source: family_person_attributes
      family_phenotypes:
        name: family phenotypes
        source: family_phenotypes
      carrier_phenotypes:
        name: carrier phenotypes
        source: carrier_phenotypes
      inheritance:
        name: inheritance type
        source: inheritance_type
      study_phenotype:
        name: study phenotype
        source: study_phenotype
      best:
        name: family best state
        source: best_st
      family_genotype:
        name: family genotype
        source: genotype
      family_structure:
        name: family structure
        source: family_structure
      geneeffect:
        name: all effects
        source: effects
      effectdetails:
        name: effect details
        source: effect_details
      alt_alleles:
        name: alt alleles
        source: af_allele_count
      par_called:
        name: parents called
        source: af_parents_called_count
      allele_freq:
        name: allele frequency
        source: af_allele_freq
      seen_as_denovo:
        name: seen_as_denovo
        source: seen_as_denovo
      seen_in_affected:
        name: seen_in_affected
        source: seen_in_affected
      seen_in_unaffected:
        name: seen_in_unaffected
        source: seen_in_unaffected

common_report:
  enabled: true
  effect_groups:
  - LGDs
  - nonsynonymous
  - UTRs
  - CNV
  effect_types:
  - Nonsense
  - Frame-shift
  - Splice-site
  - Missense
  - No-frame-shift
  - noStart
  - noEnd
  - Synonymous
  - Non coding
  - Intron
  - Intergenic
  - 3'-UTR
  - 5'-UTR
denovo_gene_sets:
  enabled: true
  selected_person_set_collections:
  - phenotype
  standard_criterias:
    effect_types:
      segments:
        LGDs: LGDs
        Missense: missense
        Synonymous: synonymous
    sexes:
      segments:
        Female: F
        Male: M
        Unspecified: U
  recurrency_criteria:
    segments:
      Single:
          start: 1
          end: 2
      Triple:
          start: 3
          end: -1
      Recurrent:
          start: 2
          end: -1
  gene_sets_names:
  - LGDs
  - LGDs.Male
  - LGDs.Female
  - LGDs.Recurrent
  - LGDs.Single
  - LGDs.Triple
  - Missense
  - Missense.Male
  - Missense.Female
  - Missense.Recurrent
  - Missense.Triple
  - Synonymous
  - Synonymous.Male
  - Synonymous.Female
  - Synonymous.Recurrent
  - Synonymous.Triple
enrichment:
  enabled: false
            """),
        },
    )

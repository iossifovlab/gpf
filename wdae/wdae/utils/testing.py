# pylint: disable=C0116
import pathlib
import textwrap

from gpf_instance.gpf_instance import WGPFInstance

from dae.gene_sets.denovo_gene_set_helpers import DenovoGeneSetHelpers
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pheno.build_pheno_browser import main as build_browser
from dae.pheno.pheno_import import main as pheno_import
from dae.studies.study import GenotypeData
from dae.testing import (
    setup_directories,
    setup_gpf_instance,
    setup_pedigree,
    setup_vcf,
    vcf_study,
)
from dae.testing.import_helpers import setup_dataset_config
from dae.testing.t4c8_import import t4c8_genes, t4c8_genome


def setup_t4c8_grr(
    root_path: pathlib.Path,
) -> GenomicResourceRepo:
    repo_path = root_path / "t4c8_grr"
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
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                meta:
                  description: t4c8 gene score
                """,
            "t4c8_gene_score.csv": textwrap.dedent("""
                gene,t4c8_score
                t4,10.123456789
                c8,20.0
            """),
        },
    )
    setup_directories(
        repo_path / "gene_sets" / "main",
        {
            GR_CONF_FILE_NAME:
            """
                type: gene_set
                id: main
                format: directory
                directory: main_gene_sets
                web_label: Main
                web_format_str: "key| (|count|): |desc"
                meta:
                  description: t4c8 main gene sets
                """,
            "main_gene_sets": {
                "t4_candidates.txt": textwrap.dedent(
                """t4_candidates
                   T4 Candidates
                   t4
                """),
                "c8_candidates.txt": textwrap.dedent(
                """c8_candidates
                   C8 Candidates
                   c8
                """),
                "all_candidates.txt": textwrap.dedent(
                """all_candidates
                   All Candidates
                   t4
                   c8
                """),
            },
        },
    )

    setup_directories(
        repo_path / "genomic_scores" / "score_one",
        {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: position_score
                table:
                  filename: data.txt
                scores:
                - id: score_one
                  type: float
                  name: score
            """),
            "data.txt": textwrap.dedent("""
                chrom\tpos_begin\tscore
                chr1\t4\t0.01
                chr1\t54\t0.02
                chr1\t90\t0.03
                chr1\t100\t0.04
                chr1\t119\t0.05
                chr1\t122\t0.06
            """),
        },
    )

    setup_directories(
      repo_path / "coding_len_background",
      {
        "genomic_resource.yaml": textwrap.dedent("""
            type: gene_score
            filename: coding_len_background.tsv
            separator: "\t"
            scores:
            - id: gene_weight
              name: t4c8CodingLenBackground
              histogram:
                type: number
                number_of_bins: 10
                view_range:
                  min: 0
                  max: 20
            meta:
              description: T4C8 gene coding length enrichment background model
        """),
        "coding_len_background.tsv": "gene\tgene_weight\nT4\t44\nC8\t45",
      },
    )

    cli_manage(["repo-repair", "-R", str(repo_path), "-j", "1"])

    return build_genomic_resource_repository({
        "id": "t4c8_local",
        "type": "directory",
        "directory": str(repo_path),
    })


def setup_t4c8_instance(
    root_path: pathlib.Path,
) -> GPFInstance:
    t4c8_grr = setup_t4c8_grr(root_path)

    instance_path = root_path / "gpf_instance"

    _t4c8_default_study_config(instance_path)

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
                default_study_config:
                  conf_file: default_study_configuration.yaml
                genotype_storage:
                  default: duckdb_wgpf_test
                  storages:
                  - id: duckdb_wgpf_test
                    storage_type: duckdb_parquet
                    memory_limit: 16GB
                    base_dir: '%(wd)s/duckdb_storage'
                gpfjs:
                  visible_datasets:
                  - t4c8_dataset
                  - t4c8_study_1
                  - nonexistend_dataset
            """),
            "annotation.yaml": textwrap.dedent("""
               - position_score: genomic_scores/score_one
            """),
        },
    )

    _study_1_pheno(
        root_path,
        instance_path,
    )

    gpf_instance = setup_gpf_instance(
        instance_path,
        grr=t4c8_grr,
    )

    _t4c8_study_1(root_path, gpf_instance)
    _t4c8_study_2(root_path, gpf_instance)
    _t4c8_dataset(gpf_instance)
    _t4c8_study_4(root_path, gpf_instance)

    gpf_instance.reload()

    for study_id in [
            "t4c8_study_1", "t4c8_study_2", "t4c8_dataset", "t4c8_study_4"]:
        study = gpf_instance.get_genotype_data(study_id)
        assert study is not None, study_id
        DenovoGeneSetHelpers.build_collection(study)

    gpf_instance.reload()

    return gpf_instance


def _t4c8_study_1(
    root_path: pathlib.Path,
    t4c8_instance: GPFInstance,
) -> GenotypeData:
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

    return vcf_study(
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
        study_config_update={
            "phenotype_data": "study_1_pheno",
        },
    )


def _t4c8_study_2(
    root_path: pathlib.Path,
    t4c8_instance: GPFInstance,
) -> GenotypeData:
    ped_path = setup_pedigree(
        root_path / "t4c8_study_2" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f2.1     mom1     0     0     2   1      mom
f2.1     dad1     0     0     1   1      dad
f2.1     ch1      dad1  mom1  2   2      prb
f2.3     mom3     0     0     2   1      mom
f2.3     dad3     0     0     1   1      dad
f2.3     ch3      dad3  mom3  2   2      prb
f2.3     ch4      dad3  mom3  2   0      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "t4c8_study_2" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3 ch4
chr1   5   .  A   C   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0 0/1
chr1   6   .  C   G   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/1 0/0
chr1   7   .  G   T   .    .      .    GT     0/0  1/0  0/1 0/0  0/0  0/0 0/1
        """)

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            },
        },
    }
    return vcf_study(
        root_path,
        "t4c8_study_2", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
        study_config_update={
            "conf_dir": str(root_path / "t4c8_study_2"),
            "person_set_collections": {
                "phenotype": {
                    "id": "phenotype",
                    "name": "Phenotype",
                    "sources": [
                        {
                            "from": "pedigree",
                            "source": "status",
                        },
                    ],
                    "default": {
                        "color": "#aaaaaa",
                        "id": "unspecified",
                        "name": "unspecified",
                    },
                    "domain": [
                        {
                            "color": "#bbbbbb",
                            "id": "epilepsy",
                            "name": "epilepsy",
                            "values": [
                                "affected",
                            ],
                        },
                        {
                            "color": "#00ff00",
                            "id": "unaffected",
                            "name": "unaffected",
                            "values": [
                                "unaffected",
                            ],
                        },
                    ],
                },
                "selected_person_set_collections": [
                    "phenotype",
                ],
            },
        })


def _t4c8_dataset(
    t4c8_instance: GPFInstance,
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    (root_path / "datasets").mkdir(exist_ok=True)

    setup_dataset_config(
        t4c8_instance,
        "t4c8_dataset",
        ["t4c8_study_1", "t4c8_study_2"],
        dataset_config_update=textwrap.dedent(f"""
            conf_dir: { root_path / "dataset "}
            person_set_collections:
                phenotype:
                  id: phenotype
                  name: Phenotype
                  sources:
                  - from: pedigree
                    source: status
                  domain:
                  - color: '#4b2626'
                    id: developmental_disorder
                    name: developmental disorder
                    values:
                    - affected
                  - color: '#ffffff'
                    id: unaffected
                    name: unaffected
                    values:
                    - unaffected
                  default:
                    color: '#aaaaaa'
                    id: unspecified
                    name: unspecified
                selected_person_set_collections:
                - phenotype"""))


def setup_wgpf_instance(root_path: pathlib.Path) -> WGPFInstance:
    t4c8_instance = setup_t4c8_instance(root_path)
    t4c8_grr = t4c8_instance.grr
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    instance_filename = str(root_path / "gpf_instance.yaml")
    return WGPFInstance.build(instance_filename, grr=t4c8_grr)


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
  - freq
  - pheno_measures
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
  - pheno_measures

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
    pheno_measures:
      name: pheno measures
      columns:
      - pheno_age
      - pheno_iq

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

    phenotype:
      pheno_age:
        role: prb
        source: "i1.age"
        format: "%%.3f"
        name: Age
      pheno_iq:
        role: prb
        source: "i1.iq"
        format: "%%.3f"
        name: IQ

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
  enabled: true
  selected_person_set_collections:
    - phenotype
  selected_background_models:
    - coding_len_background
  default_background_model: coding_len_background
  selected_counting_models:
    - enrichment_gene_counting
    - enrichment_events_counting
  counting:
    enrichment_gene_counting:
      id: enrichment_gene_counting
      name: Counting affected genes
      desc: Counting affected genes
    enrichment_events_counting:
      id: enrichment_events_counting
      name: Counting events
      desc: Counting events
  default_counting_model: enrichment_gene_counting
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
    - CNV+
    - CNV-
gene_browser:
  enabled: true
  frequency_column: "score_one"
  effect_column: "effect.worst effect type"
  location_column: "variant.location"
  domain_min: 0.01
  domain_max: 100
            """),
        },
    )


def _study_1_pheno(
    root_path: pathlib.Path,
    instance_path: pathlib.Path,
) -> None:
    pheno_path = root_path / "study_1_pheno_import"
    ped_path = setup_pedigree(
        pheno_path / "pedigree" / "study_1_pheno.ped", textwrap.dedent("""
familyId personId dadId momId sex status role phenotype
f1.1     mom1     0     0     2   1      mom  unaffected
f1.1     dad1     0     0     1   1      dad  unaffected
f1.1     p1       dad1  mom1  2   2      prb  autism
f1.1     s1       dad1  mom1  1   1      sib  unaffected
f1.2     mom2     0     0     2   1      mom  unaffected
f1.2     dad2     0     0     1   1      dad  unaffected
f1.2     p2       dad2  mom2  2   2      prb  autism
f1.2     s2       dad2  mom2  1   1      sib  unaffected
f1.3     mom3     0     0     2   1      mom  unaffected
f1.3     dad3     0     0     1   1      dad  unaffected
f1.3     p3       dad3  mom3  2   2      prb  autism
f1.3     s3       dad3  mom3  2   1      sib  unaffected
f1.4     mom4     0     0     2   1      mom  unaffected
f1.4     dad4     0     0     1   1      dad  unaffected
f1.4     p4       dad4  mom4  2   2      prb  autism
f1.4     s4       dad4  mom4  2   1      sib  unaffected
        """),
    )
    setup_directories(
        pheno_path / "instruments", {
        "i1.csv": textwrap.dedent("""
personId,age,iq,m1,m2,m3,m4,m5
mom1,495.85101568044115,97.50432405604393,52.81283557677513,30.02770124013255,71.37577329050546,7,val3
dad1,455.7415088310677,95.69209763066596,30.17069676417365,46.09107120958192,80.80918132613797,6,val5
p1,166.33975600961486,104.91189182223437,110.71113119414974,28.525899172698242,35.91763476048754,0,val3
s1,171.7517126432528,38.666056616173776,89.98648478019244,45.48364527683189,36.402944728465634,1,val2
mom2,538.9804553566523,77.21819916001459,54.140552015763305,46.634514570013124,57.885493130264315,5,val3
dad2,565.9100943623504,74.26681832043354,63.03565166617398,36.205901443513405,88.42665767730243,8,val4
p2,111.53800328766471,66.69411560428445,75.83138674585497,43.482874849182046,42.4619179257155,0,val2
s2,112.55713299362333,103.40031120687064,81.23597041806396,26.159521971641645,34.43553369099789,0,val3
mom3,484.44595137123844,65.76732558306583,91.03624223708377,60.66214100006954,82.3034749091715,6,val3
dad3,529.0340708815538,102.32942897750618,102.99152655929812,49.50549744685827,74.83036326691582,2,val1
p3,68.00148724003327,69.33300891928155,96.6345202846831,39.854725276645524,41.07164247649136,2,val1
s3,82.79666720433862,14.497397082398294,70.28387304358455,36.733060149749015,32.979273050187054,0,val3
mom4,413.46229185729595,100.18402999912475,80.87413378193011,56.58170217214086,52.756604936750776,2,val4
dad4,519.696209236225,95.17277547237524,50.73287772082178,34.58584942696778,63.241999271724694,2,val3
p4,157.61834502034586,103.07449426952655,99.54884909890457,37.31662520714209,50.87487739184816,2,val1
s4,121.0199895975403,39.74107684421966,77.32212831797972,51.37116746952451,36.558215318085175,1,val4
        """),
    })

    setup_directories(
        pheno_path, {
        "regressions.yaml": textwrap.dedent("""
        regression:
          age:
            instrument_name: "i1"
            measure_name: "age"
            display_name: "Age"
            jitter: 0.1
          iq:
            instrument_name: "i1"
            measure_name: "iq"
            display_name: "Non verbal IQ"
            jitter: 0.1
        """),
    })

    pheno_import([
        "--pheno-id", "study_1_pheno",
        "-p", str(ped_path),
        "-i", str(pheno_path / "instruments"),
        "--force",
        "-j", "1",
        "--person-column", "personId",
        "-o", str(instance_path / "pheno" / "study_1_pheno"),
        "--task-status-dir", str(pheno_path / "status"),
        "--regression", str(pheno_path / "regressions.yaml"),
    ])
    build_browser([
        str(instance_path / "pheno" / "study_1_pheno"),
        "--phenotype-data-id", "study_1_pheno",
        "-j", "1",
        "--force",
        "--task-status-dir", str(pheno_path / "status"),
    ])


def _t4c8_study_4(
    root_path: pathlib.Path,
    t4c8_instance: GPFInstance,
) -> GenotypeData:
    ped_path = setup_pedigree(
        root_path / "t4c8_study_4" / "pedigree" / "in.ped",
        """
familyId personId dadId  momId  sex status role phenotype
f4.1     mom4.1   0      0      2   1      mom  unaffected
f4.1     dad4.1   0      0      1   1      dad  unaffected
f4.1     p4.1     dad4.1 mom4.1 2   2      prb  autism
f4.1     s4.1     dad4.1 mom4.1 1   1      sib  unaffected
f4.3     mom4.3   0      0      2   1      mom  unaffected
f4.3     dad4.3   0      0      1   1      dad  unaffected
f4.3     p4.3     dad4.3 mom4.3 2   2      prb  autism
f4.3     s4.3     dad4.3 mom4.3 2   1      sib  unaffected
f4.5     mom4.5   0      0      2   1      mom  unaffected
f4.5     dad4.5   0      0      1   1      dad  unaffected
f4.5     p4.5     dad4.5 mom4.5 1   2      prb  autism
        """)
    vcf_path1 = setup_vcf(
        root_path / "t4c8_study_4" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID   REF ALT QUAL FILTER INFO FORMAT mom4.1 dad4.1 p4.1 s4.1 mom4.3 dad4.3 p4.3 s4.3 mom4.5 dad4.5 p4.5
chr1   52  MIS  C   A   .    .      .    GT     0/0    0/0    0/1  0/0  0/0    0/0    0/0  0/0  0/0    0/0    0/0
chr1   54  SYN  T   C   .    .      .    GT     0/0    0/0    0/0  0/0  0/0    0/0    0/1  0/0  0/0    0/0    0/0
chr1   57  SYN  A   C   .    .      .    GT     0/0    0/0    0/1  0/0  0/0    0/0    0/1  0/1  0/0    0/0    0/1
chr1   117 MIS  T   G   .    .      .    GT     0/0    0/0    0/1  0/0  0/0    0/0    0/0  0/1  0/0    0/0    0/1
chr1   119 SYN  A   G   .    .      .    GT     0/0    0/0    0/0  0/1  0/0    0/0    0/0  0/0  0/0    0/0    0/0
        """)  # noqa: E501

    return vcf_study(
        root_path,
        "t4c8_study_4", ped_path, [vcf_path1],
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

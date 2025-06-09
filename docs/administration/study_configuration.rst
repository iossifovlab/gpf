GPF Study Configuration
=======================


* ``id`` - ID of the study. This is a required field.

* ``name`` - display name of the study. If the ``name`` is not specified, the
  ``id`` will be used as the display name.

* ``enabled`` - whether the study is enabled. 

* ``description_file`` - path to the study description file.

* ``study_phenotype`` - study phenotype. 

* ``has_denovo`` - whether the study has de novo variants.

* ``has_transmitted`` - whether the study has transmitted variants.

* ``has_cnv`` - whether the study has CNV variants.

* ``has_complex`` - whether the study has complex variants.

* ``has_tandem_repeat`` - whether the study has tandem repeat variants.

* ``has_zygosity`` - whether the study has zygosity information.

* ``phenotype_data`` - phenotype data associated with the study.
    
* ``phenotype_browser`` - whether the phenotype browser is enabled.
* ``phenotype_tool`` - whether the phenotype tool is enabled.

* ``person_set_collections`` - section to define person set collections
  associated with the study.

* ``genotype_storage`` - section to define genotype storage configuration for
  the study.

* ``genotype browser`` - section to define genotype browser configuration for the
  study.
* ``common_report`` - section to define common report configuration for the
  study.
* ``denovo_gene_sets`` - section to define de novo gene sets configuration for
  the study.
* ``enrichment`` - section to define enrichment configuration for the study.
* ``gene_browser`` - section to define gene browser configuration for the
  study.

.. code-block:: yaml
    :linenos:

    id: example_study
    phenotype_browser: false
    phenotype_tool: false
    study_type:
    - WE
    study_phenotype: autism
    has_transmitted: false
    has_denovo: true
    has_complex: false
    has_cnv: false

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

      has_present_in_child: true
      has_present_in_parent: true
      has_pedigree_selector: true

      variant_types:
        - sub
        - ins
        - del
        - complex
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
            lgd_rank:
                name: LGD rank
                source: LGD_rank
                format: '%%d'
            rvis_rank:
                name: RVIS rank
                source: RVIS_rank
                format: '%%d'
            pli_rank:
                name: pLI rank
                source: pLI_rank
                format: '%%d'
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
            phylop_phylop100way:
                name: 100way
                source: phylop100way
                format: '%%.3f'
            phylop_phylop30way:
                name: 30way
                source: phylop30way
                format: '%%.3f'
            phylop_phylop20way:
                name: 20way
                source: phylop20way
                format: '%%.3f'
            phastcons_phastcons100way:
                name: 100way
                source: phastcons100way
                format: '%%.3f'
            phastcons_phastcons30way:
                name: 30way
                source: phastcons30way
                format: '%%.3f'
            phastcons_phastcons20way:
                name: 20way
                source: phastcons20way
                format: '%%.3f'
            fitcons_fitcons2_e073:
                name: Prefrontal Cortex
                source: fitcons2_e073
                format: '%%.3f'
            fitcons_fitcons2_e081:
                name: ' Male Fetal'
                source: fitcons2_e081
                format: '%%.3f'
            fitcons_fitcons2_e082:
                name: Female Fetal
                source: fitcons2_e082
                format: '%%.3f'
            freq_ssc:
                name: SSC
                source: ssc_freq
                format: '%%.3f'
            freq_exome_gnomad:
                name: exome gnomAD
                source: exome_gnomad_v2_1_1_af_percent
                format: '%%.3f'
            freq_genome_gnomad:
                name: genome gnomAD
                source: genome_gnomad_v3_af_percent
                format: '%%.3f'
            cadd_raw:
                name: CADD raw
                source: cadd_raw
                format: '%%.3f'
            cadd_phred:
                name: CADD phred
                source: cadd_phred
                format: '%%.3f'
            mpc:
                name: MPC
                source: mpc
                format: '%%.3f'
            linsight:
                name: Linsight
                source: linsight
                format: '%%.3f'
            genome_gnomad_v2_1_1_ac:
                name: genome_gnomad_v2_1_1_ac
                source: genome_gnomad_v2_1_1_ac
                format: '%%d'
            genome_gnomad_v2_1_1_an:
                name: genome_gnomad_v2_1_1_an
                source: genome_gnomad_v2_1_1_an
                format: '%%d'
            genome_gnomad_v2_1_1_controls_ac:
                name: genome_gnomad_v2_1_1_controls_ac
                source: genome_gnomad_v2_1_1_controls_ac
                format: '%%d'
            genome_gnomad_v2_1_1_controls_an:
                name: genome_gnomad_v2_1_1_controls_an
                source: genome_gnomad_v2_1_1_controls_an
                format: '%%d'
            genome_gnomad_v2_1_1_non_neuro_ac:
                name: genome_gnomad_v2_1_1_non_neuro_ac
                source: genome_gnomad_v2_1_1_non_neuro_ac
                format: '%%d'
            genome_gnomad_v2_1_1_non_neuro_an:
                name: genome_gnomad_v2_1_1_non_neuro_an
                source: genome_gnomad_v2_1_1_non_neuro_an
                format: '%%d'
            genome_gnomad_v2_1_1_af_percent:
                name: genome_gnomad_v2_1_1_af_percent
                source: genome_gnomad_v2_1_1_af_percent
                format: '%%.3f'
            genome_gnomad_v2_1_1_controls_af_percent:
                name: genome_gnomad_v2_1_1_controls_af_percent
                source: genome_gnomad_v2_1_1_controls_af_percent
                format: '%%.3f'
            genome_gnomad_v2_1_1_non_neuro_af_percent:
                name: genome_gnomad_v2_1_1_non_neuro_af_percent
                source: genome_gnomad_v2_1_1_non_neuro_af_percent
                format: '%%.3f'
            exome_gnomad_v2_1_1_ac:
                name: exome_gnomad_v2_1_1_ac
                source: exome_gnomad_v2_1_1_ac
                format: '%%d'
            exome_gnomad_v2_1_1_an:
                name: exome_gnomad_v2_1_1_an
                source: exome_gnomad_v2_1_1_an
            exome_gnomad_v2_1_1_controls_ac:
                name: exome_gnomad_v2_1_1_controls_ac
                source: exome_gnomad_v2_1_1_controls_ac
                format: '%%d'
            exome_gnomad_v2_1_1_controls_an:
                name: exome_gnomad_v2_1_1_controls_an
                source: exome_gnomad_v2_1_1_controls_an
                format: '%%d'
            exome_gnomad_v2_1_1_non_neuro_ac:
                name: exome_gnomad_v2_1_1_non_neuro_ac
                source: exome_gnomad_v2_1_1_non_neuro_ac
                format: '%%d'
            exome_gnomad_v2_1_1_non_neuro_an:
                name: exome_gnomad_v2_1_1_non_neuro_an
                source: exome_gnomad_v2_1_1_non_neuro_an
                format: '%%d'
            exome_gnomad_v2_1_1_af_percent:
                name: exome_gnomad_v2_1_1_af_percent
                source: exome_gnomad_v2_1_1_af_percent
                format: '%%.3f'
            exome_gnomad_v2_1_1_controls_af_percent:
                name: exome_gnomad_v2_1_1_controls_af_percent
                source: exome_gnomad_v2_1_1_controls_af_percent
                format: '%%.3f'
            exome_gnomad_v2_1_1_non_neuro_af_percent:
                name: exome_gnomad_v2_1_1_non_neuro_af_percent
                source: exome_gnomad_v2_1_1_non_neuro_af_percent
                format: '%%.3f'
            genome_gnomad_v3_ac:
                name: genome_gnomad_v3_ac
                source: genome_gnomad_v3_ac
                format: '%%d'
            genome_gnomad_v3_an:
                name: genome_gnomad_v3_an
                source: genome_gnomad_v3_an
                format: '%%d'
            genome_gnomad_v3_af_percent:
                name: genome_gnomad_v3_af_percent
                source: genome_gnomad_v3_af_percent
                format: '%%.3f'
            phylop100way:
                name: phyloP100way
                source: phylop100way
                format: '%%.3f'
            phylop30way:
                name: phyloP30way
                source: phylop30way
                format: '%%.3f'
            phylop20way:
                name: phyloP20way
                source: phylop20way
                format: '%%.3f'
            phylop7way:
                name: phyloP7way
                source: phylop7way
                format: '%%.3f'
            phastcons100way:
                name: phastCons100way
                source: phastcons100way
                format: '%%.3f'
            phastcons30way:
                name: phastCons30way
                source: phastcons30way
                format: '%%.3f'
            phastcons20way:
                name: phastCons20way
                source: phastcons20way
                format: '%%.3f'
            phastcons7way:
                name: phastCons7way
                source: phastcons7way
                format: '%%.3f'
            fitcons_i6_merged:
                name: FitCons i6 merged
                source: fitcons_i6_merged
                format: '%%.3f'
            fitcons2_e067:
                name: FitCons2 Brain Angular Gyrus
                source: fitcons2_e067
                format: '%%.3f'
            fitcons2_e068:
                name: FitCons2 Brain Anterior Caudate
                source: fitcons2_e068
                format: '%%.3f'
            fitcons2_e069:
                name: FitCons2 Brain Cingulate Gyrus
                source: fitcons2_e069
                format: '%%.3f'
            fitcons2_e070:
                name: FitCons2 Brain Germinal Matrix
                source: fitcons2_e070
                format: '%%.3f'
            fitcons2_e071:
                name: FitCons2 Brain Hippocampus Middle
                source: fitcons2_e071
                format: '%%.3f'
            fitcons2_e072:
                name: FitCons2 Brain Inferior Temporal Lobe
                source: fitcons2_e072
                format: '%%.3f'
            fitcons2_e073:
                name: FitCons2 Brain Dorsolateral Prefrontal Cortex
                source: fitcons2_e073
                format: '%%.3f'
            fitcons2_e074:
                name: FitCons2 Brain Substantia Nigra
                source: fitcons2_e074
                format: '%%.3f'
            fitcons2_e081:
                name: FitCons2 Fetal Brain Male
                source: fitcons2_e081
                format: '%%.3f'
            fitcons2_e082:
                name: FitCons2 Fetal Brain Female
                source: fitcons2_e082
                format: '%%.3f'
  
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
          - lgd_rank
          - rvis_rank
          - pli_rank
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
        mpc_cadd:
          name: MPC and CADD
          columns:
          - mpc
          - cadd_raw
          - cadd_phred
        phylop:
          name: phyloP
          columns:
          - phylop_phylop100way
          - phylop_phylop30way
          - phylop_phylop20way
        phastcons:
          name: phastCons
          columns:
          - phastcons_phastcons100way
          - phastcons_phastcons30way
          - phastcons_phastcons20way
        fitcons:
          name: FitCons Brain
          columns:
          - fitcons_fitcons2_e073
          - fitcons_fitcons2_e081
          - fitcons_fitcons2_e082
        freq:
          name: Frequency
          columns:
          - freq_ssc
          - freq_exome_gnomad
          - freq_genome_gnomad

      preview_columns:
      - family
      - variant
      - genotype
      - effect
      - gene_scores
      - phylop
      - phastcons
      - mpc_cadd
      - fitcons
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
      - phylop100way
      - phylop30way
      - phylop20way
      - phylop7way
      - phastcons100way
      - phastcons30way
      - phastcons20way
      - phastcons7way
      - cadd_raw
      - cadd_phred
      - mpc
      - linsight
      - fitcons_i6_merged
      - fitcons2_e067
      - fitcons2_e068
      - fitcons2_e069
      - fitcons2_e070
      - fitcons2_e071
      - fitcons2_e072
      - fitcons2_e073
      - fitcons2_e074
      - fitcons2_e081
      - fitcons2_e082
      - genome_gnomad_v2_1_1_ac
      - genome_gnomad_v2_1_1_an
      - genome_gnomad_v2_1_1_controls_ac
      - genome_gnomad_v2_1_1_controls_an
      - genome_gnomad_v2_1_1_non_neuro_ac
      - genome_gnomad_v2_1_1_non_neuro_an
      - genome_gnomad_v2_1_1_af_percent
      - genome_gnomad_v2_1_1_controls_af_percent
      - genome_gnomad_v2_1_1_non_neuro_af_percent
      - exome_gnomad_v2_1_1_ac
      - exome_gnomad_v2_1_1_an
      - exome_gnomad_v2_1_1_controls_ac
      - exome_gnomad_v2_1_1_controls_an
      - exome_gnomad_v2_1_1_non_neuro_ac
      - exome_gnomad_v2_1_1_non_neuro_an
      - exome_gnomad_v2_1_1_af_percent
      - exome_gnomad_v2_1_1_controls_af_percent
      - exome_gnomad_v2_1_1_non_neuro_af_percent
      - genome_gnomad_v3_ac
      - genome_gnomad_v3_an
      - genome_gnomad_v3_af_percent

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
      selected_person_set_collections:
      - phenotype
      selected_background_models:
      - hg38/enrichment/coding_length_ref_gene_v20170601
      - enrichment/samocha_background
      - hg38/enrichment/ur_synonymous_SFARI_SSC_WGS_2
      - hg38/enrichment/ur_synonymous_SFARI_SSC_WGS_CSHL
      - hg38/enrichment/ur_synonymous_w1202s766e611_liftover
      - hg38/enrichment/ur_synonymous_iWES_v1_1
      - hg38/enrichment/ur_synonymous_iWES_v2
      - hg38/enrichment/ur_synonymous_iWGS_v1_1
      - hg38/enrichment/ur_synonymous_AGRE_WG38_859
      default_background_model: enrichment/samocha_background
      selected_counting_models:
      - enrichment_events_counting
      - enrichment_gene_counting
      counting:
        enrichment_events_counting:
          id: enrichment_events_counting
          name: Counting events
          desc: Counting events
        enrichment_gene_counting:
          id: enrichment_gene_counting
          name: Counting affected genes
          desc: Counting affected genes
      default_counting_model: enrichment_events_counting
      effect_types:
      - LGDs
      - missense
      - synonymous

    gene_browser:
      enabled: true
      frequency_column: genome_gnomad_v3_af_percent
      frequency_name: genome GnomAD %%
      effect_column: effect.worst effect type
      location_column: variant.location
      domain_min: 0.01
      domain_max: 100

Impala Batch Import
===================

.. code-block:: bash
	
	usage: impala_batch_import.py [-h] [--ped-family PED_FAMILY]
	                              [--ped-person PED_PERSON] [--ped-mom PED_MOM]
	                              [--ped-dad PED_DAD] [--ped-sex PED_SEX]
	                              [--ped-status PED_STATUS] [--ped-role PED_ROLE]
	                              [--ped-no-role] [--ped-proband PED_PROBAND]
	                              [--ped-no-header]
	                              [--ped-file-format PED_FILE_FORMAT]
	                              [--ped-layout-mode PED_LAYOUT_MODE]
	                              [--ped-sep PED_SEP]
	                              [--denovo-variant DENOVO_VARIANT]
	                              [--denovo-ref DENOVO_REF]
	                              [--denovo-alt DENOVO_ALT]
	                              [--denovo-location DENOVO_LOCATION]
	                              [--denovo-chrom DENOVO_CHROM]
	                              [--denovo-pos DENOVO_POS]
	                              [--denovo-family-id DENOVO_FAMILY_ID]
	                              [--denovo-best-state DENOVO_BEST_STATE]
	                              [--denovo-person-id DENOVO_PERSON_ID]
	                              [--denovo-sep DENOVO_SEP]
	                              [--vcf-include-reference-genotypes]
	                              [--vcf-include-unknown-family-genotypes]
	                              [--vcf-include-unknown-person-genotypes]
	                              [--vcf-multi-loader-fill-in-mode VCF_MULTI_LOADER_FILL_IN_MODE]
	                              [--vcf-denovo-mode VCF_DENOVO_MODE]
	                              [--vcf-omission-mode VCF_OMISSION_MODE]
	                              [--vcf-chromosomes VCF_CHROMOSOMES]
	                              [--dae-include-reference-genotypes]
	                              [--add-chrom-prefix ADD_CHROM_PREFIX]
	                              [--del-chrom-prefix DEL_CHROM_PREFIX]
	                              [--vcf-files <VCF filename> [<VCF filename> ...]]
	                              [--denovo-file <de Novo variants filename>]
	                              [--dae-summary-file <summary filename>]
	                              [--study-id <study id>] [-o <output directory>]
	                              [--pd PARTITION_DESCRIPTION]
	                              [--annotation-config ANNOTATION_CONFIG]
	                              [--genotype-storage GENOTYPE_STORAGE]
	                              [--target-chromosomes TARGET_CHROMOSOMES [TARGET_CHROMOSOMES ...]]
	                              <families filename>
	
	Convert variants file to parquet
	
	positional arguments:
	  <families filename>   families filename in pedigree or simple family format
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --ped-family PED_FAMILY
	                        specify the name of the column in the pedigree file
	                        that holds the ID of the family the person belongs to
	                        [default: familyId]
	  --ped-person PED_PERSON
	                        specify the name of the column in the pedigree file
	                        that holds the person's ID [default: personId]
	  --ped-mom PED_MOM     specify the name of the column in the pedigree file
	                        that holds the ID of the person's mother [default:
	                        momId]
	  --ped-dad PED_DAD     specify the name of the column in the pedigree file
	                        that holds the ID of the person's father [default:
	                        dadId]
	  --ped-sex PED_SEX     specify the name of the column in the pedigree file
	                        that holds the sex of the person [default: sex]
	  --ped-status PED_STATUS
	                        specify the name of the column in the pedigree file
	                        that holds the status of the person [default: status]
	  --ped-role PED_ROLE   specify the name of the column in the pedigree file
	                        that holds the role of the person [default: role]
	  --ped-no-role         indicates that the provided pedigree file has no role
	                        column. If this argument is provided, the import tool
	                        will guess the roles of individuals and write them in
	                        a "role" column.
	  --ped-proband PED_PROBAND
	                        specify the name of the column in the pedigree file
	                        that specifies persons with role `proband`; this
	                        columns is used only when option `--ped-no-role` is
	                        specified. [default: None]
	  --ped-no-header       indicates that the provided pedigree file has no
	                        header. The pedigree column arguments will accept
	                        indices if this argument is given. [default: False]
	  --ped-file-format PED_FILE_FORMAT
	                        Families file format. It should `pedigree` or
	                        `simple`for simple family format [default: pedigree]
	  --ped-layout-mode PED_LAYOUT_MODE
	                        Layout mode specifies how pedigrees drawing of each
	                        family is handled. Available options are `generate`
	                        and `load`. When layout mode option is set to generate
	                        the loadertryes to generate a layout for the family
	                        pedigree. When `load` is specified, the loader tries
	                        to load the layout from the layout column of the
	                        pedigree. [default: load]
	  --ped-sep PED_SEP     Families file field separator [default: `\t`]
	  --denovo-sep DENOVO_SEP
	                        Denovo file field separator [default: `\t`]
	  --vcf-include-reference-genotypes
	                        include reference only variants [default: False]
	  --vcf-include-unknown-family-genotypes
	                        include family variants with fully unknown genotype
	                        [default: False]
	  --vcf-include-unknown-person-genotypes
	                        include family variants with partially unknown
	                        genotype [default: False]
	  --vcf-multi-loader-fill-in-mode VCF_MULTI_LOADER_FILL_IN_MODE
	                        used for multi VCF files loader to fill missing
	                        genotypes; supported values are `reference` or
	                        `unknown`[default: reference]
	  --vcf-denovo-mode VCF_DENOVO_MODE
	                        used for handling family variants with denovo
	                        inheritance; supported values are: `denovo`,
	                        `possible_denovo`, `ignore`; [default:
	                        possible_denovo]
	  --vcf-omission-mode VCF_OMISSION_MODE
	                        used for handling family variants with omission
	                        inheritance; supported values are: `omission`,
	                        `possible_omission`, `ignore`; [default:
	                        possible_omission]
	  --vcf-chromosomes VCF_CHROMOSOMES, --vc VCF_CHROMOSOMES
	                        specifies a list of filename template substitutions;
	                        then specified variant filename(s) are treated as
	                        templates and each occurent of `{vc}` is replaced
	                        consecutively by elements of VCF wildcards list; by
	                        default the list is empty and no substitution takes
	                        place. [default: None]
	  --dae-include-reference-genotypes
	                        fill in reference only variants [default: False]
	  --add-chrom-prefix ADD_CHROM_PREFIX
	                        Add specified prefix to each chromosome name in
	                        variants file
	  --del-chrom-prefix DEL_CHROM_PREFIX
	                        Removes specified prefix from each chromosome name in
	                        variants file
	  --vcf-files <VCF filename> [<VCF filename> ...]
	                        VCF file to import
	  --denovo-file <de Novo variants filename>
	                        DAE denovo variants file
	  --dae-summary-file <summary filename>
	                        summary variants file to import
	  --study-id <study id>, --id <study id>
	                        Study ID. If none specified, the basename of families
	                        filename is used to construct study id [default:
	                        basename(families filename)]
	  -o <output directory>, --out <output directory>
	                        output directory. If none specified, current directory
	                        is used [default: .]
	  --pd PARTITION_DESCRIPTION, --partition-description PARTITION_DESCRIPTION
	                        Path to a config file containing the partition
	                        description
	  --annotation-config ANNOTATION_CONFIG
	                        Path to an annotation config file to use when
	                        annotating
	  --genotype-storage GENOTYPE_STORAGE, --gs GENOTYPE_STORAGE
	                        Genotype Storage which will be used for import
	                        [default: genotype_filesystem]
	  --target-chromosomes TARGET_CHROMOSOMES [TARGET_CHROMOSOMES ...], --tc TARGET_CHROMOSOMES [TARGET_CHROMOSOMES ...]
	                        specified which targets to build; by default target
	                        chromosomes are extracted from variants file and/or
	                        default reference genome used in GPF instance;
	                        [default: None]
	
	variant specification:
	  --denovo-variant DENOVO_VARIANT
	                        The label or index of the column containing the CSHL-
	                        style representation of the variant.[Default: variant]
	  --denovo-ref DENOVO_REF
	                        The label or index of the column containing the
	                        reference allele for the variant. [Default: none]
	  --denovo-alt DENOVO_ALT
	                        The label or index of the column containing the
	                        alternative allele for the variant. [Default: none]
	
	variant location:
	  --denovo-location DENOVO_LOCATION
	                        The label or index of the column containing the CSHL-
	                        style location of the variant. [Default: location]
	  --denovo-chrom DENOVO_CHROM
	                        The label or index of the column containing the
	                        chromosome upon which the variant is located.
	                        [Default: none]
	  --denovo-pos DENOVO_POS
	                        The label or index of the column containing the
	                        position upon which the variant is located. [Default:
	                        none]
	
	variant genotype:
	  --denovo-family-id DENOVO_FAMILY_ID
	                        The label or index of the column containing the
	                        family's ID. [Default: familyId]
	  --denovo-best-state DENOVO_BEST_STATE
	                        The label or index of the column containing the best
	                        state for the family. [Default: bestState]
	  --denovo-person-id DENOVO_PERSON_ID
	                        The label or index of the column containing the
	                        person's ID. [Default: none]


Import Tools
============

What is Import Tools
--------------------

Import Tools is the new way to import studies into seqpipe. Import Tools allows
for studies to be imported in one step without the need to generate Snakefiles
and execute those in another step. The study and the arguments used to import it
are described in a single yaml config file. The config file is general enough
and can be commited in a source code repository allowing other team members to
use it.

Import Tools assumes input data has already been massaged into a format
supported by seqpipe.

Import Tools config files
-------------------------

Import Tools config files has a relatively simple structure. In their simple
form they consist of 3 sections:
 - Input section: describing the input files. Files like the pedigree file, vcf
   files and the configuration options required to read these files successfully.
 - Processing config: describing how the input is supposed to be handled and
   processed.
 - Destination: describing whre to store the imported data. This could be like
   an impala table. This section also includes the partition_description.

Import Tools configuration format
---------------------------------
.. code-block:: yaml

    vars:
        input_dir: "..."

    id: SFARI_SPARK_WES_2

    input:
        file: "external file defining input"
        (OR)
        input_dir:
    
        pedigree:
            file: %(input_dir)s/SFARI_SPARK_WES_2.ped

    vcf:
        files:
            - wes2_15995_exome.gatk.vcf.gz
        denovo_mode: ignore
        omission_mode: ignore
        add_chrom_prefix: chr
    denovo:
        files:
            - wes2_merged_cohFreq_Cut17_final_v1_ALL_042921_GPF.tsv.txt
        persion_id: spid
        chrom: chrom
        pos: pos
        ref: ref
        alt: alt
        add_chrom_prefix: chr

    processing_config:
        vcf: single_bucket
        (OR)
        vcf: chromsome
        (OR):
        vcf:
            chromosomes: ['chr1', 'chr2', 'chr3', ..., 'chr22', 'chrX', 'chrY']
        (OR):
        vcf:
            chromosomes: ['autosomes', 'chrX', 'chrM']
            region_length: 100M
        vcf:
            import_task_bin_size: 1000000
        work_dir: ""

    gpf_instance:
        path: ...

    (optional by default use gpf_instance annotation pipeline-a)
    annotation:
        gpf_pipeline: ""
        (OR)
        file: ""
        (OR)
        embedded-annotation

    (optional by default use the default storage of the gpf instance)
    destination:
        storage_id: "id in gpf_instance"
        (OR)
        storage_type: impala_schema_1
            hdfs:
                base_dir: "/user/impala_schema_1/studies"
                host: seqclust0
                port: 8020
                replication: 1
            impala:
                db: "impala_schema_1"
                hosts:
                    - seqclust0
                    - seqclust1
                    - seqclust2
                port: 21050
                pool_size: 3

    parquet_row_group_size:
        vcf: 30M

    partition_description:
        region_bin:
            chromosomes: [chr1, chr2, chr3, chr4, chr5, chr6, chr7, chr8, chr9, chr10, chr11, chr12, chr13, chr14, chr15, chr16, chr17, chr18, chr19, chr20, chr21, chr22, chrX]
            region_length: 30000000
        family_bin:
            bin_size: 10
        frequency_bin:
            rare_boundary: 5
        coding_bin:
            coding_effect_types: [splice-site,frame-shift,nonsense,no-frame-shift-newStop,noStart,noEnd,missense,no-frame-shift,CDS,synonymous,coding_unknown,regulatory,3'UTR,5'UTR]

For any set of input files (denovo, vcf and so on) if the corresponding section
in *processing_config* is missing then the default value for bucket generation
is *single_bucket*.

All files specified in the *input* section are relative to the *input_dir*. The
*input_dir* is itself relative to the directory where the config file is
located. *input_dir* is options, if unspecified then every file would be
relative to the config file's directory. If the input configuration is in an
external file then input file paths will be relative to the external file.


Classes and Functions
---------------------

.. toctree::
   :maxdepth: 3

   modules/dae.import_tools

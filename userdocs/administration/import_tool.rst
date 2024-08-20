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
- Destination: describing where to store the generated data. For example this
could be an impala table. This section also includes the
partition_description.

Import Tools configuration format
---------------------------------

.. code:: yaml

    vars:
        my_dir: "..."

    id: SFARI_SPARK_WES_2

    input:
        file: "external file defining input"
        (OR)
        input_dir:

        pedigree:
            file: %(my_dir)s/SFARI_SPARK_WES_2.ped
            dad: fatherId
            mom: motherId
            status: affected

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
        work_dir: ""

    (optional by default use default gpf_instance)
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
        storage_type: impala
        (OR)
        storage_type: impala
        id: storage_id
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
            chromosomes: ['autosomes', chrX]  # All chromosomes not explicitly listed are grouped into 'other'.
            region_length: 30M   # this is optional. If ommitted, one region_per chromosome is created.
        family_bin:  # creates family_bin partition. 
                     # Families are randomly split into groups of size bin_size.
            bin_size: 10
        frequency_bin:   # creates frequency_bin partition: 
                         #    0 - de novo, 1 - ultra-rare, 
                         #    2 rare (frequency less than the rare_boundary), 
                         #    3 - common (frequency more than the rare_boundary)
            rare_boundary: 5
        coding_bin:      # creates coding_bin: 1 - coding, 0 - non-coding
            coding_effect_types: "splice-site,frame-shift,nonsense,no-frame-shift-newStop,noStart,noEnd,missense,no-frame-shift,CDS,synonymous,coding_unknown,regulatory,3'UTR,5'UTR"
    OR
    partition_description:
        region_bin:
            chromosomes: ['autosomes', chrX]
    OR
    partition_description:
        frequency_bin:
            rare_boundary: 5


*input* is the section where we describe the input files. It is devided into
subsections for each input type (vcf, denovo and so on).
All files are relative to the *input_dir*. The
*input_dir* is itself relative to the directory where the config file is
located. *input_dir* is options, if unspecified then every file would be
relative to the config file's directory. If the input configuration is in an
external file then input file paths will be relative to the external file.

*processing_config* is where we describe how to split input files into smaller
buckets for parallel processing. *single_bucket* means that the entire input
will be processed in a single task without spliting it into smaller parts.
*chromosome* or a list of chromosomes means that each chromosome will be
processed in parallel. If *region_length* is specified then each chromosome
will be split into regions with length *region_length* and all such regions will
be processed in parallel. *work_dir* is the location where parquet files will
be generated. If missing then the current working directory is used.

For any set of input files (denovo, vcf and so on) if the corresponding section
in *processing_config* is missing then the default value for bucket generation
is *single_bucket*.

*gpf_instance* is an optional section that allows you to specify a gpf instance
configuration file.

*annotation* is where the annotation pipeline is specified. It can either be the
name of a pipeline described in the gpf config (using the gpf_pipeline argument),
path to a file describing the pipeline or an embedded annotation pipeline.

*destination* describes where generated parquet files will be imported. This
section could be the name of a storage defined in the gpf instance or an
embedded storage config. If only *storage_type* is specified then parquet files
will be generated for the particular storage type but will NOT be imported
anywhere. This is useful for just generating parquet files without actually
importing them.


Working with the Import Tools CLI
---------------------------------
To import a study first you would need the import configuration as described
above. To run import tools with the config file execute:

.. code-block:: bash

    import_tools import_config.yaml

To list the steps that will be executed without actually executing them:

.. code-block:: bash

    import_tools import_config.yaml list

*import_tools* has a number of parameters. Run with --help to see them. One
commonly used one is `-j` which specifies the number of tasks to run in parallel.


Running on a SGE cluster
-------------------------

.. code-block:: bash

    import_tools import_config.yaml run --sge -j 100

This command will run import tools on a SGE cluster using 100 parallel workers.
This assumes a preconfigured, working SGE cluster. The *import_config.yaml* file
should be placed on a shared file system that can be accessed by all nodes in
the cluster.


Running on a Kubernetes cluster
-------------------------------

Running on kubernetes is a little bit more involved because typically nodes in
the cluster don't share a common file system and the machine where we run
*import_tools* is usually not part of the cluster. So the import process needs
a common storage that can be access both by the nodes in the cluster and the
machine where import tools is run from. The easiest way to achieve this is by
using S3.

The best setup is to place the import configuration on S3 together will the
input data. Accessing S3 (and other AWS services) usually happends through an
access and secret keys. Assuming these keys are already configured in the
corresponding environment variables we can run import tools like that:

.. code-block:: bash

    import_tools s3://bucket/import_config.yaml run --kubernetes --envvars AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY --image-pull-secrets seqpipe-registry-cred -j 20

The environment variables specified by --envvars will be propagated to the
worker pods so that the workers can access S3. The --image-pull-secrets specifies
a kubernetes secret that should contain the credentials used for accessing the
seqpipe docker registry from which the images for the worker pods will be pulled
from. And -j specifies that 20 workers should be started.

If using a non-AWS S3 such as a ceph storage, the endpoint url can be specified
using the *S3_ENDPOINT_URL* environment variable:


.. code-block:: bash

    S3_ENDPOINT_URL=http://s3.my-server.com:7480 import_tools s3://bucket/import_config.yaml run --kubernetes --envvars AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY --image-pull-secrets seqpipe-registry-cred -j 20




Example of import_project.yaml from existing schema2 parquet files
##################################################################

NOTE: This fails for now, but we will soon repair it.

.. code:: yaml

    id: whole_exome_ten_families_BQ
    
    processing_config:
      parquet_dataset_dir: ./whole_exome_ten_families
    
    destination:
      storage_id: ivan_BIGQUERY

    
Example of import_project.yaml for creating schema2 parquet files
#################################################################

NOTE: Soon, we will change the storage_type to the more appropriate 'schema2'.

.. code:: yaml

    id: whole_exome_ten_families
    input:
      pedigree:
        file: collection.ped
    
      vcf:
        files:
        - transmission.vcf.gz
        denovo_mode: denovo
    
    processing_config:
        vcf:
          chromosomes: ['autosomes']
          region_length: 100M
    destination:
        storage_type: duckdb
#!/bin/bash 

# Working directory 
DATA_DIR=/home/ubuntu/gpf_validation_data/data_hg19/studies/SFARI_SPARK_WES_p/data 
PARTITION_DESC=$DATA_DIR/partition_description.conf

# Ingest data into Impala Schema1:
# --------------------------------------------------------- 

STUDY_ID="schema1"
OUTPUT_DIR=$DATA_DIR/schema1
rm -rf $OUTPUT_DIR

hdfs dfs -fs hdfs://localhost:8020 -rm -r -f /user/data_hg19_empty/studies/schema1

simple_study_import.py ${DATA_DIR}/SPARKv3-families.ped \
    --ped-sex gender \
    -o ${OUTPUT_DIR} \
    --id ${STUDY_ID} \
    --vcf-files ${DATA_DIR}/SPARK_pilot1379ind.ColumbiaJointCall.vcf.gz

#     --denovo-file ${DATA_DIR}/1394probands_denovoSNVindels_annotated5_pf_ia.csv \
#     --denovo-chrom CHROM \
#     --denovo-pos POS \
#     --denovo-person-id SPID \
#     --denovo-ref REF \
#     --denovo-alt ALT \

# Ingests data into Impala & BigQuery Schema2:
# -----------------------------------------------------------

IMPORT_DIR=$DATA_DIR/import 
HDFS_DIR=/user/data_hg19_startup/studies/imported/

rm -rf $IMPORT_DIR && mkdir -p $IMPORT_DIR

# Call ped2parquet, then load the parquet files for schema2 
ped2parquet.py --verbose $DATA_DIR/SPARKv3-families.ped \
	--ped-sex gender \
	--pd $PARTITION_DESC \
	-o $IMPORT_DIR/SPARKv3-families.parquet 

# Convert to VCF to Parquet 
vcf2schema2.py --verbose $DATA_DIR/SPARKv3-families.ped \
	$DATA_DIR/SPARK_pilot1379ind.ColumbiaJointCall.vcf.gz \
	--ped-sex gender \
	--pd $PARTITION_DESC \
	-o $DATA_DIR/import 

# -----------------------------------------------------------
# IMPALA INGESTION 
# -----------------------------------------------------------
hdfs dfs -fs hdfs://localhost:8020 -rm -r -f $HDFS_DIR
hdfs dfs -fs hdfs://localhost:8020 -mkdir $HDFS_DIR 

# Make directories for parquet ingestion 
hdfs dfs -fs hdfs://localhost:8020 -mkdir -p $HDFS_DIR/meta
hdfs dfs -fs hdfs://localhost:8020 -mkdir -p $HDFS_DIR/pedigree
hdfs dfs -fs hdfs://localhost:8020 -mkdir -p $HDFS_DIR/family
hdfs dfs -fs hdfs://localhost:8020 -mkdir -p $HDFS_DIR/summary

# Copy from local FS to HDFS 
hdfs dfs -fs hdfs://localhost:8020 -put -f $IMPORT_DIR/meta.parquet $HDFS_DIR/meta
hdfs dfs -fs hdfs://localhost:8020 -put -f $IMPORT_DIR/SPARKv3-families.parquet $HDFS_DIR/pedigree
hdfs dfs -fs hdfs://localhost:8020 -put -f $IMPORT_DIR/summary/* $HDFS_DIR/summary
hdfs dfs -fs hdfs://localhost:8020 -put -f $IMPORT_DIR/family/* $HDFS_DIR/family 

# Impala create reference parquet tables
docker exec -it gpf_impala rm -rf /impala-import.sql

# no need to hardcode parquet 
META_PARQUET=$HDFS_DIR/meta/meta.parquet
PEDIGREE_PARQUET=$HDFS_DIR/pedigree/SPARKv3-families.parquet
FAMILY_PARQUET=`hdfs dfs -fs hdfs://localhost:8020 -find $HDFS_DIR/family | grep parquet | head -n 1`
SUMMARY_PARQUET=`hdfs dfs -fs hdfs://localhost:8020 -find $HDFS_DIR/summary | grep parquet | head -n 1`

printf "
DROP DATABASE IF EXISTS gpf_schema2 CASCADE;
CREATE DATABASE gpf_schema2;
USE gpf_schema2;

DROP TABLE IF EXISTS imported_parquet;
DROP TABLE IF EXISTS imported_pedigree;
DROP TABLE IF EXISTS imported_summary_allele;
DROP TABLE IF EXISTS imported_family_allele;

CREATE EXTERNAL TABLE IF NOT EXISTS imported_meta
LIKE PARQUET '$META_PARQUET'
STORED AS PARQUET
LOCATION '$HDFS_DIR/meta/';

CREATE EXTERNAL TABLE IF NOT EXISTS imported_pedigree
LIKE PARQUET '$PEDIGREE_PARQUET'
STORED AS PARQUET
LOCATION '$HDFS_DIR/pedigree/';

CREATE EXTERNAL TABLE IF NOT EXISTS imported_summary_alleles
LIKE PARQUET '$SUMMARY_PARQUET'
PARTITIONED BY (region_bin STRING, frequency_bin INT, coding_bin INT)
STORED AS PARQUET
LOCATION '$HDFS_DIR/summary/';

CREATE EXTERNAL TABLE  IF NOT EXISTS imported_family_alleles
LIKE PARQUET '$FAMILY_PARQUET'
PARTITIONED BY (region_bin STRING, frequency_bin INT, coding_bin INT, family_bin INT)
STORED AS PARQUET
LOCATION '$HDFS_DIR/family/';

ALTER TABLE imported_summary_alleles RECOVER PARTITIONS;
ALTER TABLE imported_family_alleles RECOVER PARTITIONS;

" > /tmp/impala-import.sql

docker cp /tmp/impala-import.sql gpf_impala:/
docker exec -it gpf_impala impala-shell -f impala-import.sql

# -----------------------------------------------------------
# BIGQUERY INGESTION  
# - https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-parquet 
#
# 1) install gcloud & login with `gcloud auth login`
# 2) create a service account (json)
# 3) requires a google account, cloud project w/ permissions in storage, bigquery 
# 
# 4) Specify partioning and set to CUSTOM (mixed types: string int) 
# -  https://cloud.google.com/bigquery/docs/hive-partitioned-loads-gcs
# ex. 
# 	--hive_partitioning_mode=CUSTOM
#	--hive_partitioning_source_uri_prefix=gs://gpf/import/{region_bin:STRING}/{frequency_bin:INTEGER}/{family_bin:INTEGER} \
# -----------------------------------------------------------

REGION=us-east1
PROJECT=data-innov
DATASET=schema2

# Remove import directory 
gsutil rm -r -a gs://gpf/import

# Copy parquet files w/ directory structor to cloud storage (gs://) 
gsutil -m cp -r $IMPORT_DIR/meta.parquet gs://gpf/import/meta/
gsutil -m cp -r $IMPORT_DIR/*families.parquet gs://gpf/import/pedigree/
gsutil -m cp -r $IMPORT_DIR/summary/* gs://gpf/import/summary/ 
gsutil -m cp -r $IMPORT_DIR/family/* gs://gpf/import/family/ 

# Remove dataset (sync)
bq --sync rm -r -f --dataset $PROJECT:$DATASET  

# Create a new dataset 
bq --sync --location=$REGION mk --dataset $PROJECT:$DATASET

# BigQuery load uploaded parquet files
bq load --source_format=PARQUET --autodetect --replace=true --parquet_enable_list_inference=true \
	$DATASET.imported_meta gs://gpf/import/meta/*.parquet 

bq load --source_format=PARQUET --autodetect --replace=true --parquet_enable_list_inference=true \
	$DATASET.imported_pedigree gs://gpf/import/pedigree/*.parquet

bq load --source_format=PARQUET --autodetect --replace=true --parquet_enable_list_inference=true \
	--hive_partitioning_mode=CUSTOM \
	--hive_partitioning_source_uri_prefix=gs://gpf/import/summary/{region_bin:STRING}/{frequency_bin:INTEGER}/{coding_bin:INTEGER} \
 	$DATASET.imported_summary_alleles gs://gpf/import/summary/*.parquet 

bq load --source_format=PARQUET --autodetect --replace=true \
	--hive_partitioning_mode=CUSTOM \
	--hive_partitioning_source_uri_prefix=gs://gpf/import/family/{region_bin:STRING}/{frequency_bin:INTEGER}/{coding_bin:INTEGER}/{family_bin:INTEGER} \
	$DATASET.imported_family_alleles gs://gpf/import/family/*.parquet

SELECT DISTINCT 
    sa.bucket_index,
    sa.summary_index,
    fa.family_index,
    fa.family_id,
    sa.summary_variant_data,
    fa.family_variant_data
FROM
    `gcp-genotype-storage`.gpf_genotype_storage_dev_lubo.minimal_vcf_summary_alleles AS sa
JOIN
    `gcp-genotype-storage`.gpf_genotype_storage_dev_lubo.minimal_vcf_family_alleles AS fa
ON 
    (fa.summary_index = sa.summary_index AND
     fa.bucket_index = sa.bucket_index AND
     fa.allele_index = sa.allele_index)
JOIN UNNEST(sa.effect_gene)  as eg 
WHERE
    ( (  eg.effect_gene_symbols in (  'g1'  )  ) ) AND 
    ( (`chromosome` = 'foo' AND (-19996 <= `position`) AND (20015 >= COALESCE(`end_position`, `position`))) ) AND 
    ( sa.allele_index > 0 )




"
bq load --project_id gcp-genotype-storage \
    --source_format=PARQUET --autodetect --replace=true \
    --parquet_enable_list_inference=true \
 	gpf_genotype_storage_dev_lubo.bq_load_summary_alleles \
    gs://gcp-genotype-storage-input/dev_gcp_genotype_storage/gpf_genotype_storage_dev_lubo/minimal_vcf/summary_variants/*.parquet 
"
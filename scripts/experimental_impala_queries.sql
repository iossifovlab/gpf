SELECT variants.bucket_index, variants.summary_index, variants.allele_index, variants.variant_type, `position`, variants.family_id, pedigree.status, inheritance_in_members 
FROM data_hg38_production.SFARI_SPARK_WES_1_temp_variants as variants JOIN data_hg38_production.SFARI_SPARK_WES_1_temp_pedigree as pedigree 
WHERE
    ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) 
    AND ( (`chromosome` = 'chr14' AND ((`position` >= 21428145 AND `position` <= 21428145) ) )) 
    AND ( (  variants.effect_types in ( 'missense' )  ) ) 
    AND ( variants.allele_index > 0 ) AND ( variants.region_bin IN ('chr14_0') )
    AND variants.variant_in_members = pedigree.person_id 

SELECT variants.bucket_index, variants.summary_index, variants.variant_type, MIN(`position`), COUNT(DISTINCT variants.family_id), gpf_bit_or(pedigree.status) as status, gpf_or(BITAND(inheritance_in_members, 4)) 
FROM data_hg38_production.SFARI_SPARK_WES_1_temp_variants as variants JOIN data_hg38_production.SFARI_SPARK_WES_1_temp_pedigree as pedigree 
WHERE
    ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) 
    AND ( (`chromosome` = 'chr14' AND ((`position` >= 21428145 AND `position` <= 21428145) ) )) 
    AND ( (  variants.effect_types in ( 'missense' )  ) ) 
    AND ( variants.allele_index > 0 ) AND ( variants.region_bin IN ('chr14_0') )
    AND variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index, variant_type


SELECT variants.bucket_index, variants.summary_index, variants.variant_type, MIN(`position`), COUNT(DISTINCT variants.family_id), gpf_bit_or(pedigree.status) as status, gpf_or(BITAND(inheritance_in_members, 4)) 
FROM data_hg38_production.SFARI_SPARK_WES_1_temp_variants as variants JOIN data_hg38_production.SFARI_SPARK_WES_1_temp_pedigree as pedigree 
WHERE
    ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) 
    AND ( (`chromosome` = 'chr14' AND ((`position` >= 21428145 AND `position` <= 21428145) ) )) 
    AND ( (  variants.effect_types in ( 'missense' )  ) ) 
    AND ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) 
    AND ( variants.allele_index > 0 ) AND ( variants.region_bin IN ('chr14_0') )
    AND variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index, variant_type




CREATE EXTERNAL TABLE data_hg38_production_202005.SFARI_SSC_WGS_2_variants (                                                                                                                 
  bucket_index INT COMMENT 'Inferred from Parquet file.',                                                                                                                                    
  chromosome STRING COMMENT 'Inferred from Parquet file.',                                                                                                                                   
  `position` INT COMMENT 'Inferred from Parquet file.',                                                                                                                                      
  end_position INT COMMENT 'Inferred from Parquet file.',                                                                                                                                    
  effect_types STRING COMMENT 'Inferred from Parquet file.',                                                                                                                                                                                                                                                                                                                              
  effect_gene_symbols STRING COMMENT 'Inferred from Parquet file.',                                                                                                                          
  summary_index INT COMMENT 'Inferred from Parquet file.',                                                                                                                                   
  allele_index INT COMMENT 'Inferred from Parquet file.',                                                                                                                                    
  variant_type TINYINT COMMENT 'Inferred from Parquet file.',                                                                                                                                
  transmission_type TINYINT COMMENT 'Inferred from Parquet file.',                                                                                                                           
  reference STRING COMMENT 'Inferred from Parquet file.',                                                                                                                                    
  family_index INT COMMENT 'Inferred from Parquet file.',                                                                                                                                    
  family_id STRING COMMENT 'Inferred from Parquet file.',                                                                                                                                    
  is_denovo TINYINT COMMENT 'Inferred from Parquet file.',                                                                                                                                   
  variant_in_sexes TINYINT COMMENT 'Inferred from Parquet file.',                                                                                                                            
  variant_in_roles INT COMMENT 'Inferred from Parquet file.',                                                                                                                                
  inheritance_in_members SMALLINT COMMENT 'Inferred from Parquet file.',                                                                                                                     
  variant_in_members STRING COMMENT 'Inferred from Parquet file.',                                                                                                                           
  af_allele_freq FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                
  af_allele_count INT COMMENT 'Inferred from Parquet file.',                                                                                                                                 
  af_parents_called_percent FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                                                                                                                                                                                                  
  af_parents_called_count INT COMMENT 'Inferred from Parquet file.',                                                                                                                         
  family_variant_index FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                          
  phylop100way FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                  
  phylop20way FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                   
  phylop30way FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                   
  phylop7way FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                    
  phastcons100way FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                               
  phastcons20way FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                
  phastcons30way FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                
  phastcons7way FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                                                                                                                                                                                                              
  cadd_raw FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                                                                                                                                                                                                                   
  cadd_phred FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                                                                                                                                                                                                                 
  fitcons_i6_merged FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                             
  linsight FLOAT COMMENT 'Inferred from Parquet file.',
  fitcons2_e067 FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                 
  fitcons2_e068 FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                 
  fitcons2_e069 FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                 
  fitcons2_e070 FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                 
  fitcons2_e071 FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                 
  fitcons2_e072 FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                 
  fitcons2_e073 FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                 
  fitcons2_e074 FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                 
  fitcons2_e081 FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                 
  fitcons2_e082 FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                 
  mpc FLOAT COMMENT 'Inferred from Parquet file.',                                            
  ssc_freq FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                                      
  genome_gnomad_af FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                              
  genome_gnomad_af_percent FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                      
  genome_gnomad_ac FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                              
  genome_gnomad_an FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                              
  genome_gnomad_controls_ac FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                     
  genome_gnomad_controls_an FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                     
  genome_gnomad_controls_af FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                     
  genome_gnomad_non_neuro_ac FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                    
  genome_gnomad_non_neuro_an FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                    
  genome_gnomad_non_neuro_af FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                    
  genome_gnomad_controls_af_percent FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                             
  genome_gnomad_non_neuro_af_percent FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                            
  exome_gnomad_af FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                               
  exome_gnomad_af_percent FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                       
  exome_gnomad_ac FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                               
  exome_gnomad_an FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                               
  exome_gnomad_controls_ac FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                      
  exome_gnomad_controls_an FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                      
  exome_gnomad_controls_af FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                      
  exome_gnomad_non_neuro_ac FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                     
  exome_gnomad_non_neuro_an FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                     
  exome_gnomad_non_neuro_af FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                                     
  exome_gnomad_controls_af_percent FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                              
  exome_gnomad_non_neuro_af_percent FLOAT COMMENT 'Inferred from Parquet file.',                                                                                                             
  variant_data STRING COMMENT 'Inferred from Parquet file.'                                                                                                                                  
)                                                                                             
PARTITIONED BY (                                                                              
  region_bin STRING,                                                                          
  frequency_bin TINYINT,                                                                      
  coding_bin TINYINT,                                                                         
  family_bin TINYINT                                                                          
)                                                                                             
STORED AS PARQUET
LOCATION '/user/data_hg38_production_202005/studies/SFARI_SSC_WGS_2/variants' 
TBLPROPERTIES (
    'DO_NOT_UPDATE_STATS'='true', 
    'gpf_partitioning_coding_bin_coding_effect_types'='splice-site,frame-shift,nonsense,no-frame-shift-newStop,noStart,noEnd,missense,no-frame-shift,CDS,synonymous,coding_unknown,regulatory,3\'UTR,5\'UTR',
    'gpf_partitioning_family_bin_family_bin_size'='10',
    'gpf_partitioning_frequency_bin_rare_boundary'='5', 
    'gpf_partitioning_region_bin_chromosomes'='chr1, chr2, chr3, chr4, chr5, chr6, chr7, chr8, chr9, chr10, chr11, chr12, chr13, chr14, chr15, chr16, chr17, chr18, chr19, chr20, chr21, chr22, chrX',
    'gpf_partitioning_region_bin_region_length'='60000000');


ALTER TABLE data_hg38_production_202005.SFARI_SSC_WGS_2_variants RECOVER PARTITIONS;

REFRESH data_hg38_production_202005.SFARI_SSC_WGS_2_variants;




CREATE EXTERNAL TABLE data_hg19_production_202005.agre_wg_859_pedigree (
  family_id STRING COMMENT 'Inferred from Parquet file.',
  person_id STRING COMMENT 'Inferred from Parquet file.',
  dad_id STRING COMMENT 'Inferred from Parquet file.',
  mom_id STRING COMMENT 'Inferred from Parquet file.',
  sex TINYINT COMMENT 'Inferred from Parquet file.',
  status TINYINT COMMENT 'Inferred from Parquet file.',
  `role` INT COMMENT 'Inferred from Parquet file.',
  sample_id STRING COMMENT 'Inferred from Parquet file.',
  generated BOOLEAN COMMENT 'Inferred from Parquet file.',
  layout STRING COMMENT 'Inferred from Parquet file.',
  family_bin TINYINT COMMENT 'Inferred from Parquet file.'
)
STORED AS PARQUET
LOCATION 'hdfs://10.0.29.6:8020/user/data_hg19_production_202005/studies/AGRE_WG_859/pedigree';

REFRESH data_hg19_production_202005.agre_wg_859_pedigree;







CREATE EXTERNAL TABLE data_hg19_production_202005.sparkv3_pilot_pedigree (
  family_id STRING COMMENT 'Inferred from Parquet file.',
  person_id STRING COMMENT 'Inferred from Parquet file.',
  dad_id STRING COMMENT 'Inferred from Parquet file.',
  mom_id STRING COMMENT 'Inferred from Parquet file.',
  sex TINYINT COMMENT 'Inferred from Parquet file.',
  status TINYINT COMMENT 'Inferred from Parquet file.',
  `role` INT COMMENT 'Inferred from Parquet file.',
  sample_id STRING COMMENT 'Inferred from Parquet file.',
  generated BOOLEAN COMMENT 'Inferred from Parquet file.',
  layout STRING COMMENT 'Inferred from Parquet file.',
  family_bin TINYINT COMMENT 'Inferred from Parquet file.'
)
STORED AS PARQUET
LOCATION 'hdfs://10.0.29.6:8020/user/data_hg19_production_202005/studies/SPARKv3_pilot/pedigree';

REFRESH data_hg19_production_202005.sparkv3_pilot_pedigree;


CREATE EXTERNAL TABLE data_hg19_production_202005.svip_pedigree (
  family_id STRING COMMENT 'Inferred from Parquet file.',
  person_id STRING COMMENT 'Inferred from Parquet file.',
  dad_id STRING COMMENT 'Inferred from Parquet file.',
  mom_id STRING COMMENT 'Inferred from Parquet file.',
  sex TINYINT COMMENT 'Inferred from Parquet file.',
  status TINYINT COMMENT 'Inferred from Parquet file.',
  `role` INT COMMENT 'Inferred from Parquet file.',
  sample_id STRING COMMENT 'Inferred from Parquet file.',
  generated BOOLEAN COMMENT 'Inferred from Parquet file.',
  layout STRING COMMENT 'Inferred from Parquet file.',
  family_bin TINYINT COMMENT 'Inferred from Parquet file.',
  svip_summary_variables_genetic_status_16p STRING COMMENT 'Inferred from Parquet file.',
  diagnosis_summary_diagnosis_summary_svip_diagnosis_m1 STRING COMMENT 'Inferred from Parquet file.'
)
STORED AS PARQUET
LOCATION 'hdfs://10.0.29.6:8020/user/data_hg19_production_202005/studies/SVIP/pedigree';


REFRESH data_hg19_production_202005.svip_pedigree;



CREATE EXTERNAL TABLE data_hg19_production_202005.ssc_wg_510_pedigree (
  family_id STRING COMMENT 'Inferred from Parquet file.',
  person_id STRING COMMENT 'Inferred from Parquet file.',
  dad_id STRING COMMENT 'Inferred from Parquet file.',
  mom_id STRING COMMENT 'Inferred from Parquet file.',
  sex TINYINT COMMENT 'Inferred from Parquet file.',
  status TINYINT COMMENT 'Inferred from Parquet file.',
  `role` INT COMMENT 'Inferred from Parquet file.',
  sample_id STRING COMMENT 'Inferred from Parquet file.',
  generated BOOLEAN COMMENT 'Inferred from Parquet file.',
  layout STRING COMMENT 'Inferred from Parquet file.',
  family_bin TINYINT COMMENT 'Inferred from Parquet file.'
)
STORED AS PARQUET
LOCATION 'hdfs://10.0.29.6:8020/user/data_hg19_production_202005/studies/SSC_WG_510/pedigree';

REFRESH data_hg19_production_202005.ssc_wg_510_pedigree;



CREATE EXTERNAL TABLE data_hg19_production_202005.w1202s766e611_pedigree (
  family_id STRING COMMENT 'Inferred from Parquet file.',
  person_id STRING COMMENT 'Inferred from Parquet file.',
  dad_id STRING COMMENT 'Inferred from Parquet file.',
  mom_id STRING COMMENT 'Inferred from Parquet file.',
  sex TINYINT COMMENT 'Inferred from Parquet file.',
  status TINYINT COMMENT 'Inferred from Parquet file.',
  `role` INT COMMENT 'Inferred from Parquet file.',
  sample_id STRING COMMENT 'Inferred from Parquet file.',
  generated BOOLEAN COMMENT 'Inferred from Parquet file.',
  layout STRING COMMENT 'Inferred from Parquet file.',
  family_bin TINYINT COMMENT 'Inferred from Parquet file.',
  originalstudy STRING COMMENT 'Inferred from Parquet file.'
)
STORED AS PARQUET
LOCATION 'hdfs://10.0.29.6:8020/user/data_hg19_production_202005/studies/w1202s766e611/pedigree';

REFRESH data_hg19_production_202005.w1202s766e611_pedigree;




SELECT COUNT(DISTINCT variants.family_id), GROUP_CONCAT(DISTINCT CAST(pedigree.status AS STRING)), GROUP_CONCAT(DISTINCT CAST(BITAND(inheritance_in_members, 4) AS STRING))
FROM data_hg19_production_202005.SPARKv3_pilot_variants as variants
JOIN data_hg19_production_202005.sparkv3_pilot_pedigree as pedigree
WHERE
    ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND ( (variants.chromosome = '14' AND variants.`position` >= 21833353 AND variants.`position` <= 21925457) ) AND ( variants.region_bin IN ('14_0') ) AND
    variants.variant_in_members = pedigree.person_id
GROUP BY bucket_index, summary_index;


SELECT COUNT(DISTINCT variants.family_id), GROUP_CONCAT(DISTINCT CAST(pedigree.status AS STRING)), GROUP_CONCAT(DISTINCT CAST(BITAND(inheritance_in_members, 4) AS STRING))
FROM data_hg19_production_202005.SSC_WG_510_variants as variants
JOIN data_hg19_production_202005.SSC_WG_510_pedigree as pedigree
WHERE
    ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND ( (variants.chromosome = '14' AND variants.`position` >= 21833353 AND variants.`position` <= 21925457) ) AND ( variants.region_bin IN ('14_0') ) AND
    variants.variant_in_members = pedigree.person_id
GROUP BY bucket_index, summary_index;



SELECT COUNT(DISTINCT variants.family_id), GROUP_CONCAT(DISTINCT CAST(pedigree.status AS STRING)), GROUP_CONCAT(DISTINCT CAST(BITAND(inheritance_in_members, 4) AS STRING))
FROM data_hg19_production_202005.AGRE_WG_859_variants as variants
JOIN data_hg19_production_202005.AGRE_WG_859_pedigree as pedigree
WHERE
    ( (  variants.effect_gene_symbols in (  'DMD'  )  ) ) AND ( (variants.chromosome = 'X' AND variants.`position` >= 31117345 AND variants.`position` <= 33377726) ) AND ( variants.region_bin IN ('X_0') ) AND
    variants.variant_in_members = pedigree.person_id
GROUP BY bucket_index, summary_index;






SELECT variants.bucket_index, variants.summary_index,
     COUNT(DISTINCT variants.family_id), gpf_bit_or(pedigree.status), GROUP_CONCAT(DISTINCT CAST(pedigree.status AS STRING)), gpf_or(BITAND(inheritance_in_members, 4)) 
FROM 
  data_hg19_production_202005.IossifovWE2014_variants as variants 
  JOIN data_hg19_production_202005.IossifovWE2014_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND ( (`chromosome` = '14' AND `position` >= 21833353 AND `position` <= 21925457) ) 
  AND variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index



SELECT COUNT(DISTINCT variants.family_id), GROUP_CONCAT(DISTINCT CAST(pedigree.status AS STRING)), gpf_bit_or(pedigree.status), GROUP_CONCAT(DISTINCT CAST(BITAND(inheritance_in_members, 4) AS STRING))
FROM data_hg19_production_202005.SSC_WG_510_variants as variants
JOIN data_hg19_production_202005.SSC_WG_510_pedigree as pedigree
WHERE
    ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND ( (variants.chromosome = '14' AND variants.`position` >= 21833353 AND variants.`position` <= 21925457) ) AND ( variants.region_bin IN ('14_0') ) AND
    variants.variant_in_members = pedigree.person_id
GROUP BY bucket_index, summary_index LIMIT 10;


SELECT COUNT(DISTINCT variants.family_id), GROUP_CONCAT(DISTINCT CAST(pedigree.status AS STRING)), gpf_bit_or(pedigree.status), GROUP_CONCAT(DISTINCT CAST(BITAND(inheritance_in_members, 4) AS STRING)), gpf_or(BITAND(inheritance_in_members, 4))
FROM data_hg19_production_202005.AGRE_WG_859_variants as variants
JOIN data_hg19_production_202005.AGRE_WG_859_pedigree as pedigree
WHERE
    ( (  variants.effect_gene_symbols in (  'DMD'  )  ) ) AND ( (variants.chromosome = 'X' AND variants.`position` >= 31117345 AND variants.`position` <= 33377726) ) AND ( variants.region_bin IN ('X_0') ) AND
    variants.variant_in_members = pedigree.person_id
GROUP BY bucket_index, summary_index;





SELECT bucket_index, summary_index, allele_index, chromosome, `position`, end_position, variant_type, reference, family_id, genome_gnomad_af_percent 
FROM data_hg19_production_202005.SSC_WG_510_variants 
WHERE
    ( (`chromosome` = '14' AND `position` >= 21861156 AND `position` <= 21861217) ) 
    AND ( BITAND(150, inheritance_in_members) != 0 ) 
    AND ( (genome_gnomad_af_percent <= 0.0014344821771817549 or genome_gnomad_af_percent is null) ) 
    AND ( region_bin IN ('14_0') );





SELECT variants.bucket_index, variants.summary_index, variants.family_id, gpf_bit_or(pedigree.status)
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants as variants JOIN data_hg38_production_202005.SSC_WG38_CSHL_2380_pedigree as pedigree 
WHERE
    ( (`chromosome` = 'chr14' AND `position` >= 21394746 AND `position` <= 21398626) ) AND 
    ( (  variants.effect_types in (  'missense'  )  ) ) AND 
    ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
    ( (variants.ssc_freq <= 0.4734866617797162 or variants.ssc_freq is null) ) AND 
    ( variants.allele_index > 0 ) AND 
    ( variants.coding_bin = 1 ) AND 
    ( variants.region_bin IN ('chr14_0') ) AND 
    variants.variant_in_members = pedigree.person_id AND 
    pedigree.status IN (2,1)
GROUP BY bucket_index, summary_index, family_id;



SELECT variants.bucket_index, variants.summary_index, variants.family_id, gpf_bit_or(pedigree.status) as variant_in_status
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants as variants JOIN data_hg38_production_202005.SSC_WG38_CSHL_2380_pedigree as pedigree 
WHERE
  ( (`chromosome` = 'chr14' AND `position` >= 21385194 AND `position` <= 21437298) ) AND 
  ( (  variants.effect_types in (  'missense'  )  ) ) AND 
  ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( (variants.ssc_freq <= 100 or variants.ssc_freq is null) ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.coding_bin = 1 ) AND 
  ( variants.region_bin IN ('chr14_0') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index, family_id
HAVING   gpf_bit_or(pedigree.status) = 1;


SELECT variants.bucket_index, variants.summary_index, variants.family_id, variants.variant_data as variant_data / gpf_first(variants.variant_data) as variant_data
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants as variants JOIN data_hg38_production_202005.SSC_WG38_CSHL_2380_pedigree as pedigree 
WHERE
  ( (`chromosome` = 'chr14' AND `position` >= 21394240 AND `position` <= 21394473) ) AND 
  ( (  variants.effect_types in (  'missense'  )  ) ) AND 
  ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( (variants.ssc_freq <= 0.015520677159789525 or variants.ssc_freq is null) ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.coding_bin = 1 ) AND 
  ( variants.region_bin IN ('chr14_0') ) AND variants.variant_in_members = pedigree.person_id
GROUP BY bucket_index, summary_index, family_id
HAVING   gpf_bit_or(pedigree.status) = 1;




SELECT bucket_index, summary_index, family_id
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants 
WHERE
  ( (`chromosome` = 'chr5' AND `position` >= 14652278 AND `position` <= 133020534) ) AND 
  ( (  effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'noStart' , 'noEnd' , 'no-frame-shift' , '3\'UTR' , '5\'UTR' , 'CDS'  )  ) ) AND 
  (effect_gene_symbols in ('SNORD141A')) AND
  ( BITAND(150, inheritance_in_members) != 0 ) AND 
  ( (ssc_freq <= 100 or ssc_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( coding_bin = 1 ) AND 
  ( region_bin IN ('chr5_0','chr5_1','chr5_2') )



SELECT bucket_index, summary_index, chromosome, `position`, family_id, inheritance_in_members FROM data_hg38_production_202005.SPARK_WE38_CSHL_5953_variants 
WHERE
  ( (`chromosome` = 'chr14' AND `position` >= 21393502 AND `position` <= 21393518) ) AND 
  ( (  effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'noStart' , 'noEnd' , 'no-frame-shift' , '3\'UTR' , '5\'UTR' , 'CDS'  )  ) ) AND 
  ( BITAND(150, inheritance_in_members) != 0 ) AND 
  ( (ssc_freq <= 0.018212768885494165 or ssc_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( coding_bin = 1 ) AND 
  ( region_bin IN ('chr14_0') );

SELECT bucket_index, summary_index, chromosome, `position`, family_id, inheritance_in_members FROM data_hg38_production_202005.SPARK_WE38_CSHL_5953_variants 
WHERE
  ( (`chromosome` = 'chr14' AND `position` >= 21393502 AND `position` <= 21393518) ) AND 
  ( (  effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'noStart' , 'noEnd' , 'no-frame-shift' , '3\'UTR' , '5\'UTR' , 'CDS'  )  ) ) AND 
  ( (ssc_freq <= 0.018212768885494165 or ssc_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( coding_bin = 1 ) AND 
  ( region_bin IN ('chr14_0') );




SELECT bucket_index, summary_index, chromosome, `position`, effect_types, family_id 
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants 
WHERE
  ( (`chromosome` = 'chr14' AND `position` >= 21385194 AND `position` <= 21437298) ) AND 
  ( (  effect_types in (  'noStart' , 'noEnd' , 'no-frame-shift' , '3\'UTR' , '5\'UTR' , 'CDS'  )  ) ) AND 
  ( BITAND(150, inheritance_in_members) != 0 ) AND 
  ( (ssc_freq <= 100 or ssc_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( coding_bin = 1 ) AND 
  ( region_bin IN ('chr14_0') );


SELECT bucket_index, summary_index, chromosome, `position`, effect_types, family_id, coding_bin 
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants 
WHERE
  ( (`chromosome` = 'chr14' AND `position` >= 21385194 AND `position` <= 21437298) ) AND 
  ( (  effect_types in (  'noStart' , 'noEnd' , 'no-frame-shift' , '3\'UTR' , '5\'UTR' , 'CDS'  )  ) ) AND 
  ( BITAND(150, inheritance_in_members) != 0 ) AND 
  ( (ssc_freq <= 100 or ssc_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( region_bin IN ('chr14_0') );


SELECT bucket_index, summary_index, allele_index, chromosome, `position`, variant_type, reference, family_id, effect_types, effect_gene_symbols, variant_in_members, inheritance_in_members
FROM data_hg38_production_202005.sfari_spark_wes_1_consortium_variants 
WHERE
  ( (`chromosome` = 'chr14' AND `position` >= 21393689 AND `position` <= 21393701) ) AND 
  ( (  effect_types in (  'missense' , 'synonymous' , 'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS'  )  ) ) AND 
  ( BITAND(150, inheritance_in_members) != 0 ) AND ( BITAND(8, inheritance_in_members) = 0 ) AND 
  ( (ssc_freq <= 0.032783757946796464 or ssc_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( region_bin IN ('chr14_0') );




SELECT variants.bucket_index, variants.summary_index, COUNT(DISTINCT variants.family_id), gpf_bit_or(pedigree.status), gpf_or(BITAND(inheritance_in_members, 4)) 
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants as variants JOIN data_hg38_production_202005.SSC_WG38_CSHL_2380_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'SNORD141A'  )  ) ) AND 
  ( (`chromosome` = 'chr5' AND `position` >= 14632278 AND `position` <= 14672382) OR 
    (`chromosome` = 'chr6' AND `position` >= 73498245 AND `position` <= 73538438) OR 
    (`chromosome` = 'chr9' AND `position` >= 133000430 AND `position` <= 133040534) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.region_bin IN ('chr5_0','chr6_1','chr9_2') );


SELECT variants.bucket_index, variants.summary_index, gpf_bit_or(pedigree.status), gpf_or(BITAND(inheritance_in_members, 4)) 
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants as variants JOIN data_hg38_production_202005.SSC_WG38_CSHL_2380_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'SNORD141A'  )  ) ) AND 
  ( (`chromosome` = 'chr5' AND `position` >= 14632278 AND `position` <= 14672382) OR 
    (`chromosome` = 'chr6' AND `position` >= 73498245 AND `position` <= 73538438) OR 
    (`chromosome` = 'chr9' AND `position` >= 133000430 AND `position` <= 133040534) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'nonsense' , 'frame-shift' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS', 'non-coding'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( variants.allele_index > 0 ) AND ( variants.coding_bin = 1 ) AND 
  ( variants.region_bin IN ('chr5_0','chr6_1','chr9_2') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index;

SELECT variants.bucket_index, variants.summary_index, gpf_bit_or(pedigree.status), gpf_or(BITAND(inheritance_in_members, 4)), GROUP_CONCAT(variants.effect_types) 
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants as variants JOIN data_hg38_production_202005.SSC_WG38_CSHL_2380_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'SNORD141A'  )  ) ) AND 
  ( (`chromosome` = 'chr5' AND `position` >= 14632278 AND `position` <= 14672382) OR 
    (`chromosome` = 'chr6' AND `position` >= 73498245 AND `position` <= 73538438) OR 
    (`chromosome` = 'chr9' AND `position` >= 133000430 AND `position` <= 133040534) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( variants.allele_index > 0 ) AND ( variants.coding_bin = 1 ) AND 
  ( variants.region_bin IN ('chr5_0','chr6_1','chr9_2') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index;


SELECT variants.bucket_index, variants.summary_index 
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants as variants JOIN data_hg38_production_202005.SSC_WG38_CSHL_2380_pedigree as pedigree 
WHERE
  ( (`chromosome` = 'chr5' AND `position` >= 14652278 AND `position` <= 14652382) OR (`chromosome` = 'chr6' AND `position` >= 73518245 AND `position` <= 73518438) OR (`chromosome` = 'chr9' AND `position` >= 133020430 AND `position` <= 133020534) ) AND 
  ( (  variants.effect_gene_symbols in (  'SNORD141A'  )  ) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( (variants.ssc_freq <= 100 or variants.ssc_freq is null) ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.coding_bin = 1 ) AND 
  ( variants.region_bin IN ('chr5_0','chr6_1','chr9_2') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id 
HAVING gpf_bit_or(pedigree.status) IN (1, 2, 3);







SELECT variants.bucket_index, variants.summary_index
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants as variants JOIN data_hg38_production_202005.SSC_WG38_CSHL_2380_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'SNORD141A'  )  ) ) AND 
  ( (`chromosome` = 'chr5' AND `position` >= 14632278 AND `position` <= 14672382) OR 
    (`chromosome` = 'chr6' AND `position` >= 73498245 AND `position` <= 73538438) OR 
    (`chromosome` = 'chr9' AND `position` >= 133000430 AND `position` <= 133040534) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.region_bin IN ('chr5_0','chr6_1','chr9_2') ) AND 
  variants.variant_in_members = pedigree.person_id 
  GROUP BY bucket_index, summary_index




SELECT gpf_first(variants.chromosome), gpf_first(variants.variant_data)
FROM data_hg38_production_202005.SSC_WG38_CSHL_2380_variants as variants JOIN data_hg38_production_202005.SSC_WG38_CSHL_2380_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = 'chr14' AND `position` >= 21385194 AND `position` <= 21437298) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND 
  ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( (variants.ssc_freq <= 100 or variants.ssc_freq is null) ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.coding_bin = 1 ) AND 
  ( variants.region_bin IN ('chr14_0') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id
HAVING gpf_bit_or(pedigree.status) IN (3, 2, 1);



SELECT variants.bucket_index, variants.summary_index, gpf_first(variants.chromosome), MIN(variants.`position`), MIN(variants.end_position), MIN(variants.variant_type), gpf_first(variants.reference), variants.family_id, gpf_first(variants.variant_data) 
FROM data_hg38_production_202005.AGRE_WG38_859_variants as variants JOIN data_hg38_production_202005.AGRE_WG38_859_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = 'chr14' AND `position` >= 21385194 AND `position` <= 21437298) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND 
  ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( false ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.coding_bin = 1 ) AND 
  ( variants.region_bin IN ('chr14_0') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id 
HAVING gpf_bit_or(pedigree.status) IN (3, 2, 1)


SELECT variants.bucket_index, variants.summary_index, gpf_first(variants.chromosome), MIN(variants.`position`), MIN(variants.end_position), MIN(variants.variant_type), gpf_first(variants.reference), variants.family_id, gpf_first(variants.variant_data) 
FROM data_hg38_production_202005.sfari_spark_wes_1_consortium_variants as variants JOIN data_hg38_production_202005.sfari_spark_wes_1_consortium_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = 'chr14' AND `position` >= 21385194 AND `position` <= 21437298) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( (variants.ssc_freq <= 100 or variants.ssc_freq is null) ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.region_bin IN ('chr14_0') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id 
HAVING gpf_bit_or(pedigree.status) IN (3, 2, 1)


SELECT variants.bucket_index, variants.summary_index
FROM data_hg38_production_202005.sfari_spark_wes_1_consortium_variants as variants JOIN data_hg38_production_202005.sfari_spark_wes_1_consortium_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = 'chr14' AND `position` >= 21385194 AND `position` <= 21437298) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( (variants.ssc_freq <= 100 or variants.ssc_freq is null) ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.region_bin IN ('chr14_0') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id 
HAVING gpf_bit_or(pedigree.status) IN (3, 2, 1)


SELECT variants.bucket_index, variants.summary_index
FROM data_hg38_production_202005.sfari_spark_wes_1_consortium_variants as variants JOIN data_hg38_production_202005.sfari_spark_wes_1_consortium_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (  variants.chromosome = 'chr14' AND variants.`position` >= 21385194 AND variants.`position` <= 21437298) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS'  )  ) ) AND 
  ( (variants.ssc_freq <= 100 or variants.ssc_freq is null) ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.region_bin IN ('chr14_0') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id 
HAVING gpf_bit_or(pedigree.status) IN (3, 2, 1)


SELECT variants.bucket_index, variants.summary_index, variants.variant_in_members, variants.allele_index, variants.ssc_freq, variants.region_bin, `chromosome`, `position`
FROM data_hg38_production_202005.sfari_spark_wes_1_consortium_variants as variants 
LIMIT 10;





SELECT variants.bucket_index, variants.summary_index, COUNT(DISTINCT variants.family_id), gpf_bit_or(pedigree.status) 
FROM data_hg38_production_202005.SFARI_SPARK_WGS_1_variants as variants JOIN data_hg38_production_202005.SFARI_SPARK_WGS_1_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND ( (`chromosome` = 'chr14' AND `position` >= 21365194 AND `position` <= 21457298) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.region_bin IN ('chr14_0') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index;


SELECT bucket_index, summary_index, chromosome, `position`, variant_type, family_id 
FROM data_hg38_production_202005.SFARI_SPARK_WES_1_variants 
WHERE
  ( (  effect_gene_symbols in (  'CHD8'  )  ) ) AND ( (`chromosome` = 'chr14' AND `position` >= 21385194 AND `position` <= 21437298) ) AND 
  ( (  effect_types in          (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS'  )  ) ) AND 
  ( BITAND(8, inheritance_in_members) = 0 AND BITAND(32, inheritance_in_members) = 0 ) AND ( BITAND(150, inheritance_in_members) != 0 ) AND 
  ( (ssc_freq <= 100 or ssc_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( region_bin IN ('chr14_0') )


SELECT bucket_index, summary_index, chromosome, `position`, end_position, variant_type, reference, family_id 
FROM data_hg38_production_202005.SFARI_SPARK_WGS_1_variants 
WHERE
  ( (  effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = 'chr14' AND `position` >= 21393932 AND `position` <= 21394045) ) AND 
  ( (  effect_types in (  'synonymous'  )  ) ) AND 
  ( BITAND(8, inheritance_in_members) = 0 AND BITAND(32, inheritance_in_members) = 0 ) AND ( BITAND(150, inheritance_in_members) != 0 ) AND 
  ( (ssc_freq <= 0.03408583939688799 or ssc_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( region_bin IN ('chr14_0') )



SELECT variants.bucket_index, variants.summary_index, gpf_first(chromosome), MIN(`position`), COUNT(DISTINCT variants.family_id), gpf_bit_or(pedigree.status) 
FROM data_hg38_production_202005.SFARI_SPARK_WGS_1_variants as variants JOIN data_hg38_production_202005.SFARI_SPARK_WGS_1_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = 'chr14' AND `position` >= 21393932 AND `position` <= 21394045) ) AND 
  ( (  variants.effect_types in (  'synonymous'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.region_bin IN ('chr14_0') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index;



SELECT bucket_index, summary_index, chromosome, `position`, end_position, variant_type, reference, family_id 
FROM data_hg38_production_202005.SFARI_SPARK_WGS_1_variants 
WHERE
  ( (  effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = 'chr14' AND `position` >= 21393992 AND `position` <= 21393992) ) AND 
  ( (  effect_types in (  'synonymous'  )  ) ) AND 
  ( BITAND(8, inheritance_in_members) = 0 AND BITAND(32, inheritance_in_members) = 0 ) AND ( BITAND(150, inheritance_in_members) != 0 ) AND 
  ( (ssc_freq <= 0.03408583939688799 or ssc_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( region_bin IN ('chr14_0') );


SELECT bucket_index, summary_index, chromosome, `position`, end_position, variant_type, reference, family_id 
FROM data_hg38_production_202005.SFARI_SPARK_WES_1_variants 
WHERE
  ( (  effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = 'chr14' AND `position` >= 21393992 AND `position` <= 21393992) ) AND 
  ( (  effect_types in (  'synonymous'  )  ) ) AND 
  ( BITAND(8, inheritance_in_members) = 0 AND BITAND(32, inheritance_in_members) = 0 ) AND ( BITAND(150, inheritance_in_members) != 0 ) AND 
  ( (ssc_freq <= 0.03408583939688799 or ssc_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( region_bin IN ('chr14_0') );



SELECT variants.bucket_index, variants.summary_index, gpf_first(variants.chromosome), MIN(variants.`position`), MIN(variants.end_position), MIN(variants.variant_type), gpf_first(variants.reference), variants.family_id
FROM data_hg19_production_202005.SPARKv3_pilot_variants as variants JOIN data_hg19_production_202005.SPARKv3_pilot_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = '14' AND `position` >= 21854022 AND `position` <= 21854022) ) AND 
  ( (  variants.effect_types in (  'missense'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( (variants.genome_gnomad_af_percent >= 0.002411158224232163 AND variants.genome_gnomad_af_percent <= 0.20464154880884206) ) AND 
  ( variants.allele_index > 0 ) AND ( variants.region_bin IN ('14_0') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id 
HAVING gpf_bit_or(pedigree.status) IN (1);



SELECT variants.bucket_index, variants.summary_index, gpf_first(variants.chromosome), MIN(variants.`position`), MIN(variants.end_position), MIN(variants.variant_type), gpf_first(variants.reference), variants.family_id
FROM data_hg19_production_202005.SPARKv3_pilot_variants as variants JOIN data_hg19_production_202005.SPARKv3_pilot_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = '14' AND `position` >= 21854022 AND `position` <= 21854022) ) AND 
  ( variants.allele_index > 0 ) AND ( variants.region_bin IN ('14_0') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id;




select chromosome, `position`, variant_type, summary_index, allele_index, family_index, family_id, variant_in_sexes, variant_in_roles, variant_in_members, inheritance_in_members,
    bitand(inheritance_in_members, 4) as denovo,
    bitand(inheritance_in_members, 8) as possible_denovo,
    bitand(inheritance_in_members, 16) as omission,
    bitand(inheritance_in_members, 32) as possible_omission,
    bitand(inheritance_in_members, 64) as other,
    bitand(inheritance_in_members, 128) as missing,
    bitand(inheritance_in_members, 256) as unknown_inheritance
from sfari_ssc_wgs_2b_variants;


SELECT bucket_index, summary_index, chromosome, `position`, end_position, variant_type, reference, family_id FROM data_hg38_production.SFARI_SSC_WGS_2b_variants 
WHERE
  ( (  effect_types in (  'nonsense' , 'frame-shift' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'no-frame-shift' , 'noStart' , 'noEnd' , 'synonymous' , 'non-coding' , 'intron' , 'non-coding-intron' , 'intergenic' , '3\'UTR' , '3\'UTR-intron' , '5\'UTR' , '5\'UTR-intron' , 'CNV+' , 'CNV-'  )  ) ) 
  AND ( BITAND(8, inheritance_in_members) = 0 AND BITAND(32, inheritance_in_members) = 0 ) AND ( BITAND(134, inheritance_in_members) != 0 ) 
  AND ( (((BITAND(variant_type, 4) != 0)) OR ((BITAND(variant_type, 2) != 0))) OR ((BITAND(variant_type, 1) != 0)) ) 
  AND ( (af_allele_count <= 1 or af_allele_count is null) ) AND ( allele_index > 0 ) AND ( frequency_bin = 0 OR frequency_bin = 1 );

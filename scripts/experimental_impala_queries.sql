SELECT variants.bucket_index, variants.summary_index, variants.chromosome, variants.`position`, variants.end_position, variants.variant_type, variants.reference, variants.family_id, variants.variant_data, variants.extra_attributes 
FROM data_hg38_seqclust.SFARI_ABN_WGS_V1_variants as variants JOIN data_hg38_seqclust.SFARI_ABN_WGS_V1_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = 'chr14' AND ((`position` >= 21365194 AND `position` <= 21457298) OR (COALESCE(end_position, -1) >= 21365194 AND COALESCE(end_position, -1) <= 21457298) OR (21365194 >= `position` AND 21457298 <= COALESCE(end_position, -1)))) ) AND 
  ( (  variants.effect_types in (  'nonsense' , 'frame-shift' , 'splice-site' , 'no-frame-shift-newStop' , 'missense'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(406, variants.inheritance_in_members) != 0 ) AND 
  ( (((BITAND(variants.variant_type, 4) != 0)) OR ((BITAND(variants.variant_type, 2) != 0))) OR ((BITAND(variants.variant_type, 1) != 0)) ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.coding_bin = 1 ) AND 
  ( variants.region_bin IN ('chr14_0') )AND 
  ((pedigree.asd_status_label = "ASD confirmed" ) OR (pedigree.asd_status_label = "ASD under review" ) OR (pedigree.asd_status_label = "unspecified" )) AND 
  variants.variant_in_members = pedigree.person_id


SELECT bucket_index, summary_index, chromosome, `position`, end_position, variant_type, reference, family_id, variant_data, extra_attributes 
FROM data_hg38_seqclust.SFARI_ABN_WGS_V1_variants                                                                                              
WHERE                                                                                                                                                                                                                                                                                                                                                                            
  ( (  effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = 'chr14' AND ((`position` >= 21385194 AND `position` <= 21437298) OR (COALESCE(end_position, -1) >= 21385194 AND COALESCE(end_position, -1) <= 21437298) OR (21385194 >= `position` AND 21437298 <= COALESCE(end_position, -1)))) ) AND 
  ( (  effect_types in (  'frame-shift' , 'nonsense' , 'splice-site', 'no-frame-shift-newStop' , 'missense'  )  ) ) AND 
  ( BITAND(8, inheritance_in_members) = 0 AND BITAND(32, inheritance_in_members) = 0 ) AND ( BITAND(406, inheritance_in_members) != 0 ) AND 
  ( (((((BITAND(variant_type, 16) != 0)) OR ((BITAND(variant_type, 32) != 0))) OR ((BITAND(variant_type, 2) != 0))) OR ((BITAND(variant_type, 1) != 0))) OR ((BITAND(variant_type, 4) != 0))) AND 
  ( (genome_gnomad_v3_af_percent <= 100 or genome_gnomad_v3_af_percent is null) ) AND 
  ( allele_index > 0 ) AND 
  ( coding_bin = 1 ) AND 
  ( region_bin IN ('chr14_0') )




SELECT 

variants.bucket_index,
variants.chromosome,
variants.`position`,
variants.end_position,
variants.effect_types,
variants.effect_gene_symbols,
variants.summary_index,
variants.allele_index,
variants.variant_type,
variants.transmission_type,
variants.reference,
variants.family_index,
variants.family_id,
variants.is_denovo,
variants.variant_in_sexes,
variants.variant_in_roles,
variants.inheritance_in_members,
variants.variant_in_members,
pedigree.primaryphenotype,
pedigree.person_id

FROM data_hg38_seqclust.denovo_db_liftover_variants as variants JOIN data_hg38_seqclust.denovo_db_liftover_pedigree as pedigree 
WHERE
  ( (  variants.effect_types in (  'nonsense' , 'frame-shift' , 'splice-site' , 'no-frame-shift-newStop'  )  ) ) 
  AND ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) 
  AND ( BITAND(4, variants.inheritance_in_members) != 0 ) 
  AND ( (((BITAND(variants.variant_type, 4) != 0)) OR ((BITAND(variants.variant_type, 1) != 0))) OR ((BITAND(variants.variant_type, 2) != 0)) ) 
  AND ( variants.allele_index > 0 )
  AND ((pedigree.primaryphenotype = "control" )) AND variants.variant_in_members = pedigree.person_id


--- AGP
SELECT 
  COUNT(DISTINCT bucket_index, summary_index, family_index)
FROM data_hg38_seqclust.sfari_spark_wes_1_consortium_variants 
WHERE                         
  ( (  effect_gene_symbols in (  'KMT2C'  )  ) ) AND 
  ( (`chromosome` = 'chr7' AND ((`position` >= 152114925 AND `position` <= 152456005) OR (COALESCE(end_position, -1) >= 152114925 AND COALESCE(end_position, -1) <= 152456005) OR (152114925 >= `position` AND 152456005 <= COALESCE(end_position, -1)))) ) AND 
  ( (  effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop'  )  ) ) AND 
  ( BITAND(8, inheritance_in_members) = 0 AND BITAND(32, inheritance_in_members) = 0 ) AND ( BITAND(134, inheritance_in_members) != 0 ) AND 
  ( (af_allele_freq <= 1.0 or af_allele_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( frequency_bin = 1 OR frequency_bin = 2 OR frequency_bin = 0 ) AND 
  ( region_bin IN ('chr7_5') ) ;


--- genotype browser

SELECT 
  COUNT(DISTINCT bucket_index, summary_index, family_index)
FROM data_hg38_seqclust.sfari_spark_wes_1_consortium_variants                                                                      
WHERE                                                                                                                                                                                                                                                                                                                                                                            
  ( (  effect_gene_symbols in (  'KMT2C'  )  ) ) AND 
  ( (`chromosome` = 'chr7' AND ((`position` >= 152114925 AND `position` <= 152456005) OR (COALESCE(end_position, -1) >= 152114925 AND COALESCE(end_position, -1) <= 152456005) OR (152114925 >= `position` AND 152456005 <= COALESCE(end_position, -1)))) ) AND 
  ( (  effect_types in (  'nonsense' , 'frame-shift' , 'splice-site' , 'no-frame-shift-newStop'  )  ) ) AND 
  ( BITAND(8, inheritance_in_members) = 0 AND BITAND(32, inheritance_in_members) = 0 ) AND ( BITAND(134, inheritance_in_members) != 0 ) AND 
  ( ((((BITAND(variant_in_roles, 128) != 0)) AND ((NOT ((BITAND(variant_in_roles, 256) != 0))))) OR (((NOT ((BITAND(variant_in_roles, 128) != 0)))) AND ((BITAND(variant_in_roles, 256) != 0)))) OR (((BITAND(variant_in_roles, 128) != 0)) AND ((BITAND(variant_in_roles, 256) != 0))) ) AND 
  ( (af_allele_freq <= 1 or af_allele_freq is null) ) AND 
  ( allele_index > 0 ) AND 
  ( frequency_bin = 2 OR frequency_bin = 0 OR frequency_bin = 1 ) AND 
  ( region_bin IN ('chr7_5') );









CREATE TABLE IF NOT EXISTS gpf_variant_db.sparkv3_pilot_summary_alleles (
  `bucket_index` int, 
  `chromosome` string, 
  `position` int, 
  `end_position` int, 
  `effect_types` string, 
  `effect_gene_symbols` string, 
  `summary_index` int, 
  `allele_index` int, 
  `variant_type` tinyint, 
  `transmission_type` tinyint, 
  `reference` string, 
  `af_allele_freq` float, 
  `af_allele_count` int, 
  `af_parents_called_percent` float, 
  `af_parents_called_count` int
) 
PARTITIONED BY (
  `region_bin` string, 
  `frequency_bin` tinyint
) 
STORED AS PARQUET


INSERT INTO gpf_variant_db.sparkv3_pilot_summary_alleles 
( 
  `bucket_index`,
  `position`,
  `summary_index`,
  `allele_index`,
  `effect_types`,
  `effect_gene_symbols`,
  `variant_type`,
  `transmission_type`,
  `chromosome`,
  `end_position`,
  `reference`,
  `af_allele_freq`,
  `af_allele_count`,
  `af_parents_called_percent`,
  `af_parents_called_count`
) 
PARTITION (`region_bin`, `frequency_bin`)
SELECT 
  `bucket_index`, 
  `position`, 
  `summary_index`, 
  `allele_index`, 
  `effect_types`, 
  `effect_gene_symbols`, 
  `variant_type`, 
  `transmission_type`, 
  MIN(`chromosome`), 
  MIN(`end_position`), 
  MIN(`reference`), 
  MIN(`af_allele_freq`), 
  MIN(`af_allele_count`), 
  MIN(`af_parents_called_percent`), 
  MIN(`af_parents_called_count`),
  `region_bin`,
  `frequency_bin`
FROM gpf_variant_db.sparkv3_pilot_variants as variants 
GROUP BY `bucket_index`, `position`, `summary_index`, `allele_index`, `effect_types`, `effect_gene_symbols`, `variant_type`, `transmission_type`, `region_bin`, `frequency_bin`


CREATE EXTERNAL TABLE gpf_variant_db.sparkv3_pilot_family_allele (
  `bucket_index` INT,  
  `summary_index` INT,
  `family_index` INT,  
  `transmission_type` TINYINT,  
  `family_id` STRING,  
  `is_denovo` TINYINT,  
  `variant_in_sexes` TINYINT,  
  `variant_in_roles` INT,  
  `inheritance_in_members` SMALLINT,  
  `variant_in_members` STRING  
) 
PARTITIONED BY (
  region_bin string, 
  frequency_bin tinyint, 
  family_bin tinyint
) 
STORED AS PARQUET 


INSERT INTO gpf_variant_db.sparkv3_pilot_family_allele 
PARTITION (region_bin, frequency_bin, family_bin) 
SELECT  
  `bucket_index`,
  `summary_index`,  
  `family_index`,
  `transmission_type`,
  `family_id`,  
  `is_denovo`,  
  `variant_in_sexes`,  
  `variant_in_roles`,  
  `inheritance_in_members`,  
  `variant_in_members`, 
  `region_bin`, 
  `frequency_bin`, 
  `family_bin` 
FROM gpf_variant_db.sparkv3_pilot_variants;


SELECT 
  `bucket_index`, 
  `position`, 
  `summary_index`, 
  `allele_index`, 
  `effect_types`, 
  `effect_gene_symbols`, 
  `variant_type`, 
  `transmission_type`, 
  COUNT(DISTINCT `chromosome`), 
  COUNT(DISTINCT `end_position`), 
  COUNT(DISTINCT `reference`), 
  COUNT(DISTINCT `af_allele_freq`), 
  COUNT(DISTINCT `af_allele_count`), 
  COUNT(DISTINCT `af_parents_called_percent`), 
  COUNT(DISTINCT `af_parents_called_count`),
  `region_bin`,
  `frequency_bin`
FROM gpf_variant_db.sparkv3_pilot_variants as variants 
GROUP BY `bucket_index`, `position`, `summary_index`, `allele_index`, `effect_types`, `effect_gene_symbols`, `variant_type`, `transmission_type`, `region_bin`, `frequency_bin`



SELECT bucket_index, summary_index, chromosome, `position`, effect_gene_symbols, effect_types, variant_type, family_id FROM data_hg38_seqclust.SFARI_SSC_WGS_CSHL_variants 
WHERE
  ( (  effect_gene_symbols in (  'SNORD141A'  )  ) ) AND 
  ( (`chromosome` = 'chr5' AND ((`position` >= 14632278 AND `position` <= 14672382) OR (COALESCE(end_position, -1) >= 14632278 AND COALESCE(end_position, -1) <= 14672382) OR (14632278 >= `position` AND 14672382 <= COALESCE(end_position, -1)))) OR 
    (`chromosome` = 'chr6' AND ((`position` >= 73498245 AND `position` <= 73538438) OR (COALESCE(end_position, -1) >= 73498245 AND COALESCE(end_position, -1) <= 73538438) OR (73498245 >= `position` AND 73538438 <= COALESCE(end_position, -1)))) OR 
    (`chromosome` = 'chr9' AND ((`position` >= 133000430 AND `position` <= 133040534) OR (COALESCE(end_position, -1) >= 133000430 AND COALESCE(end_position, -1) <= 133040534) OR (133000430 >= `position` AND 133040534 <= COALESCE(end_position, -1)))) ) AND 
  ( (  effect_types in (  'nonsense' , 'frame-shift' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'no-frame-shift' , 'noStart' , 'noEnd' , 'synonymous'  )  ) ) AND 
  ( BITAND(8, inheritance_in_members) = 0 AND BITAND(32, inheritance_in_members) = 0 ) AND ( BITAND(150, inheritance_in_members) != 0 ) AND 
  ( (((BITAND(variant_type, 4) != 0)) OR ((BITAND(variant_type, 2) != 0))) OR ((BITAND(variant_type, 1) != 0)) ) AND 
  ( allele_index > 0 ) AND 
  ( coding_bin = 1 ) AND 
  ( region_bin IN ('chr5_0','chr6_2','chr9_4') )


SELECT variants.bucket_index, variants.summary_index, MIN(variants.chromosome), MIN(variants.`position`), MIN(variants.effect_types), MIN(variants.effect_gene_symbols), variants.family_id, MIN(variants.inheritance_in_members), MAX(variants.inheritance_in_members)
FROM data_hg38_seqclust.SFARI_SSC_WGS_CSHL_variants as variants JOIN data_hg38_seqclust.SFARI_SSC_WGS_CSHL_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'SNORD141A'  )  ) ) AND 
  ( (`chromosome` = 'chr5' AND ((`position` >= 14652278 AND `position` <= 14652382) OR (COALESCE(end_position, -1) >= 14652278 AND COALESCE(end_position, -1) <= 14652382) OR (14652278 >= `position` AND 14652382 <= COALESCE(end_position, -1)))) OR 
    (`chromosome` = 'chr6' AND ((`position` >= 73518245 AND `position` <= 73518438) OR (COALESCE(end_position, -1) >= 73518245 AND COALESCE(end_position, -1) <= 73518438) OR (73518245 >= `position` AND 73518438 <= COALESCE(end_position, -1)))) OR 
    (`chromosome` = 'chr9' AND ((`position` >= 133020430 AND `position` <= 133020534) OR (COALESCE(end_position, -1) >= 133020430 AND COALESCE(end_position, -1) <= 133020534) OR (133020430 >= `position` AND 133020534 <= COALESCE(end_position, -1)))) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS' , 'CNV+' , 'CNV-'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(134, variants.inheritance_in_members) != 0 ) AND 
  ( (variants.genome_gnomad_v3_af_percent <= 100 or variants.genome_gnomad_v3_af_percent is null) ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.coding_bin = 1 ) AND 
  ( variants.region_bin IN ('chr5_0','chr6_2','chr9_4') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id 
HAVING gpf_bit_or(pedigree.status) IN (3, 1, 2)


SELECT variants.bucket_index, variants.summary_index, MIN(variants.chromosome), MIN(variants.`position`), MIN(variants.end_position), MIN(variants.variant_type), variants.family_id
FROM data_hg38_seqclust.SFARI_SSC_WGS_CSHL_variants as variants JOIN data_hg38_seqclust.SFARI_SSC_WGS_CSHL_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'SNORD141A'  )  ) ) AND 
  ( (`chromosome` = 'chr5' AND ((`position` >= 14652278 AND `position` <= 14652382) OR (COALESCE(end_position, -1) >= 14652278 AND COALESCE(end_position, -1) <= 14652382) OR (14652278 >= `position` AND 14652382 <= COALESCE(end_position, -1)))) OR 
    (`chromosome` = 'chr6' AND ((`position` >= 73518245 AND `position` <= 73518438) OR (COALESCE(end_position, -1) >= 73518245 AND COALESCE(end_position, -1) <= 73518438) OR (73518245 >= `position` AND 73518438 <= COALESCE(end_position, -1)))) OR 
    (`chromosome` = 'chr9' AND ((`position` >= 133020430 AND `position` <= 133020534) OR (COALESCE(end_position, -1) >= 133020430 AND COALESCE(end_position, -1) <= 133020534) OR (133020430 >= `position` AND 133020534 <= COALESCE(end_position, -1)))) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'cnv+' , 'cnv-' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'non-coding' , 'intron' , 'intergenic' , '3\'UTR' , '3\'UTR-intron' , '5\'UTR' , '5\'UTR-intron' , 'CDS' , 'CNV+' , 'CNV-'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( (variants.genome_gnomad_v3_af_percent <= 100 or variants.genome_gnomad_v3_af_percent is null) ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.region_bin IN ('chr5_0','chr6_2','chr9_4') ) AND variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id 
HAVING gpf_bit_or(pedigree.status) IN (3, 1, 2)


SELECT variants.bucket_index, variants.summary_index, variants.family_id, MIN(variants.effect_types)
FROM data_hg38_seqclust.SFARI_SSC_WGS_CSHL_variants as variants JOIN data_hg38_seqclust.SFARI_SSC_WGS_CSHL_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'SNORD15A'  )  ) ) AND 
  ( (`chromosome` = 'chr11' AND ((`position` >= 75400391 AND `position` <= 75400538) OR (COALESCE(end_position, -1) >= 75400391 AND COALESCE(end_position, -1) <= 75400538) OR (75400391 >= `position` AND 75400538 <= COALESCE(end_position, -1)))) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( (variants.genome_gnomad_v3_af_percent <= 100 or variants.genome_gnomad_v3_af_percent is null) ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.region_bin IN ('chr11_2') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id 
HAVING gpf_bit_or(pedigree.status) IN (3, 1, 2)




SELECT variants.bucket_index, variants.summary_index, MIN(variants.chromosome), MIN(variants.`position`), variants.family_id  
FROM data_hg38_seqclust.sfari_spark_wes_1_consortium_variants as variants JOIN data_hg38_seqclust.sfari_spark_wes_1_consortium_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'POGZ'  )  ) ) AND 
  ( (`chromosome` = 'chr1' AND ((`position` >= 151424919 AND `position` <= 151424967) OR (COALESCE(end_position, -1) >= 151424919 AND COALESCE(end_position, -1) <= 151424967) OR (151424919 >= `position` AND 151424967 <= COALESCE(end_position, -1)))) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND 
  ( BITAND(134, variants.inheritance_in_members) != 0 ) AND
  ( variants.allele_index > 0 ) AND 
  ( variants.region_bin IN ('chr1_5') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY variants.bucket_index, variants.summary_index, variants.family_id HAVING gpf_bit_or(pedigree.status) IN (1, 2, 3);




SELECT variants.bucket_index, variants.summary_index, variants.family_variants_count, variants.seen_in_status, variants.seen_as_denovo 
FROM data_hg38_production_202005.sfari_spark_wgs_1_summary_variants as variants 
WHERE
  ( (  variants.effect_gene_symbols in (  'CHD8'  )  ) ) AND 
  ( (`chromosome` = 'chr14' AND ((`position` >= 21365194 AND `position` <= 21457298) OR (COALESCE(end_position, -1) >= 21365194 AND COALESCE(end_position, -1) <= 21457298) OR (21365194 >= `position` AND 21457298 <= COALESCE(end_position, -1)))) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'nonsense' , 'frame-shift' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS' , 'CNV+' , 'CNV-'  )  ) ) AND 
  ( variants.allele_index > 0 ) AND ( variants.coding_bin = 1 ) AND ( variants.region_bin IN ('chr14_0') )



SELECT
    variants.bucket_index,
    variants.summary_index,
    variants.allele_index,
    variants.effect_types,
    variants.effect_gene_symbols,
    MIN(variants.af_allele_count),
    MAX(variants.af_allele_count),
    MIN(variants.genome_gnomad_v3_ac),
    MAX(variants.genome_gnomad_v3_ac),
    CAST(COUNT(DISTINCT variants.family_id) AS INT),
    CAST(gpf_bit_or(pedigree.status) AS TINYINT),
    CAST(gpf_or(BITAND(inheritance_in_members, 4)) AS BOOLEAN)
FROM data_hg38_seqclust.SFARI_SPARK_WGS_1_variants as variants 
JOIN data_hg38_seqclust.SFARI_SPARK_WGS_1_pedigree as pedigree
WHERE
    variants.allele_index > 0 AND 
    variants.variant_in_members = pedigree.person_id 
GROUP BY 
    bucket_index,
    summary_index,
    allele_index,
    effect_types,
    effect_gene_symbols,
    variant_type,
    transmission_type
HAVING MIN(variants.af_allele_count) != MAX(variants.af_allele_count) OR MIN(variants.genome_gnomad_v3_ac) != MAX(variants.genome_gnomad_v3_ac)
LIMIT 50;

SELECT
    variants.bucket_index,
    variants.summary_index,
    variants.allele_index,
    variants.effect_types,
    variants.effect_gene_symbols,
    MIN(variants.af_allele_count),
    MAX(variants.af_allele_count),
    MIN(variants.genome_gnomad_v3_ac),
    MAX(variants.genome_gnomad_v3_ac),
    CAST(COUNT(DISTINCT variants.family_id) AS INT),
    CAST(gpf_bit_or(pedigree.status) AS TINYINT),
    CAST(gpf_or(BITAND(inheritance_in_members, 4)) AS BOOLEAN)
FROM data_hg38_seqclust.SFARI_SPARK_WGS_1_variants as variants 
JOIN data_hg38_seqclust.SFARI_SPARK_WGS_1_pedigree as pedigree
WHERE
    variants.region_bin = 'chr1_0' AND 
    variants.frequency_bin = 2 AND
    variants.allele_index > 0 AND 
    variants.variant_in_members = pedigree.person_id 
GROUP BY 
    bucket_index,
    summary_index,
    allele_index,
    effect_types,
    effect_gene_symbols,
    variant_type,
    transmission_type
HAVING MIN(variants.af_allele_count) != MAX(variants.af_allele_count) OR MIN(variants.genome_gnomad_v3_ac) != MAX(variants.genome_gnomad_v3_ac)
LIMIT 50;


ALTER TABLE sfari_ssc_wgs_cshl_variants SET TBLPROPERTIES(
  "gpf_partitioning_coding_bin_coding_effect_types" = 
  "splice-site,frame-shift,nonsense,no-frame-shift-newStop,noStart,noEnd,missense,no-frame-shift,CDS,synonymous,coding_unknown,regulatory,3'UTR,5'UTR,CNV+,CNV-")


ALTER TABLE data_hg38_seqclust.agre_wg38_859_variants SET TBLPROPERTIES(
  "gpf_partitioning_coding_bin_coding_effect_types" = 
  "splice-site,frame-shift,nonsense,no-frame-shift-newStop,noStart,noEnd,missense,no-frame-shift,CDS,synonymous,coding_unknown,regulatory,3'UTR,5'UTR,CNV+,CNV-")

ALTER TABLE data_hg38_seqclust.sfari_spark_wgs_1_variants SET TBLPROPERTIES(
  "gpf_partitioning_coding_bin_coding_effect_types" = 
  "splice-site,frame-shift,nonsense,no-frame-shift-newStop,noStart,noEnd,missense,no-frame-shift,CDS,synonymous,coding_unknown,regulatory,3'UTR,5'UTR,CNV+,CNV-");


SELECT variants.bucket_index, variants.summary_index, allele_index, COUNT(DISTINCT variants.family_id), gpf_bit_or(pedigree.status), gpf_or(BITAND(inheritance_in_members, 4))
FROM impala_test_db.summary_stats_variants as variants JOIN impala_test_db.summary_stats_pedigree as pedigree 
WHERE
  ( (`chromosome` = '1' AND ((`position` >= 865581 AND `position` <= 865581) OR (COALESCE(end_position, -1) >= 865581 AND COALESCE(end_position, -1) <= 865581) OR (865581 >= `position` AND 865581 <= COALESCE(end_position, -1)))) ) AND 
  ( variants.allele_index > 0 ) AND variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index, allele_index, variant_type


SELECT variants.bucket_index, variants.summary_index, allele_index, COUNT(DISTINCT variants.family_id), gpf_bit_or(pedigree.status), gpf_or(BITAND(inheritance_in_members, 4))
FROM gpf_variant_db.summary_stats_variants as variants JOIN gpf_variant_db.summary_stats_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'SAMD11'  )  ) ) AND ( (`chromosome` = '1' AND ((`position` >= 841121 AND `position` <= 899961) OR (COALESCE(end_position, -1) >= 841121 AND COALESCE(end_position, -1) <= 899961) OR (841121 >= `position` AND 899961 <= COALESCE(end_position, -1)))) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'nonsense' , 'frame-shift' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS' , 'CNV+' , 'CNV-'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND ( variants.allele_index > 0 ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index, allele_index, variant_type, transmission_type

SELECT variants.bucket_index, variants.summary_index, COUNT(DISTINCT variants.family_id), gpf_bit_or(pedigree.status), gpf_or(BITAND(inheritance_in_members, 4))
FROM gpf_variant_db.summary_stats_variants as variants JOIN gpf_variant_db.summary_stats_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'SAMD11'  )  ) ) AND ( (`chromosome` = '1' AND ((`position` >= 841121 AND `position` <= 899961) OR (COALESCE(end_position, -1) >= 841121 AND COALESCE(end_position, -1) <= 899961) OR (841121 >= `position` AND 899961 <= COALESCE(end_position, -1)))) ) AND 
  ( (  variants.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop' , 'nonsense' , 'frame-shift' , 'splice-site' , 'no-frame-shift-newStop' , 'missense' , 'synonymous' , 'noStart' , 'noEnd' , 'no-frame-shift' , 'CDS' , 'CNV+' , 'CNV-'  )  ) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND ( variants.allele_index > 0 ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index, allele_index, variant_type, transmission_type


SELECT variants.bucket_index, variants.summary_index, allele_index, variant_type, transmission_type, COUNT(DISTINCT variants.family_id), gpf_or(BITAND(inheritance_in_members, 4))
FROM impala_test_db.summary_stats_variants as variants JOIN impala_test_db.summary_stats_pedigree as pedigree 
WHERE
  ( (`chromosome` = '1' AND ((`position` >= 865582 AND `position` <= 865583) OR (COALESCE(end_position, -1) >= 865582 AND COALESCE(end_position, -1) <= 865583) OR (865582 >= `position` AND 865583 <= COALESCE(end_position, -1)))) ) AND 
  ( variants.allele_index > 0 ) AND variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index, allele_index, variant_type, transmission_type





SELECT variants.bucket_index, variants.summary_index, COUNT(DISTINCT variants.family_id)
FROM data_hg38_production.SFARI_SSC_WGS_2b_variants as variants JOIN data_hg38_production.SFARI_SSC_WGS_2b_pedigree as pedigree 
WHERE
  ( (  variants.effect_gene_symbols in (  'DMRTA2'  )  ) ) AND ( (`chromosome` = 'chr1' AND ((`position` >= 50397551 AND `position` <= 50443447) OR (COALESCE(end_position, -1) >= 50397551 AND COALESCE(end_position, -1) <= 50443447) OR (50397551 >= `position` AND 50443447 <= COALESCE(end_position, -1)))) ) AND 
  ( BITAND(8, variants.inheritance_in_members) = 0 AND BITAND(32, variants.inheritance_in_members) = 0 ) AND ( BITAND(150, variants.inheritance_in_members) != 0 ) AND 
  ( variants.allele_index > 0 ) AND 
  ( variants.region_bin IN ('chr1_1') ) AND 
  variants.variant_in_members = pedigree.person_id 
GROUP BY bucket_index, summary_index, allele_index, variant_type


SELECT bucket_index, summary_index, variant_type, family_index, family_id, frequency_bin FROM data_hg38_production.SFARI_SPARK_WES_1_temp_variants 
WHERE
  ( (  effect_types in (  'nonsense' , 'frame-shift' , 'splice-site' , 'no-frame-shift-newStop'  )  ) )
  AND ( (af_allele_count <= 1 or af_allele_count is null) )
  AND ( allele_index > 0 ) 
  LIMIT 10;




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

# Experiments with `duckdb_storage` performance

## Count all summary variants in `CHD8`


```sql
SELECT count(*)
  FROM
    AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa 
    CROSS JOIN
        (SELECT UNNEST(sa.effect_gene) AS eg) 
  WHERE
    ( sa.region_bin IN ('chr14_0')) AND
    (  eg.effect_gene_symbols in (  'CHD8'  )  ) AND
    ( ( sa.chromosome = 'chr14' AND ((sa.position >= 21365194 AND sa.position <= 21457298) OR (COALESCE(sa.end_position, -1) >= 21365194 AND COALESCE(sa.end_position, -1) <= 21457298) OR (21365194 >= sa.position AND 21457298 <= COALESCE(sa.end_position, -1)))) ) AND 
    ( sa.allele_index > 0 );
```

```
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│         1161 │
└──────────────┘
Run Time (s): real 15.217 user 457.906170 sys 0.343158
```

```sql
EXPLAIN ANALYZE SELECT count(*)
  FROM
    AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa 
    CROSS JOIN
        (SELECT UNNEST(sa.effect_gene) AS eg) 
  WHERE
    ( sa.region_bin IN ('chr14_0')) AND
    (  eg.effect_gene_symbols in (  'CHD8'  )  ) AND
    ( ( sa.chromosome = 'chr14' AND ((sa.position >= 21365194 AND sa.position <= 21457298) OR (COALESCE(sa.end_position, -1) >= 21365194 AND COALESCE(sa.end_position, -1) <= 21457298) OR (21365194 >= sa.position AND 21457298 <= COALESCE(sa.end_position, -1)))) ) AND 
    ( sa.allele_index > 0 );
```

```
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││         Total Time: 15.72s        ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
┌───────────────────────────┐
│      EXPLAIN_ANALYZE      │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│             0             │
│          (0.00s)          │
└─────────────┬─────────────┘                             
┌─────────────┴─────────────┐
│    UNGROUPED_AGGREGATE    │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│        count_star()       │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│             1             │
│          (0.00s)          │
└─────────────┬─────────────┘                             
┌─────────────┴─────────────┐
│           FILTER          │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│  ((allele_index > 0) AND  │
│(region_bin = 'chr14_0...  │
│(chromosome = 'chr14') AND │
│    (struct_extract(eg,    │
│'effect_gene_symbols')...  │
│ AND (((position >= 21...  │
│ AND (position <= 2145...  │
│ OR ((21365194 >= position)│
│  AND (21457298 <= COALESCE│
│ (end_position, -1))) OR ( │
│(COALESCE(end_position...  │
│   21365194) AND (COALESCE │
│(end_position, -1) <= ...  │
│            ))))           │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│       EC: 147097062       │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│            1161           │
│         (105.00s)         │
└─────────────┬─────────────┘                             
┌─────────────┴─────────────┐
│         PROJECTION        │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│             #1            │
│             #2            │
│             #3            │
│             #4            │
│             #5            │
│             eg            │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│          80969139         │
│          (33.58s)         │
└─────────────┬─────────────┘                             
┌─────────────┴─────────────┐
│           UNNEST          │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│          80969139         │
│         (246.82s)         │
└─────────────┬─────────────┘                             
┌─────────────┴─────────────┐
│         SEQ_SCAN          │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│AGRE_WG38_CSHL_859_SCHEMA2_│
│          summary          │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│        effect_gene        │
│         region_bin        │
│         chromosome        │
│          position         │
│        end_position       │
│        allele_index       │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│       EC: 147097062       │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│         147097062         │
│          (3.03s)          │
└───────────────────────────┘                             
Run Time (s): real 15.728 user 473.121997 sys 0.369473
```

In contrast to count all the variants on `chr14` we have:

```sql
SELECT count(*)
  FROM
    AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa 
  WHERE
    ( sa.region_bin IN ('chr14_0'));
```

```
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│      1611800 │
└──────────────┘
Run Time (s): real 0.027 user 0.821267 sys 0.000000
```

and to count all the variants that are in the region of `CHD8`

```sql
SELECT count(*)
  FROM
    AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa 
  WHERE
    ( sa.region_bin IN ('chr14_0')) AND
    ( ( sa.chromosome = 'chr14' AND ((sa.position >= 21365194 AND sa.position <= 21457298) OR (COALESCE(sa.end_position, -1) >= 21365194 AND COALESCE(sa.end_position, -1) <= 21457298) OR (21365194 >= sa.position AND 21457298 <= COALESCE(sa.end_position, -1)))) ) AND 
    ( sa.allele_index > 0 );
```

```
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│         2147 │
└──────────────┘
Run Time (s): real 0.012 user 0.252538 sys 0.000002
```



```sql

WITH summary AS (
SELECT *
  FROM
    AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa 
  WHERE
    ( sa.region_bin IN ('chr14_0')) AND
    ( ( sa.chromosome = 'chr14' AND ((sa.position >= 21365194 AND sa.position <= 21457298) OR (COALESCE(sa.end_position, -1) >= 21365194 AND COALESCE(sa.end_position, -1) <= 21457298) OR (21365194 >= sa.position AND 21457298 <= COALESCE(sa.end_position, -1)))) ) AND 
    ( sa.allele_index > 0 )    
)
SELECT count(*) 
FROM summary
CROSS JOIN
    (SELECT UNNEST (summary.effect_gene) as eg)
WHERE
    eg.effect_gene_symbols in ('CHD8');


```

```
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│         1161 │
└──────────────┘
Run Time (s): real 0.017 user 0.230500 sys 0.099784
```


## Count all LGDs de Novo variants

```sql
SELECT count(*)
  FROM
    AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
    JOIN
    AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
    ON (fa.summary_index = sa.summary_index AND
        fa.bucket_index = sa.bucket_index AND
        fa.allele_index = sa.allele_index) 
    CROSS JOIN
        (SELECT UNNEST(fa.allele_in_members) AS pi) 
    JOIN
    AGRE_WG38_CSHL_859_SCHEMA2_pedigree AS pedigree
    ON (pi = pedigree.person_id) 
    CROSS JOIN
        (SELECT UNNEST(sa.effect_gene) AS eg) 
  WHERE
    ( (  eg.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop'  )  ) ) AND 
    ( (8 & fa.inheritance_in_members) = 0 AND (32 & fa.inheritance_in_members) = 0 ) AND 
    ( (4 & fa.inheritance_in_members) != 0 ) AND 
    ( ((((fa.allele_in_roles & 128) != 0) AND ((NOT ((fa.allele_in_roles & 256) != 0)))) OR (((fa.allele_in_roles & 128) != 0) AND ((fa.allele_in_roles & 256) != 0))) AND (((NOT ((fa.allele_in_roles & 32) != 0))) AND ((NOT ((fa.allele_in_roles & 16) != 0)))) ) AND 
    ( (((sa.variant_type & 2) != 0) OR ((sa.variant_type & 1) != 0)) OR ((sa.variant_type & 4) != 0) ) AND 
    ( sa.allele_index > 0 ) AND 
    ( fa.frequency_bin IN (0) AND sa.frequency_bin IN (0) ) AND 
    ( fa.coding_bin IN (1) AND sa.coding_bin IN (1) );
```
resulted in big fat **OOM** (out of memory) on pooh (128GB)


Let us try to get rid of all `UNNEST` clauses. This gives us the
total count of all alleles that are in de Novo frequency bin and coding bin.

```sql
SELECT count(*)
  FROM
    AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
    JOIN
    AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
    ON (fa.summary_index = sa.summary_index AND
        fa.bucket_index = sa.bucket_index AND
        fa.allele_index = sa.allele_index) 
  WHERE
    ( (8 & fa.inheritance_in_members) = 0 AND (32 & fa.inheritance_in_members) = 0 ) AND 
    ( (4 & fa.inheritance_in_members) != 0 ) AND 
    ( ((((fa.allele_in_roles & 128) != 0) AND ((NOT ((fa.allele_in_roles & 256) != 0)))) OR (((fa.allele_in_roles & 128) != 0) AND ((fa.allele_in_roles & 256) != 0))) AND (((NOT ((fa.allele_in_roles & 32) != 0))) AND ((NOT ((fa.allele_in_roles & 16) != 0)))) ) AND 
    ( (((sa.variant_type & 2) != 0) OR ((sa.variant_type & 1) != 0)) OR ((sa.variant_type & 4) != 0) ) AND 
    ( sa.allele_index > 0 ) AND 
    ( fa.frequency_bin IN (0) AND sa.frequency_bin IN (0) ) AND 
    ( fa.coding_bin IN (1) AND sa.coding_bin IN (1) );
```

```
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│         9679 │
└──────────────┘
Run Time (s): real 0.559 user 1.052228 sys 0.595499
```

Let now try to remove the join on pedigree table:

```sql
 SELECT count(*)
  FROM
    AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
    JOIN
    AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
    ON (fa.summary_index = sa.summary_index AND
        fa.bucket_index = sa.bucket_index AND
        fa.allele_index = sa.allele_index) 
    CROSS JOIN
        (SELECT UNNEST(sa.effect_gene) AS eg) 
  WHERE
    ( (  eg.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop'  )  ) ) AND 
    ( (8 & fa.inheritance_in_members) = 0 AND (32 & fa.inheritance_in_members) = 0 ) AND 
    ( (4 & fa.inheritance_in_members) != 0 ) AND 
    ( ((((fa.allele_in_roles & 128) != 0) AND ((NOT ((fa.allele_in_roles & 256) != 0)))) OR (((fa.allele_in_roles & 128) != 0) AND ((fa.allele_in_roles & 256) != 0))) AND (((NOT ((fa.allele_in_roles & 32) != 0))) AND ((NOT ((fa.allele_in_roles & 16) != 0)))) ) AND 
    ( (((sa.variant_type & 2) != 0) OR ((sa.variant_type & 1) != 0)) OR ((sa.variant_type & 4) != 0) ) AND 
    ( sa.allele_index > 0 ) AND 
    ( fa.frequency_bin IN (0) AND sa.frequency_bin IN (0) ) AND 
    ( fa.coding_bin IN (1) AND sa.coding_bin IN (1) );
```

```
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│          486 │
└──────────────┘
Run Time (s): real 1037.503 user 32454.268769 sys 20.092551
```

Let us try to reorganize the query. Count the summary alleles in 
coding bin and de Novo frequency bin:

```sql
WITH summary AS (
SELECT *
FROM
    AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
WHERE
    ( (((sa.variant_type & 2) != 0) OR ((sa.variant_type & 1) != 0)) OR ((sa.variant_type & 4) != 0) ) AND 
    ( sa.allele_index > 0 ) AND 
    sa.frequency_bin IN (0) AND
    sa.coding_bin IN (1)
)
SELECT COUNT(*) FROM summary;
```

```
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│        10008 │
└──────────────┘
Run Time (s): real 0.007 user 0.127055 sys 0.004689
```

Now let us count the family alleles in coding bin and de Novo frequency bin
that are de Novo:

```sql
WITH family AS (
SELECT *
FROM
    AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
WHERE
    ( (8 & fa.inheritance_in_members) = 0 AND (32 & fa.inheritance_in_members) = 0 ) AND 
    ( (4 & fa.inheritance_in_members) != 0 ) AND 
    ( ((((fa.allele_in_roles & 128) != 0) AND ((NOT ((fa.allele_in_roles & 256) != 0)))) OR (((fa.allele_in_roles & 128) != 0) AND ((fa.allele_in_roles & 256) != 0))) AND (((NOT ((fa.allele_in_roles & 32) != 0))) AND ((NOT ((fa.allele_in_roles & 16) != 0)))) ) AND 
   fa.frequency_bin IN (0) AND
   fa.coding_bin IN (1) 
)
SELECT COUNT(*) FROM family;
```

```
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│         9679 │
└──────────────┘
Run Time (s): real 0.025 user 0.101976 sys 0.591267
```

Let us try to join the last two queries:

```sql
WITH 
summary AS (
SELECT *
FROM
    AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
WHERE
    ( (((sa.variant_type & 2) != 0) OR ((sa.variant_type & 1) != 0)) OR ((sa.variant_type & 4) != 0) ) AND 
    ( sa.allele_index > 0 ) AND 
    sa.frequency_bin IN (0) AND
    sa.coding_bin IN (1)
),
family AS (
SELECT *
FROM
    AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
WHERE
    ( (8 & fa.inheritance_in_members) = 0 AND (32 & fa.inheritance_in_members) = 0 ) AND 
    ( (4 & fa.inheritance_in_members) != 0 ) AND 
    ( ((((fa.allele_in_roles & 128) != 0) AND ((NOT ((fa.allele_in_roles & 256) != 0)))) OR (((fa.allele_in_roles & 128) != 0) AND ((fa.allele_in_roles & 256) != 0))) AND (((NOT ((fa.allele_in_roles & 32) != 0))) AND ((NOT ((fa.allele_in_roles & 16) != 0)))) ) AND 
   fa.frequency_bin IN (0) AND
   fa.coding_bin IN (1) 
)
SELECT COUNT(*) 
FROM 
    summary as sa
JOIN 
    family as fa
ON (
    fa.summary_index = sa.summary_index AND
    fa.bucket_index = sa.bucket_index AND
    fa.allele_index = sa.allele_index) ;

```

```
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│         9679 │
└──────────────┘
Run Time (s): real 0.072 user 0.327199 sys 0.507408
```

Now let us select only LGDs:

```sql
WITH 
summary AS (
SELECT *
FROM
    AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
WHERE
    ( (((sa.variant_type & 2) != 0) OR ((sa.variant_type & 1) != 0)) OR ((sa.variant_type & 4) != 0) ) AND 
    ( sa.allele_index > 0 ) AND 
    sa.frequency_bin IN (0) AND
    sa.coding_bin IN (1)
),
family AS (
SELECT *
FROM
    AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
WHERE
    ( (8 & fa.inheritance_in_members) = 0 AND (32 & fa.inheritance_in_members) = 0 ) AND 
    ( (4 & fa.inheritance_in_members) != 0 ) AND 
    ( ((((fa.allele_in_roles & 128) != 0) AND ((NOT ((fa.allele_in_roles & 256) != 0)))) OR (((fa.allele_in_roles & 128) != 0) AND ((fa.allele_in_roles & 256) != 0))) AND (((NOT ((fa.allele_in_roles & 32) != 0))) AND ((NOT ((fa.allele_in_roles & 16) != 0)))) ) AND 
   fa.frequency_bin IN (0) AND
   fa.coding_bin IN (1) 
)
SELECT COUNT(*) 
FROM 
    summary as sa
JOIN 
    family as fa
ON (
    fa.summary_index = sa.summary_index AND
    fa.bucket_index = sa.bucket_index AND
    fa.allele_index = sa.allele_index)
CROSS JOIN
    (SELECT UNNEST(sa.effect_gene) AS eg) 
WHERE
    ( (  eg.effect_types in (  'frame-shift' , 'nonsense' , 'splice-site' , 'no-frame-shift-newStop'  )  ) );
```

```
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│          486 │
└──────────────┘
Run Time (s): real 0.064 user 0.428915 sys 0.479439
```

## Experimental summary variants query

```sql
WITH summary AS (
    SELECT
        *
    FROM
        AGRE_WG38_CSHL_859_SCHEMA2_summary sa
    WHERE
        ( sa.region_bin IN ('chr14_0')) AND
        ( sa.chromosome = 'chr14' AND NOT ( COALESCE(sa.end_position, sa.position) < 21365194 OR sa.position > 21457298 ) ) AND sa.allele_index > 0
)

SELECT
    bucket_index, summary_index,
    list(allele_index), first(summary_variant_data)
FROM summary

CROSS JOIN
    (SELECT UNNEST (effect_gene) as eg)
WHERE
    eg.effect_gene_symbols in ('CHD8')
GROUP BY bucket_index, summary_index
LIMIT 5;
```

```sql
WITH summary AS (
    SELECT
        *
    FROM
        AGRE_WG38_CSHL_859_SCHEMA2_summary sa
    WHERE
        ( sa.region_bin IN ('chr14_0')) AND
        ( sa.chromosome = 'chr14' AND NOT ( COALESCE(sa.end_position, sa.position) < 21365194 OR sa.position > 21457298 ) ) AND sa.allele_index > 0
)

SELECT
    bucket_index, summary_index,
    list(allele_index), first(summary_variant_data)
FROM summary

CROSS JOIN
    (SELECT UNNEST (effect_gene) as eg)
WHERE
    eg.effect_gene_symbols in ('CHD8')
GROUP BY bucket_index, summary_index
LIMIT 500;
```


```sql
WITH summary AS (
    SELECT
        *
    FROM
        AGRE_WG38_CSHL_859_SCHEMA2_summary sa
    WHERE
        ( sa.region_bin IN ('chr14_0')) AND
        ( sa.coding_bin IN (1)) AND
        ( sa.chromosome = 'chr14' AND NOT ( COALESCE(sa.end_position, sa.position) < 21365194 OR sa.position > 21457298 ) ) AND sa.allele_index > 0
)

SELECT
    bucket_index, summary_index,
    list(allele_index), first(summary_variant_data)
FROM summary

CROSS JOIN
    (SELECT UNNEST (effect_gene) as eg)
WHERE
    eg.effect_gene_symbols in ('CHD8')
GROUP BY bucket_index, summary_index
LIMIT 500;
```



```sql
WITH summary AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
  WHERE
    (
      sa.af_allele_freq >= 0 AND sa.af_allele_freq <= 5
    )
    AND sa.coding_bin = 1
    AND sa.frequency_bin IN (0, 1, 2)
    AND sa.allele_index > 0
), family AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    fa.coding_bin = 1 AND fa.frequency_bin IN (0, 1, 2) AND fa.allele_index > 0
)
SELECT
  fa.bucket_index,
  fa.summary_index,
  fa.family_index,
  sa.allele_index,
  sa.summary_variant_data,
  fa.family_variant_data
FROM summary AS sa
JOIN family AS fa
  ON (
    fa.summary_index = sa.summary_index
    AND fa.bucket_index = sa.bucket_index
    AND fa.allele_index = sa.allele_index
  )
CROSS JOIN (
  SELECT
    UNNEST(effect_gene) AS eg
)
WHERE
  eg.effect_gene_symbols IN ('AAK1', 'AATK', 'ABCA2', 'ABCA3', 'ABCG1', 'ABR', 'ACCN1', 'ACLY', 'ACO2', 'ACTB', 'ADAP1', 'ADARB1', 'ADCY1', 'ADCY5', 'ADD1', 'ADNP', 'ADRBK1', 'AFF3', 'AFF4', 'AGAP1', 'AGAP2', 'AGAP3', 'AGPAT3', 'AGRN', 'AGTPBP1', 'AHDC1', 'AKAP6', 'AKAP9', 'AKT3', 'ALDOA', 'ALDOC', 'ALS2', 'AMPH', 'ANAPC1', 'ANK1', 'ANK2', 'ANK3', 'ANKRD11', 'ANKRD17', 'ANKRD52', 'AP1B1', 'AP2A1', 'AP2A2', 'AP2B1', 'AP3D1', 'APBA1', 'APBB1', 'APC', 'APC2', 'APLP1', 'APOE', 'APP', 'ARAP2', 'ARF3', 'ARFGEF1', 'ARHGAP20', 'ARHGAP21', 'ARHGAP23', 'ARHGAP32', 'ARHGAP33', 'ARHGEF11', 'ARHGEF12', 'ARHGEF17', 'ARHGEF2', 'ARHGEF4', 'ARHGEF7', 'ARID1A', 'ARID1B', 'ARID2', 'ARNT2', 'ARPP21', 'ARRB1', 'ARVCF', 'ASH1L', 'ATF7IP', 'ATG2A', 'ATG2B', 'ATG9A', 'ATMIN', 'ATN1', 'ATP13A2', 'ATP1A1', 'ATP1A2', 'ATP1A3', 'ATP1B1', 'ATP2A2', 'ATP2B2', 'ATP2B4', 'ATP5A1', 'ATP5B', 'ATP6V0A1', 'ATP6V0D1', 'ATP6V1B2', 'ATP9A', 'ATXN1', 'AUTS2', 'B3GAT1', 'BAI1', 'BAI2', 'BAP1', 'BAT2', 'BAT2L1', 'BAT2L2', 'BAT3', 'BAZ2A', 'BCAN', 'BCL9L', 'BCR', 'BIRC6', 'BMPR2', 'BPTF', 'BRD4', 'BRSK1', 'BRSK2', 'BSN', 'BZRAP1', 'C11ORF41', 'C14ORF4', 'C19ORF26', 'C20ORF117', 'C20ORF12', 'C2CD2L', 'CABIN1', 'CACNA1A', 'CACNA1B', 'CACNA1E', 'CACNA1G', 'CACNA1I', 'CACNB1', 'CACNB3', 'CADPS', 'CALM1', 'CALM3', 'CAMK2A', 'CAMK2B', 'CAMK2N1', 'CAMKK2', 'CAMSAP1', 'CAMSAP1L1', 'CAMTA1', 'CAMTA2', 'CAND1', 'CASKIN1', 'CBX6', 'CBX6-NPTXR', 'CDC42BPA', 'CDC42BPB', 'CDK16', 'CDK17', 'CDK5R1', 'CDK5R2', 'CDKL5', 'CELF5', 'CELSR2', 'CELSR3', 'CHD3', 'CHD4', 'CHD5', 'CHD6', 'CHD8', 'CHN1', 'CHN2', 'CHST2', 'CIC', 'CIT', 'CKAP5', 'CKB', 'CLASP1', 'CLASP2', 'CLCN3', 'CLEC16A', 'CLIP3', 'CLSTN1', 'CLTC', 'CNP', 'COBL', 'COPG', 'CPE', 'CPLX1', 'CPLX2', 'CPT1C', 'CREBBP', 'CRMP1', 'CRTC1', 'CTBP1', 'CTNNB1', 'CTNND2', 'CUL9', 'CUX1', 'CUX2', 'CYFIP2', 'DAB2IP', 'DAGLA', 'DAPK1', 'DBC1', 'DCAF6', 'DCLK1', 'DCTN1', 'DDN', 'DDX24', 'DENND5A', 'DGCR2', 'DGKZ', 'DHX30', 'DICER1', 'DIDO1', 'DIP2A', 'DIP2B', 'DIP2C', 'DIRAS2', 'DISP2', 'DLC1', 'DLG2', 'DLG4', 'DLG5', 'DLGAP1', 'DLGAP2', 'DLGAP3', 'DLGAP4', 'DMWD', 'DMXL2', 'DNAJC6', 'DNM1', 'DOCK3', 'DOCK4', 'DOCK9', 'DOPEY1', 'DOPEY2', 'DOT1L', 'DPP8', 'DPYSL2', 'DSCAM', 'DSCAML1', 'DST', 'DTNA', 'DTX1', 'DUSP8', 'DYNC1H1', 'EEF1A2', 'EEF2', 'EGR1', 'EHMT1', 'EHMT2', 'EIF2C1', 'EIF2C2', 'EIF4G1', 'EIF4G2', 'EIF4G3', 'ELFN2', 'ELMO2', 'EML2', 'ENC1', 'EP300', 'EP400', 'EPB41L1', 'EPB49', 'EPHA4', 'EPN1', 'EXTL3', 'FAM115A', 'FAM120A', 'FAM160A2', 'FAM171B', 'FAM179B', 'FAM190B', 'FAM21A', 'FAM5B', 'FAM65A', 'FAM91A1', 'FASN', 'FAT1', 'FAT2', 'FAT3', 'FAT4', 'FBXL16', 'FBXL19', 'FBXO41', 'FCHO1', 'FKBP8', 'FOXK2', 'FOXO3', 'FRMPD4', 'FRY', 'FSCN1', 'FYN', 'GABBR1', 'GABBR2', 'GARNL3', 'GAS7', 'GBF1', 'GCN1L1', 'GIT1', 'GLUL', 'GM996', 'GNAL', 'GNAO1', 'GNAS', 'GNAZ', 'GNB1', 'GPAM', 'GPM6A', 'GPR158', 'GPR162', 'GPRIN1', 'GRAMD1B', 'GRIK3', 'GRIK5', 'GRIN1', 'GRIN2A', 'GRIN2B', 'GRLF1', 'GRM4', 'GRM5', 'GSK3B', 'GTF3C1', 'GTF3C2', 'HCFC1', 'HCN2', 'HDAC4', 'HDAC5', 'HDLBP', 'HEATR5B', 'HERC1', 'HERC2', 'HIPK1', 'HIPK2', 'HIPK3', 'HIVEP1', 'HIVEP2', 'HIVEP3', 'HK1', 'HMGXB3', 'HNRNPUL1', 'HSP90AB1', 'HTT', 'HUWE1', 'IDS', 'IGSF9B', 'INPP4A', 'INTS1', 'IPO13', 'IPO4', 'IPO5', 'IQSEC2', 'IQSEC3', 'IRS2', 'ITPR1', 'ITSN1', 'JAK1', 'JPH3', 'JPH4', 'KALRN', 'KCNA2', 'KCNB1', 'KCNC3', 'KCND2', 'KCNH1', 'KCNH3', 'KCNH7', 'KCNMA1', 'KCNQ2', 'KCNQ3', 'KCNT1', 'KDM4B', 'KDM5C', 'KDM6B', 'KIAA0090', 'KIAA0100', 'KIAA0226', 'KIAA0284', 'KIAA0317', 'KIAA0430', 'KIAA0664', 'KIAA0802', 'KIAA0913', 'KIAA0947', 'KIAA1045', 'KIAA1109', 'KIAA1244', 'KIAA1688', 'KIAA2018', 'KIF1A', 'KIF1B', 'KIF21A', 'KIF21B', 'KIF3C', 'KIF5A', 'KIF5C', 'KIFC2', 'KLC1', 'KLHL22', 'KNDC1', 'LARGE', 'LARS2', 'LHFPL4', 'LINGO1', 'LLGL1', 'LMTK2', 'LMTK3', 'LPHN1', 'LPHN3', 'LPIN2', 'LPPR4', 'LRP1', 'LRP3', 'LRP8', 'LRRC41', 'LRRC4B', 'LRRC68', 'LRRC7', 'LRRC8B', 'LRRN2', 'LYNX1', 'MACF1', 'MADD', 'MAGED1', 'MAGI2', 'MAN2A2', 'MAP1A', 'MAP1B', 'MAP2', 'MAP3K12', 'MAP4', 'MAP4K4', 'MAP7D1', 'MAPK1', 'MAPK4', 'MAPK8IP1', 'MAPK8IP3', 'MAPKBP1', 'MAST1', 'MAST2', 'MAST4', 'MAZ', 'MBD5', 'MBP', 'MED13', 'MED13L', 'MED14', 'MED16', 'MEF2D', 'MFHAS1', 'MGAT5B', 'MIB1', 'MICAL2', 'MINK1', 'MKL2', 'MLL', 'MLL2', 'MLL3', 'MLL5', 'MMP24', 'MON2', 'MPRIP', 'MTMR4', 'MTOR', 'MTSS1L', 'MYCBP2', 'MYH10', 'MYO10', 'MYO16', 'MYO18A', 'MYO5A', 'MYST3', 'MYT1L', 'NACAD', 'NAT8L', 'NAV1', 'NAV2', 'NAV3', 'NBEA', 'NCAM1', 'NCAN', 'NCDN', 'NCKAP1', 'NCOA1', 'NCOA2', 'NCOA6', 'NCOR1', 'NCOR2', 'NCS1', 'NDRG2', 'NDRG4', 'NDST1', 'NEDD4', 'NELF', 'NEURL', 'NEURL4', 'NF1', 'NFIC', 'NFIX', 'NGEF', 'NHSL1', 'NISCH', 'NLGN2', 'NLGN3', 'NOMO1', 'NPAS2', 'NPTXR', 'NR2F1', 'NRGN', 'NRIP1', 'NRXN1', 'NRXN2', 'NRXN3', 'NSD1', 'NSF', 'NTRK2', 'NTRK3', 'NUP98', 'NWD1', 'ODZ2', 'ODZ3', 'ODZ4', 'OGDH', 'OLFM1', 'OXR1', 'PACS1', 'PACS2', 'PAK6', 'PCDH1', 'PCDH10', 'PCDH7', 'PCDH9', 'PCDHA4', 'PCDHAC2', 'PCDHGA12', 'PCDHGC3', 'PCLO', 'PCNX', 'PCNXL2', 'PCNXL3', 'PDE2A', 'PDE4B', 'PDE4DIP', 'PDE8B', 'PDS5B', 'PDZD2', 'PDZD8', 'PEG3', 'PER1', 'PFKM', 'PGM2L1', 'PHACTR1', 'PHF12', 'PHF20', 'PHLDB1', 'PHYHIP', 'PI4KA', 'PIGQ', 'PIKFYVE', 'PINK1', 'PIP5K1C', 'PITPNM1', 'PITPNM2', 'PJA2', 'PKD1', 'PKP4', 'PLCB1', 'PLCH2', 'PLD3', 'PLEC', 'PLP1', 'PLXNA1', 'PLXNA2', 'PLXNA4', 'PLXNB1', 'PLXND1', 'POLR2A', 'PPARGC1A', 'PPFIA3', 'PPM1E', 'PPP1R9B', 'PPP2R1A', 'PPP2R2C', 'PPP2R5B', 'PPP3CA', 'PREX1', 'PREX2', 'PRICKLE2', 'PRKACB', 'PRKCB', 'PRKCE', 'PRKCG', 'PROSAPIP1', 'PRPF8', 'PRR12', 'PSAP', 'PSD', 'PTCH1', 'PTEN', 'PTK2', 'PTK2B', 'PTPN11', 'PTPN5', 'PTPRD', 'PTPRF', 'PTPRG', 'PTPRJ', 'PTPRN2', 'PTPRS', 'PTPRT', 'PUM1', 'PUM2', 'QKI', 'R3HDM1', 'R3HDM2', 'RALGAPA1', 'RALGAPB', 'RALGDS', 'RAP1GAP', 'RAP1GAP2', 'RAPGEF1', 'RAPGEF2', 'RAPGEF4', 'RAPGEFL1', 'RASGRF1', 'RASGRP1', 'RC3H1', 'RC3H2', 'RELN', 'RERE', 'REV3L', 'RGS7BP', 'RHOB', 'RHOBTB2', 'RICH2', 'RIMBP2', 'RPH3A', 'RPRD2', 'RPTOR', 'RTN1', 'RTN3', 'RTN4', 'RTN4R', 'RUSC1', 'RUSC2', 'RYR2', 'SALL2', 'SAMD4B', 'SAP130', 'SAPS1', 'SAPS2', 'SASH1', 'SBF1', 'SCAF1', 'SCAP', 'SCD2', 'SCN2A', 'SCN8A', 'SEC14L1', 'SEC16A', 'SEC23A', 'SECISBP2L', 'SEPT3', 'SEPT5', 'SETD5', 'SETX', 'SEZ6L2', 'SGIP1', 'SGSM2', 'SH3BP4', 'SHANK1', 'SHANK2', 'SHANK3', 'SIPA1L1', 'SIPA1L2', 'SIPA1L3', 'SKI', 'SLC12A5', 'SLC12A6', 'SLC17A7', 'SLC1A2', 'SLC22A17', 'SLC24A2', 'SLC25A23', 'SLC4A3', 'SLC4A4', 'SLC4A8', 'SLC6A1', 'SLC6A17', 'SLC8A1', 'SLC8A2', 'SLITRK5', 'SMARCA2', 'SMARCA4', 'SMARCC2', 'SMG1', 'SMPD3', 'SNAP25', 'SNAP91', 'SNPH', 'SOBP', 'SON', 'SORBS2', 'SORL1', 'SORT1', 'SPAG9', 'SPARCL1', 'SPEG', 'SPEN', 'SPHKAP', 'SPIRE1', 'SPRED1', 'SPRN', 'SPTAN1', 'SPTB', 'SPTBN1', 'SPTBN2', 'SRCIN1', 'SREBF2', 'SRGAP3', 'SRRM2', 'STK25', 'STOX2', 'STRN4', 'STXBP1', 'STXBP5', 'SUPT6H', 'SV2A', 'SV2B', 'SYMPK', 'SYN1', 'SYNE1', 'SYNGAP1', 'SYNGR1', 'SYNJ1', 'SYNPO', 'SYT1', 'SYT7', 'TANC2', 'TAOK1', 'TAOK2', 'TBC1D9', 'TBC1D9B', 'TCF20', 'TCF25', 'TCF4', 'TEF', 'THRA', 'TIAM1', 'TLE3', 'TLN2', 'TMEM132A', 'TMEM151A', 'TMEM151B', 'TMEM63B', 'TMEM8B', 'TMOD2', 'TNIK', 'TNK2', 'TNKS', 'TNPO2', 'TNRC18', 'TNRC6B', 'TNS3', 'TPPP', 'TRAK1', 'TRAK2', 'TRAPPC10', 'TRIL', 'TRIM2', 'TRIM3', 'TRIM32', 'TRIM37', 'TRIM9', 'TRIO', 'TRIP12', 'TRO', 'TRPC4AP', 'TRPM3', 'TRRAP', 'TSC2', 'TSC22D1', 'TSHZ1', 'TSPAN7', 'TSPYL4', 'TTBK1', 'TTBK2', 'TTC3', 'TTC7B', 'TTLL7', 'TTYH1', 'TTYH3', 'TUBB3', 'TUBB4', 'TULP4', 'UBA1', 'UBAP2L', 'UBE2O', 'UBE3B', 'UBE3C', 'UBQLN1', 'UBQLN2', 'UBR3', 'UBR5', 'UHRF1BP1L', 'ULK1', 'ULK2', 'UNC13A', 'UNC13C', 'UNC5A', 'UQCRC1', 'USP22', 'USP32', 'USP34', 'USP5', 'USP9X', 'VAMP2', 'VPS13D', 'VPS41', 'WASF1', 'WDFY3', 'WDR13', 'WDR6', 'WNK1', 'WNK2', 'WWC1', 'XPO6', 'XPO7', 'YWHAG', 'ZC3H4', 'ZC3H7B', 'ZCCHC14', 'ZEB2', 'ZER1', 'ZFHX2', 'ZFP106', 'ZFR', 'ZFYVE1', 'ZHX3', 'ZMIZ1', 'ZMIZ2', 'ZNF238', 'ZNF365', 'ZNF462', 'ZNF521', 'ZNF536', 'ZNF704', 'ZNF827', 'ZNFX1', 'ZYG11B')
  AND eg.effect_types IN ('missense')
LIMIT 1001
```

```sql
EXPLAIN ANALYSE WITH summary AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
  WHERE
    (
      sa.af_allele_freq >= 0 AND sa.af_allele_freq <= 5
    )
    AND sa.coding_bin = 1
    AND sa.frequency_bin IN (0, 1, 2)
    AND sa.allele_index > 0
),
family AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    fa.coding_bin = 1 AND fa.frequency_bin IN (0, 1, 2) AND fa.allele_index > 0
),
fullvariants AS (
SELECT
  fa.bucket_index as bucket_index,
  fa.summary_index as summary_index,
  fa.family_index as family_index,
  fa.allele_index as allele_index,
  sa.summary_variant_data as summary_variant_data,
  fa.family_variant_data as family_variant_data,
  eg.effect_gene_symbols as gene_symbol
FROM summary AS sa
JOIN family AS fa
  ON (
    fa.summary_index = sa.summary_index
    AND fa.bucket_index = sa.bucket_index
    AND fa.allele_index = sa.allele_index
  )
CROSS JOIN (
  SELECT
    UNNEST(effect_gene) AS eg
)
WHERE
  eg.effect_types IN ('missense')
)
SELECT
  bucket_index,
  summary_index,
  family_index,
  allele_index,
  summary_variant_data,
  family_variant_data
FROM fullvariants
WHERE
  gene_symbol IN ('AAK1', 'AATK', 'ABCA2', 'ABCA3', 'ABCG1', 'ABR', 'ACCN1', 'ACLY', 'ACO2', 'ACTB', 'ADAP1', 'ADARB1', 'ADCY1', 'ADCY5', 'ADD1', 'ADNP', 'ADRBK1', 'AFF3', 'AFF4', 'AGAP1', 'AGAP2', 'AGAP3', 'AGPAT3', 'AGRN', 'AGTPBP1', 'AHDC1', 'AKAP6', 'AKAP9', 'AKT3', 'ALDOA', 'ALDOC', 'ALS2', 'AMPH', 'ANAPC1', 'ANK1', 'ANK2', 'ANK3', 'ANKRD11', 'ANKRD17', 'ANKRD52', 'AP1B1', 'AP2A1', 'AP2A2', 'AP2B1', 'AP3D1', 'APBA1', 'APBB1', 'APC', 'APC2', 'APLP1', 'APOE', 'APP', 'ARAP2', 'ARF3', 'ARFGEF1', 'ARHGAP20', 'ARHGAP21', 'ARHGAP23', 'ARHGAP32', 'ARHGAP33', 'ARHGEF11', 'ARHGEF12', 'ARHGEF17', 'ARHGEF2', 'ARHGEF4', 'ARHGEF7', 'ARID1A', 'ARID1B', 'ARID2', 'ARNT2', 'ARPP21', 'ARRB1', 'ARVCF', 'ASH1L', 'ATF7IP', 'ATG2A', 'ATG2B', 'ATG9A', 'ATMIN', 'ATN1', 'ATP13A2', 'ATP1A1', 'ATP1A2', 'ATP1A3', 'ATP1B1', 'ATP2A2', 'ATP2B2', 'ATP2B4', 'ATP5A1', 'ATP5B', 'ATP6V0A1', 'ATP6V0D1', 'ATP6V1B2', 'ATP9A', 'ATXN1', 'AUTS2', 'B3GAT1', 'BAI1', 'BAI2', 'BAP1', 'BAT2', 'BAT2L1', 'BAT2L2', 'BAT3', 'BAZ2A', 'BCAN', 'BCL9L', 'BCR', 'BIRC6', 'BMPR2', 'BPTF', 'BRD4', 'BRSK1', 'BRSK2', 'BSN', 'BZRAP1', 'C11ORF41', 'C14ORF4', 'C19ORF26', 'C20ORF117', 'C20ORF12', 'C2CD2L', 'CABIN1', 'CACNA1A', 'CACNA1B', 'CACNA1E', 'CACNA1G', 'CACNA1I', 'CACNB1', 'CACNB3', 'CADPS', 'CALM1', 'CALM3', 'CAMK2A', 'CAMK2B', 'CAMK2N1', 'CAMKK2', 'CAMSAP1', 'CAMSAP1L1', 'CAMTA1', 'CAMTA2', 'CAND1', 'CASKIN1', 'CBX6', 'CBX6-NPTXR', 'CDC42BPA', 'CDC42BPB', 'CDK16', 'CDK17', 'CDK5R1', 'CDK5R2', 'CDKL5', 'CELF5', 'CELSR2', 'CELSR3', 'CHD3', 'CHD4', 'CHD5', 'CHD6', 'CHD8', 'CHN1', 'CHN2', 'CHST2', 'CIC', 'CIT', 'CKAP5', 'CKB', 'CLASP1', 'CLASP2', 'CLCN3', 'CLEC16A', 'CLIP3', 'CLSTN1', 'CLTC', 'CNP', 'COBL', 'COPG', 'CPE', 'CPLX1', 'CPLX2', 'CPT1C', 'CREBBP', 'CRMP1', 'CRTC1', 'CTBP1', 'CTNNB1', 'CTNND2', 'CUL9', 'CUX1', 'CUX2', 'CYFIP2', 'DAB2IP', 'DAGLA', 'DAPK1', 'DBC1', 'DCAF6', 'DCLK1', 'DCTN1', 'DDN', 'DDX24', 'DENND5A', 'DGCR2', 'DGKZ', 'DHX30', 'DICER1', 'DIDO1', 'DIP2A', 'DIP2B', 'DIP2C', 'DIRAS2', 'DISP2', 'DLC1', 'DLG2', 'DLG4', 'DLG5', 'DLGAP1', 'DLGAP2', 'DLGAP3', 'DLGAP4', 'DMWD', 'DMXL2', 'DNAJC6', 'DNM1', 'DOCK3', 'DOCK4', 'DOCK9', 'DOPEY1', 'DOPEY2', 'DOT1L', 'DPP8', 'DPYSL2', 'DSCAM', 'DSCAML1', 'DST', 'DTNA', 'DTX1', 'DUSP8', 'DYNC1H1', 'EEF1A2', 'EEF2', 'EGR1', 'EHMT1', 'EHMT2', 'EIF2C1', 'EIF2C2', 'EIF4G1', 'EIF4G2', 'EIF4G3', 'ELFN2', 'ELMO2', 'EML2', 'ENC1', 'EP300', 'EP400', 'EPB41L1', 'EPB49', 'EPHA4', 'EPN1', 'EXTL3', 'FAM115A', 'FAM120A', 'FAM160A2', 'FAM171B', 'FAM179B', 'FAM190B', 'FAM21A', 'FAM5B', 'FAM65A', 'FAM91A1', 'FASN', 'FAT1', 'FAT2', 'FAT3', 'FAT4', 'FBXL16', 'FBXL19', 'FBXO41', 'FCHO1', 'FKBP8', 'FOXK2', 'FOXO3', 'FRMPD4', 'FRY', 'FSCN1', 'FYN', 'GABBR1', 'GABBR2', 'GARNL3', 'GAS7', 'GBF1', 'GCN1L1', 'GIT1', 'GLUL', 'GM996', 'GNAL', 'GNAO1', 'GNAS', 'GNAZ', 'GNB1', 'GPAM', 'GPM6A', 'GPR158', 'GPR162', 'GPRIN1', 'GRAMD1B', 'GRIK3', 'GRIK5', 'GRIN1', 'GRIN2A', 'GRIN2B', 'GRLF1', 'GRM4', 'GRM5', 'GSK3B', 'GTF3C1', 'GTF3C2', 'HCFC1', 'HCN2', 'HDAC4', 'HDAC5', 'HDLBP', 'HEATR5B', 'HERC1', 'HERC2', 'HIPK1', 'HIPK2', 'HIPK3', 'HIVEP1', 'HIVEP2', 'HIVEP3', 'HK1', 'HMGXB3', 'HNRNPUL1', 'HSP90AB1', 'HTT', 'HUWE1', 'IDS', 'IGSF9B', 'INPP4A', 'INTS1', 'IPO13', 'IPO4', 'IPO5', 'IQSEC2', 'IQSEC3', 'IRS2', 'ITPR1', 'ITSN1', 'JAK1', 'JPH3', 'JPH4', 'KALRN', 'KCNA2', 'KCNB1', 'KCNC3', 'KCND2', 'KCNH1', 'KCNH3', 'KCNH7', 'KCNMA1', 'KCNQ2', 'KCNQ3', 'KCNT1', 'KDM4B', 'KDM5C', 'KDM6B', 'KIAA0090', 'KIAA0100', 'KIAA0226', 'KIAA0284', 'KIAA0317', 'KIAA0430', 'KIAA0664', 'KIAA0802', 'KIAA0913', 'KIAA0947', 'KIAA1045', 'KIAA1109', 'KIAA1244', 'KIAA1688', 'KIAA2018', 'KIF1A', 'KIF1B', 'KIF21A', 'KIF21B', 'KIF3C', 'KIF5A', 'KIF5C', 'KIFC2', 'KLC1', 'KLHL22', 'KNDC1', 'LARGE', 'LARS2', 'LHFPL4', 'LINGO1', 'LLGL1', 'LMTK2', 'LMTK3', 'LPHN1', 'LPHN3', 'LPIN2', 'LPPR4', 'LRP1', 'LRP3', 'LRP8', 'LRRC41', 'LRRC4B', 'LRRC68', 'LRRC7', 'LRRC8B', 'LRRN2', 'LYNX1', 'MACF1', 'MADD', 'MAGED1', 'MAGI2', 'MAN2A2', 'MAP1A', 'MAP1B', 'MAP2', 'MAP3K12', 'MAP4', 'MAP4K4', 'MAP7D1', 'MAPK1', 'MAPK4', 'MAPK8IP1', 'MAPK8IP3', 'MAPKBP1', 'MAST1', 'MAST2', 'MAST4', 'MAZ', 'MBD5', 'MBP', 'MED13', 'MED13L', 'MED14', 'MED16', 'MEF2D', 'MFHAS1', 'MGAT5B', 'MIB1', 'MICAL2', 'MINK1', 'MKL2', 'MLL', 'MLL2', 'MLL3', 'MLL5', 'MMP24', 'MON2', 'MPRIP', 'MTMR4', 'MTOR', 'MTSS1L', 'MYCBP2', 'MYH10', 'MYO10', 'MYO16', 'MYO18A', 'MYO5A', 'MYST3', 'MYT1L', 'NACAD', 'NAT8L', 'NAV1', 'NAV2', 'NAV3', 'NBEA', 'NCAM1', 'NCAN', 'NCDN', 'NCKAP1', 'NCOA1', 'NCOA2', 'NCOA6', 'NCOR1', 'NCOR2', 'NCS1', 'NDRG2', 'NDRG4', 'NDST1', 'NEDD4', 'NELF', 'NEURL', 'NEURL4', 'NF1', 'NFIC', 'NFIX', 'NGEF', 'NHSL1', 'NISCH', 'NLGN2', 'NLGN3', 'NOMO1', 'NPAS2', 'NPTXR', 'NR2F1', 'NRGN', 'NRIP1', 'NRXN1', 'NRXN2', 'NRXN3', 'NSD1', 'NSF', 'NTRK2', 'NTRK3', 'NUP98', 'NWD1', 'ODZ2', 'ODZ3', 'ODZ4', 'OGDH', 'OLFM1', 'OXR1', 'PACS1', 'PACS2', 'PAK6', 'PCDH1', 'PCDH10', 'PCDH7', 'PCDH9', 'PCDHA4', 'PCDHAC2', 'PCDHGA12', 'PCDHGC3', 'PCLO', 'PCNX', 'PCNXL2', 'PCNXL3', 'PDE2A', 'PDE4B', 'PDE4DIP', 'PDE8B', 'PDS5B', 'PDZD2', 'PDZD8', 'PEG3', 'PER1', 'PFKM', 'PGM2L1', 'PHACTR1', 'PHF12', 'PHF20', 'PHLDB1', 'PHYHIP', 'PI4KA', 'PIGQ', 'PIKFYVE', 'PINK1', 'PIP5K1C', 'PITPNM1', 'PITPNM2', 'PJA2', 'PKD1', 'PKP4', 'PLCB1', 'PLCH2', 'PLD3', 'PLEC', 'PLP1', 'PLXNA1', 'PLXNA2', 'PLXNA4', 'PLXNB1', 'PLXND1', 'POLR2A', 'PPARGC1A', 'PPFIA3', 'PPM1E', 'PPP1R9B', 'PPP2R1A', 'PPP2R2C', 'PPP2R5B', 'PPP3CA', 'PREX1', 'PREX2', 'PRICKLE2', 'PRKACB', 'PRKCB', 'PRKCE', 'PRKCG', 'PROSAPIP1', 'PRPF8', 'PRR12', 'PSAP', 'PSD', 'PTCH1', 'PTEN', 'PTK2', 'PTK2B', 'PTPN11', 'PTPN5', 'PTPRD', 'PTPRF', 'PTPRG', 'PTPRJ', 'PTPRN2', 'PTPRS', 'PTPRT', 'PUM1', 'PUM2', 'QKI', 'R3HDM1', 'R3HDM2', 'RALGAPA1', 'RALGAPB', 'RALGDS', 'RAP1GAP', 'RAP1GAP2', 'RAPGEF1', 'RAPGEF2', 'RAPGEF4', 'RAPGEFL1', 'RASGRF1', 'RASGRP1', 'RC3H1', 'RC3H2', 'RELN', 'RERE', 'REV3L', 'RGS7BP', 'RHOB', 'RHOBTB2', 'RICH2', 'RIMBP2', 'RPH3A', 'RPRD2', 'RPTOR', 'RTN1', 'RTN3', 'RTN4', 'RTN4R', 'RUSC1', 'RUSC2', 'RYR2', 'SALL2', 'SAMD4B', 'SAP130', 'SAPS1', 'SAPS2', 'SASH1', 'SBF1', 'SCAF1', 'SCAP', 'SCD2', 'SCN2A', 'SCN8A', 'SEC14L1', 'SEC16A', 'SEC23A', 'SECISBP2L', 'SEPT3', 'SEPT5', 'SETD5', 'SETX', 'SEZ6L2', 'SGIP1', 'SGSM2', 'SH3BP4', 'SHANK1', 'SHANK2', 'SHANK3', 'SIPA1L1', 'SIPA1L2', 'SIPA1L3', 'SKI', 'SLC12A5', 'SLC12A6', 'SLC17A7', 'SLC1A2', 'SLC22A17', 'SLC24A2', 'SLC25A23', 'SLC4A3', 'SLC4A4', 'SLC4A8', 'SLC6A1', 'SLC6A17', 'SLC8A1', 'SLC8A2', 'SLITRK5', 'SMARCA2', 'SMARCA4', 'SMARCC2', 'SMG1', 'SMPD3', 'SNAP25', 'SNAP91', 'SNPH', 'SOBP', 'SON', 'SORBS2', 'SORL1', 'SORT1', 'SPAG9', 'SPARCL1', 'SPEG', 'SPEN', 'SPHKAP', 'SPIRE1', 'SPRED1', 'SPRN', 'SPTAN1', 'SPTB', 'SPTBN1', 'SPTBN2', 'SRCIN1', 'SREBF2', 'SRGAP3', 'SRRM2', 'STK25', 'STOX2', 'STRN4', 'STXBP1', 'STXBP5', 'SUPT6H', 'SV2A', 'SV2B', 'SYMPK', 'SYN1', 'SYNE1', 'SYNGAP1', 'SYNGR1', 'SYNJ1', 'SYNPO', 'SYT1', 'SYT7', 'TANC2', 'TAOK1', 'TAOK2', 'TBC1D9', 'TBC1D9B', 'TCF20', 'TCF25', 'TCF4', 'TEF', 'THRA', 'TIAM1', 'TLE3', 'TLN2', 'TMEM132A', 'TMEM151A', 'TMEM151B', 'TMEM63B', 'TMEM8B', 'TMOD2', 'TNIK', 'TNK2', 'TNKS', 'TNPO2', 'TNRC18', 'TNRC6B', 'TNS3', 'TPPP', 'TRAK1', 'TRAK2', 'TRAPPC10', 'TRIL', 'TRIM2', 'TRIM3', 'TRIM32', 'TRIM37', 'TRIM9', 'TRIO', 'TRIP12', 'TRO', 'TRPC4AP', 'TRPM3', 'TRRAP', 'TSC2', 'TSC22D1', 'TSHZ1', 'TSPAN7', 'TSPYL4', 'TTBK1', 'TTBK2', 'TTC3', 'TTC7B', 'TTLL7', 'TTYH1', 'TTYH3', 'TUBB3', 'TUBB4', 'TULP4', 'UBA1', 'UBAP2L', 'UBE2O', 'UBE3B', 'UBE3C', 'UBQLN1', 'UBQLN2', 'UBR3', 'UBR5', 'UHRF1BP1L', 'ULK1', 'ULK2', 'UNC13A', 'UNC13C', 'UNC5A', 'UQCRC1', 'USP22', 'USP32', 'USP34', 'USP5', 'USP9X', 'VAMP2', 'VPS13D', 'VPS41', 'WASF1', 'WDFY3', 'WDR13', 'WDR6', 'WNK1', 'WNK2', 'WWC1', 'XPO6', 'XPO7', 'YWHAG', 'ZC3H4', 'ZC3H7B', 'ZCCHC14', 'ZEB2', 'ZER1', 'ZFHX2', 'ZFP106', 'ZFR', 'ZFYVE1', 'ZHX3', 'ZMIZ1', 'ZMIZ2', 'ZNF238', 'ZNF365', 'ZNF462', 'ZNF521', 'ZNF536', 'ZNF704', 'ZNF827', 'ZNFX1', 'ZYG11B')
```

```
┌─────────────────────────────────────┐                                                                                                                                                                               
│┌───────────────────────────────────┐│                                                                                                                                                                               
││         Total Time: 14.50s        ││                                                                                                                                                                               
│└───────────────────────────────────┘│                                                                                                                                                                               
└─────────────────────────────────────┘                                                                                                                                                                               
                                                                                                                                                                     

```


```sql
EXPLAIN ANALYSE WITH summary AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
  WHERE
    (
      sa.af_allele_freq >= 0 AND sa.af_allele_freq <= 5
    )
    AND sa.coding_bin = 1
    AND sa.frequency_bin IN (0, 1, 2)
    AND sa.allele_index > 0
),
family AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    fa.coding_bin = 1 AND fa.frequency_bin IN (0, 1, 2) AND fa.allele_index > 0
),
fullvariants AS (
SELECT
  fa.bucket_index as bucket_index,
  fa.summary_index as summary_index,
  fa.family_index as family_index,
  fa.allele_index as allele_index,
  sa.summary_variant_data as summary_variant_data,
  fa.family_variant_data as family_variant_data,
  eg.effect_gene_symbols as gene_symbol
FROM summary AS sa
JOIN family AS fa
  ON (
    fa.summary_index = sa.summary_index
    AND fa.bucket_index = sa.bucket_index
    AND fa.allele_index = sa.allele_index
  )
CROSS JOIN (
  SELECT
    UNNEST(effect_gene) AS eg
)
WHERE
  eg.effect_types IN ('missense')
)
SELECT
  bucket_index,
  summary_index,
  family_index,
  allele_index,
  summary_variant_data,
  family_variant_data
FROM fullvariants
```


```sql
SELECT
  bucket_index,
  summary_index ,
  allele_index,
  UNNEST(effect_gene)
FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
WHERE
(
    sa.af_allele_freq >= 0 AND sa.af_allele_freq <= 5
)
AND sa.coding_bin = 1
AND sa.frequency_bin IN (0, 1, 2)
AND sa.allele_index > 0
AND sa.effect_gene.effect_types = 'missense'
LIMIT 10
```



```sql
EXPLAIN ANALYSE WITH summary AS (
  SELECT
    bucket_index,
    summary_index,
    allele_index,
    UNNEST(effect_gene, recursive := true),
    summary_variant_data
  FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
  WHERE
    (
      af_allele_freq >= 0 AND af_allele_freq <= 5
    )
    AND coding_bin = 1
    AND frequency_bin IN (0, 1, 2)
    AND allele_index > 0
),
effect_gene_summary AS (
SELECT * from summary as sa
WHERE
    sa.effect_types IN ('missense') AND
    sa.effect_gene_symbols IN ('AAK1', 'AATK', 'ABCA2', 'ABCA3', 'ABCG1', 'ABR', 'ACCN1', 'ACLY', 'ACO2', 'ACTB', 'ADAP1', 'ADARB1', 'ADCY1', 'ADCY5', 'ADD1', 'ADNP', 'ADRBK1', 'AFF3', 'AFF4', 'AGAP1', 'AGAP2', 'AGAP3', 'AGPAT3', 'AGRN', 'AGTPBP1', 'AHDC1', 'AKAP6', 'AKAP9', 'AKT3', 'ALDOA', 'ALDOC', 'ALS2', 'AMPH', 'ANAPC1', 'ANK1', 'ANK2', 'ANK3', 'ANKRD11', 'ANKRD17', 'ANKRD52', 'AP1B1', 'AP2A1', 'AP2A2', 'AP2B1', 'AP3D1', 'APBA1', 'APBB1', 'APC', 'APC2', 'APLP1', 'APOE', 'APP', 'ARAP2', 'ARF3', 'ARFGEF1', 'ARHGAP20', 'ARHGAP21', 'ARHGAP23', 'ARHGAP32', 'ARHGAP33', 'ARHGEF11', 'ARHGEF12', 'ARHGEF17', 'ARHGEF2', 'ARHGEF4', 'ARHGEF7', 'ARID1A', 'ARID1B', 'ARID2', 'ARNT2', 'ARPP21', 'ARRB1', 'ARVCF', 'ASH1L', 'ATF7IP', 'ATG2A', 'ATG2B', 'ATG9A', 'ATMIN', 'ATN1', 'ATP13A2', 'ATP1A1', 'ATP1A2', 'ATP1A3', 'ATP1B1', 'ATP2A2', 'ATP2B2', 'ATP2B4', 'ATP5A1', 'ATP5B', 'ATP6V0A1', 'ATP6V0D1', 'ATP6V1B2', 'ATP9A', 'ATXN1', 'AUTS2', 'B3GAT1', 'BAI1', 'BAI2', 'BAP1', 'BAT2', 'BAT2L1', 'BAT2L2', 'BAT3', 'BAZ2A', 'BCAN', 'BCL9L', 'BCR', 'BIRC6', 'BMPR2', 'BPTF', 'BRD4', 'BRSK1', 'BRSK2', 'BSN', 'BZRAP1', 'C11ORF41', 'C14ORF4', 'C19ORF26', 'C20ORF117', 'C20ORF12', 'C2CD2L', 'CABIN1', 'CACNA1A', 'CACNA1B', 'CACNA1E', 'CACNA1G', 'CACNA1I', 'CACNB1', 'CACNB3', 'CADPS', 'CALM1', 'CALM3', 'CAMK2A', 'CAMK2B', 'CAMK2N1', 'CAMKK2', 'CAMSAP1', 'CAMSAP1L1', 'CAMTA1', 'CAMTA2', 'CAND1', 'CASKIN1', 'CBX6', 'CBX6-NPTXR', 'CDC42BPA', 'CDC42BPB', 'CDK16', 'CDK17', 'CDK5R1', 'CDK5R2', 'CDKL5', 'CELF5', 'CELSR2', 'CELSR3', 'CHD3', 'CHD4', 'CHD5', 'CHD6', 'CHD8', 'CHN1', 'CHN2', 'CHST2', 'CIC', 'CIT', 'CKAP5', 'CKB', 'CLASP1', 'CLASP2', 'CLCN3', 'CLEC16A', 'CLIP3', 'CLSTN1', 'CLTC', 'CNP', 'COBL', 'COPG', 'CPE', 'CPLX1', 'CPLX2', 'CPT1C', 'CREBBP', 'CRMP1', 'CRTC1', 'CTBP1', 'CTNNB1', 'CTNND2', 'CUL9', 'CUX1', 'CUX2', 'CYFIP2', 'DAB2IP', 'DAGLA', 'DAPK1', 'DBC1', 'DCAF6', 'DCLK1', 'DCTN1', 'DDN', 'DDX24', 'DENND5A', 'DGCR2', 'DGKZ', 'DHX30', 'DICER1', 'DIDO1', 'DIP2A', 'DIP2B', 'DIP2C', 'DIRAS2', 'DISP2', 'DLC1', 'DLG2', 'DLG4', 'DLG5', 'DLGAP1', 'DLGAP2', 'DLGAP3', 'DLGAP4', 'DMWD', 'DMXL2', 'DNAJC6', 'DNM1', 'DOCK3', 'DOCK4', 'DOCK9', 'DOPEY1', 'DOPEY2', 'DOT1L', 'DPP8', 'DPYSL2', 'DSCAM', 'DSCAML1', 'DST', 'DTNA', 'DTX1', 'DUSP8', 'DYNC1H1', 'EEF1A2', 'EEF2', 'EGR1', 'EHMT1', 'EHMT2', 'EIF2C1', 'EIF2C2', 'EIF4G1', 'EIF4G2', 'EIF4G3', 'ELFN2', 'ELMO2', 'EML2', 'ENC1', 'EP300', 'EP400', 'EPB41L1', 'EPB49', 'EPHA4', 'EPN1', 'EXTL3', 'FAM115A', 'FAM120A', 'FAM160A2', 'FAM171B', 'FAM179B', 'FAM190B', 'FAM21A', 'FAM5B', 'FAM65A', 'FAM91A1', 'FASN', 'FAT1', 'FAT2', 'FAT3', 'FAT4', 'FBXL16', 'FBXL19', 'FBXO41', 'FCHO1', 'FKBP8', 'FOXK2', 'FOXO3', 'FRMPD4', 'FRY', 'FSCN1', 'FYN', 'GABBR1', 'GABBR2', 'GARNL3', 'GAS7', 'GBF1', 'GCN1L1', 'GIT1', 'GLUL', 'GM996', 'GNAL', 'GNAO1', 'GNAS', 'GNAZ', 'GNB1', 'GPAM', 'GPM6A', 'GPR158', 'GPR162', 'GPRIN1', 'GRAMD1B', 'GRIK3', 'GRIK5', 'GRIN1', 'GRIN2A', 'GRIN2B', 'GRLF1', 'GRM4', 'GRM5', 'GSK3B', 'GTF3C1', 'GTF3C2', 'HCFC1', 'HCN2', 'HDAC4', 'HDAC5', 'HDLBP', 'HEATR5B', 'HERC1', 'HERC2', 'HIPK1', 'HIPK2', 'HIPK3', 'HIVEP1', 'HIVEP2', 'HIVEP3', 'HK1', 'HMGXB3', 'HNRNPUL1', 'HSP90AB1', 'HTT', 'HUWE1', 'IDS', 'IGSF9B', 'INPP4A', 'INTS1', 'IPO13', 'IPO4', 'IPO5', 'IQSEC2', 'IQSEC3', 'IRS2', 'ITPR1', 'ITSN1', 'JAK1', 'JPH3', 'JPH4', 'KALRN', 'KCNA2', 'KCNB1', 'KCNC3', 'KCND2', 'KCNH1', 'KCNH3', 'KCNH7', 'KCNMA1', 'KCNQ2', 'KCNQ3', 'KCNT1', 'KDM4B', 'KDM5C', 'KDM6B', 'KIAA0090', 'KIAA0100', 'KIAA0226', 'KIAA0284', 'KIAA0317', 'KIAA0430', 'KIAA0664', 'KIAA0802', 'KIAA0913', 'KIAA0947', 'KIAA1045', 'KIAA1109', 'KIAA1244', 'KIAA1688', 'KIAA2018', 'KIF1A', 'KIF1B', 'KIF21A', 'KIF21B', 'KIF3C', 'KIF5A', 'KIF5C', 'KIFC2', 'KLC1', 'KLHL22', 'KNDC1', 'LARGE', 'LARS2', 'LHFPL4', 'LINGO1', 'LLGL1', 'LMTK2', 'LMTK3', 'LPHN1', 'LPHN3', 'LPIN2', 'LPPR4', 'LRP1', 'LRP3', 'LRP8', 'LRRC41', 'LRRC4B', 'LRRC68', 'LRRC7', 'LRRC8B', 'LRRN2', 'LYNX1', 'MACF1', 'MADD', 'MAGED1', 'MAGI2', 'MAN2A2', 'MAP1A', 'MAP1B', 'MAP2', 'MAP3K12', 'MAP4', 'MAP4K4', 'MAP7D1', 'MAPK1', 'MAPK4', 'MAPK8IP1', 'MAPK8IP3', 'MAPKBP1', 'MAST1', 'MAST2', 'MAST4', 'MAZ', 'MBD5', 'MBP', 'MED13', 'MED13L', 'MED14', 'MED16', 'MEF2D', 'MFHAS1', 'MGAT5B', 'MIB1', 'MICAL2', 'MINK1', 'MKL2', 'MLL', 'MLL2', 'MLL3', 'MLL5', 'MMP24', 'MON2', 'MPRIP', 'MTMR4', 'MTOR', 'MTSS1L', 'MYCBP2', 'MYH10', 'MYO10', 'MYO16', 'MYO18A', 'MYO5A', 'MYST3', 'MYT1L', 'NACAD', 'NAT8L', 'NAV1', 'NAV2', 'NAV3', 'NBEA', 'NCAM1', 'NCAN', 'NCDN', 'NCKAP1', 'NCOA1', 'NCOA2', 'NCOA6', 'NCOR1', 'NCOR2', 'NCS1', 'NDRG2', 'NDRG4', 'NDST1', 'NEDD4', 'NELF', 'NEURL', 'NEURL4', 'NF1', 'NFIC', 'NFIX', 'NGEF', 'NHSL1', 'NISCH', 'NLGN2', 'NLGN3', 'NOMO1', 'NPAS2', 'NPTXR', 'NR2F1', 'NRGN', 'NRIP1', 'NRXN1', 'NRXN2', 'NRXN3', 'NSD1', 'NSF', 'NTRK2', 'NTRK3', 'NUP98', 'NWD1', 'ODZ2', 'ODZ3', 'ODZ4', 'OGDH', 'OLFM1', 'OXR1', 'PACS1', 'PACS2', 'PAK6', 'PCDH1', 'PCDH10', 'PCDH7', 'PCDH9', 'PCDHA4', 'PCDHAC2', 'PCDHGA12', 'PCDHGC3', 'PCLO', 'PCNX', 'PCNXL2', 'PCNXL3', 'PDE2A', 'PDE4B', 'PDE4DIP', 'PDE8B', 'PDS5B', 'PDZD2', 'PDZD8', 'PEG3', 'PER1', 'PFKM', 'PGM2L1', 'PHACTR1', 'PHF12', 'PHF20', 'PHLDB1', 'PHYHIP', 'PI4KA', 'PIGQ', 'PIKFYVE', 'PINK1', 'PIP5K1C', 'PITPNM1', 'PITPNM2', 'PJA2', 'PKD1', 'PKP4', 'PLCB1', 'PLCH2', 'PLD3', 'PLEC', 'PLP1', 'PLXNA1', 'PLXNA2', 'PLXNA4', 'PLXNB1', 'PLXND1', 'POLR2A', 'PPARGC1A', 'PPFIA3', 'PPM1E', 'PPP1R9B', 'PPP2R1A', 'PPP2R2C', 'PPP2R5B', 'PPP3CA', 'PREX1', 'PREX2', 'PRICKLE2', 'PRKACB', 'PRKCB', 'PRKCE', 'PRKCG', 'PROSAPIP1', 'PRPF8', 'PRR12', 'PSAP', 'PSD', 'PTCH1', 'PTEN', 'PTK2', 'PTK2B', 'PTPN11', 'PTPN5', 'PTPRD', 'PTPRF', 'PTPRG', 'PTPRJ', 'PTPRN2', 'PTPRS', 'PTPRT', 'PUM1', 'PUM2', 'QKI', 'R3HDM1', 'R3HDM2', 'RALGAPA1', 'RALGAPB', 'RALGDS', 'RAP1GAP', 'RAP1GAP2', 'RAPGEF1', 'RAPGEF2', 'RAPGEF4', 'RAPGEFL1', 'RASGRF1', 'RASGRP1', 'RC3H1', 'RC3H2', 'RELN', 'RERE', 'REV3L', 'RGS7BP', 'RHOB', 'RHOBTB2', 'RICH2', 'RIMBP2', 'RPH3A', 'RPRD2', 'RPTOR', 'RTN1', 'RTN3', 'RTN4', 'RTN4R', 'RUSC1', 'RUSC2', 'RYR2', 'SALL2', 'SAMD4B', 'SAP130', 'SAPS1', 'SAPS2', 'SASH1', 'SBF1', 'SCAF1', 'SCAP', 'SCD2', 'SCN2A', 'SCN8A', 'SEC14L1', 'SEC16A', 'SEC23A', 'SECISBP2L', 'SEPT3', 'SEPT5', 'SETD5', 'SETX', 'SEZ6L2', 'SGIP1', 'SGSM2', 'SH3BP4', 'SHANK1', 'SHANK2', 'SHANK3', 'SIPA1L1', 'SIPA1L2', 'SIPA1L3', 'SKI', 'SLC12A5', 'SLC12A6', 'SLC17A7', 'SLC1A2', 'SLC22A17', 'SLC24A2', 'SLC25A23', 'SLC4A3', 'SLC4A4', 'SLC4A8', 'SLC6A1', 'SLC6A17', 'SLC8A1', 'SLC8A2', 'SLITRK5', 'SMARCA2', 'SMARCA4', 'SMARCC2', 'SMG1', 'SMPD3', 'SNAP25', 'SNAP91', 'SNPH', 'SOBP', 'SON', 'SORBS2', 'SORL1', 'SORT1', 'SPAG9', 'SPARCL1', 'SPEG', 'SPEN', 'SPHKAP', 'SPIRE1', 'SPRED1', 'SPRN', 'SPTAN1', 'SPTB', 'SPTBN1', 'SPTBN2', 'SRCIN1', 'SREBF2', 'SRGAP3', 'SRRM2', 'STK25', 'STOX2', 'STRN4', 'STXBP1', 'STXBP5', 'SUPT6H', 'SV2A', 'SV2B', 'SYMPK', 'SYN1', 'SYNE1', 'SYNGAP1', 'SYNGR1', 'SYNJ1', 'SYNPO', 'SYT1', 'SYT7', 'TANC2', 'TAOK1', 'TAOK2', 'TBC1D9', 'TBC1D9B', 'TCF20', 'TCF25', 'TCF4', 'TEF', 'THRA', 'TIAM1', 'TLE3', 'TLN2', 'TMEM132A', 'TMEM151A', 'TMEM151B', 'TMEM63B', 'TMEM8B', 'TMOD2', 'TNIK', 'TNK2', 'TNKS', 'TNPO2', 'TNRC18', 'TNRC6B', 'TNS3', 'TPPP', 'TRAK1', 'TRAK2', 'TRAPPC10', 'TRIL', 'TRIM2', 'TRIM3', 'TRIM32', 'TRIM37', 'TRIM9', 'TRIO', 'TRIP12', 'TRO', 'TRPC4AP', 'TRPM3', 'TRRAP', 'TSC2', 'TSC22D1', 'TSHZ1', 'TSPAN7', 'TSPYL4', 'TTBK1', 'TTBK2', 'TTC3', 'TTC7B', 'TTLL7', 'TTYH1', 'TTYH3', 'TUBB3', 'TUBB4', 'TULP4', 'UBA1', 'UBAP2L', 'UBE2O', 'UBE3B', 'UBE3C', 'UBQLN1', 'UBQLN2', 'UBR3', 'UBR5', 'UHRF1BP1L', 'ULK1', 'ULK2', 'UNC13A', 'UNC13C', 'UNC5A', 'UQCRC1', 'USP22', 'USP32', 'USP34', 'USP5', 'USP9X', 'VAMP2', 'VPS13D', 'VPS41', 'WASF1', 'WDFY3', 'WDR13', 'WDR6', 'WNK1', 'WNK2', 'WWC1', 'XPO6', 'XPO7', 'YWHAG', 'ZC3H4', 'ZC3H7B', 'ZCCHC14', 'ZEB2', 'ZER1', 'ZFHX2', 'ZFP106', 'ZFR', 'ZFYVE1', 'ZHX3', 'ZMIZ1', 'ZMIZ2', 'ZNF238', 'ZNF365', 'ZNF462', 'ZNF521', 'ZNF536', 'ZNF704', 'ZNF827', 'ZNFX1', 'ZYG11B')    
),
family AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    fa.coding_bin = 1 AND fa.frequency_bin IN (0, 1, 2) AND fa.allele_index > 0
)
SELECT
  fa.bucket_index as bucket_index,
  fa.summary_index as summary_index,
  fa.family_index as family_index,
  fa.allele_index as allele_index,
  sa.summary_variant_data as summary_variant_data,
  fa.family_variant_data as family_variant_data,
FROM effect_gene_summary AS sa
JOIN family AS fa
  ON (
    fa.summary_index = sa.summary_index
    AND fa.bucket_index = sa.bucket_index
    AND fa.allele_index = sa.allele_index
  )
```



```sql
WITH
effect_gene AS (
SELECT
  UNNEST(effect_gene, recursive := true)
FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
)
SELECT * FROM effect_gene AS eg
WHERE
eg.effect_types = 'missense'
LIMIT 10;
```


```sql
SELECT COUNT(*) FROM AGRE_WG38_CSHL_859_SCHEMA2_summary
CROSS JOIN (
  SELECT
    UNNEST(effect_gene) AS eg
)
```

```sql
SELECT effect_gene FROM AGRE_WG38_CSHL_859_SCHEMA2_summary WHERE length(effect_gene) > 10 LIMIT 10;
```

```sql
select count(*) from AGRE_WG38_CSHL_859_SCHEMA2_summary where length(effect_gene) = 0;
```


```sql
EXPLAIN ANALYZE WITH summary AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
  WHERE
    (
      sa.af_allele_count <= 1 OR sa.af_allele_count IS NULL
    )
    AND sa.coding_bin = 1
    AND sa.frequency_bin IN (0, 1)
    AND sa.allele_index > 0
), effect_gene AS (
  SELECT
    *,
    UNNEST(effect_gene) AS eg
  FROM summary
), effect_gene_summary AS (
  SELECT
    *
  FROM effect_gene
  WHERE
    eg.effect_types IN ('frame-shift', 'nonsense', 'splice-site', 'no-frame-shift-newStop')
), family_bins AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    fa.coding_bin = 1
    AND fa.frequency_bin IN (0, 1)
),
family AS (
  SELECT * FROM family_bins as fa WHERE
    (
      (
        (
          fa.allele_in_roles & 128
        ) <> 0
      )
      AND (
        (
          NOT (
            (
              fa.allele_in_roles & 256
            ) <> 0
          )
        )
      )
    )
    OR (
      (
        (
          fa.allele_in_roles & 128
        ) <> 0
      )
      AND (
        (
          fa.allele_in_roles & 256
        ) <> 0
      )
    )
    AND (
      8 & fa.inheritance_in_members
    ) = 0
    AND (
      32 & fa.inheritance_in_members
    ) = 0
    AND (
      150 & fa.inheritance_in_members
    ) <> 0
    AND fa.allele_index > 0
)
SELECT
  fa.bucket_index,
  fa.summary_index,
  fa.family_index,
  sa.allele_index,
  sa.summary_variant_data,
  fa.family_variant_data
FROM summary AS sa
LEFT JOIN family AS fa
  ON (
    fa.summary_index = sa.summary_index
    AND fa.bucket_index = sa.bucket_index
    AND fa.allele_index = sa.allele_index
  )

```

```sql
WITH family_bins AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    fa.coding_bin = 1
    AND fa.frequency_bin IN (0, 1)
)
SELECT count(*) FROM family_bins AS fa WHERE
    (
      (
        (
          fa.allele_in_roles & 128
        ) <> 0
      )
      AND (
        (
          NOT (
            (
              fa.allele_in_roles & 256
            ) <> 0
          )
        )
      )
    )
    OR (
      (
        (
          fa.allele_in_roles & 128
        ) <> 0
      )
      AND (
        (
          fa.allele_in_roles & 256
        ) <> 0
      )
    )
    AND (
      8 & fa.inheritance_in_members
    ) = 0
    AND (
      32 & fa.inheritance_in_members
    ) = 0
    AND (
      150 & fa.inheritance_in_members
    ) <> 0
    AND fa.allele_index > 0

```


```sql
WITH summary AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
  WHERE
    (
      sa.af_allele_count <= 1 OR sa.af_allele_count IS NULL
    )
    AND sa.coding_bin = 1
    AND sa.frequency_bin IN (0, 1)
    AND sa.allele_index > 0
), effect_gene AS (
  SELECT
    *,
    UNNEST(effect_gene) AS eg
  FROM summary
), effect_gene_summary AS (
  SELECT
    *
  FROM effect_gene
  WHERE
    eg.effect_types IN ('frame-shift', 'nonsense', 'splice-site', 'no-frame-shift-newStop')
), family_bins AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    fa.coding_bin = 1 AND fa.frequency_bin IN (0, 1)
), family AS (
  SELECT
    *
  FROM family_bins AS fa
  WHERE
    (
      (
        (
          fa.allele_in_roles & 128
        ) <> 0
      )
      AND (
        (
          NOT (
            (
              fa.allele_in_roles & 256
            ) <> 0
          )
        )
      )
    )
    OR (
      (
        (
          fa.allele_in_roles & 128
        ) <> 0
      )
      AND (
        (
          fa.allele_in_roles & 256
        ) <> 0
      )
    )
    AND (
      8 & fa.inheritance_in_members
    ) = 0
    AND (
      32 & fa.inheritance_in_members
    ) = 0
    AND (
      150 & fa.inheritance_in_members
    ) <> 0
    AND fa.allele_index > 0
)
SELECT
  fa.bucket_index,
  fa.summary_index,
  fa.family_index,
  sa.allele_index
FROM effect_gene_summary AS sa
JOIN family AS fa
  ON (
    fa.summary_index = sa.summary_index
    AND fa.bucket_index = sa.bucket_index
    AND fa.allele_index = sa.allele_index
  )
```

```sql
WITH summary AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
  WHERE
    (
      sa.af_allele_count <= 1 OR sa.af_allele_count IS NULL
    )
    AND sa.coding_bin = 1
    AND sa.frequency_bin IN (0, 1)
    AND sa.allele_index > 0
), effect_gene AS (
  SELECT
    *,
    UNNEST(effect_gene) AS eg
  FROM summary
), effect_gene_summary AS (
  SELECT
    *
  FROM effect_gene
  WHERE
    eg.effect_types IN ('frame-shift', 'nonsense', 'splice-site', 'no-frame-shift-newStop')
), family_bins AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    fa.coding_bin = 1 AND fa.frequency_bin IN (0, 1)
), family AS (
  SELECT
    *
  FROM family_bins AS fa
  WHERE
    (
      (
        (
          fa.allele_in_roles & 128
        ) <> 0
      )
      AND (
        (
          NOT (
            (
              fa.allele_in_roles & 256
            ) <> 0
          )
        )
      )
    )
    OR (
      (
        (
          fa.allele_in_roles & 128
        ) <> 0
      )
      AND (
        (
          fa.allele_in_roles & 256
        ) <> 0
      )
    )
    AND (
      8 & fa.inheritance_in_members
    ) = 0
    AND (
      32 & fa.inheritance_in_members
    ) = 0
    AND (
      150 & fa.inheritance_in_members
    ) <> 0
    AND fa.allele_index > 0
)
SELECT
    count(*)
FROM effect_gene_summary AS sa
JOIN family AS fa
  ON (
    fa.summary_index = sa.summary_index
    AND fa.bucket_index = sa.bucket_index
    AND fa.allele_index = sa.allele_index
  );
```

```sql
EXPLAIN ANALYZE WITH summary AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
  WHERE
    (
      sa.chromosome = 'chr1'
      AND NOT (
        COALESCE(sa.end_position, sa.position) < 151402724 OR sa.position > 151459465
      )
    )
    AND (
      sa.af_allele_freq <= 100
    )
    AND sa.region_bin = 'chr1_3'
    AND sa.allele_index > 0
), effect_gene AS (
  SELECT
    *,
    UNNEST(effect_gene) AS eg
  FROM summary
), effect_gene_summary AS (
  SELECT
    *
  FROM effect_gene
  WHERE
    eg.effect_gene_symbols IN ('POGZ')
    AND eg.effect_types IN ('frame-shift', 'nonsense', 'splice-site', 'no-frame-shift-newStop', 'missense', 'synonymous', 'CNV+', 'CNV-', 'no-frame-shift', 'noEnd', 'noStart', 'CDS')
), family_bins AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    fa.region_bin = 'chr1_3'
), family AS (
  SELECT
    *
  FROM family_bins AS fa
  WHERE
    (
      8 & fa.inheritance_in_members
    ) = 0
    AND (
      32 & fa.inheritance_in_members
    ) = 0
    AND (
      150 & fa.inheritance_in_members
    ) <> 0
    AND fa.allele_index > 0
)
SELECT
  fa.bucket_index,
  fa.summary_index,
  fa.family_index,
  sa.allele_index,
  sa.summary_variant_data,
  fa.family_variant_data
FROM effect_gene_summary AS sa
JOIN family AS fa
  ON (
    fa.summary_index = sa.summary_index
    AND fa.bucket_index = sa.bucket_index
    AND fa.allele_index = sa.allele_index
  )
```

```sql
EXPLAIN ANALYZE WITH summary AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
  WHERE
    sa.allele_index > 0 AND sa.region_bin = 'chr1_0'
), family AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    fa.region_bin = 'chr1_0'
    AND (
      8 & fa.inheritance_in_members
    ) = 0
    AND (
      32 & fa.inheritance_in_members
    ) = 0
    AND (
      150 & fa.inheritance_in_members
    ) <> 0
    AND fa.allele_index > 0
)
SELECT
  fa.bucket_index,
  fa.summary_index,
  fa.family_index,
  sa.allele_index,
  sa.summary_variant_data,
  fa.family_variant_data
FROM summary AS sa
LEFT JOIN family AS fa
  ON (
    fa.region_bin = sa.region_bin
    AND fa.coding_bin = sa.coding_bin
    AND fa.frequency_bin = sa.frequency_bin
    AND fa.summary_index = sa.summary_index
    AND fa.bucket_index = sa.bucket_index
    AND fa.allele_index = sa.allele_index
  )
LIMIT 10010
```


Get all variants query:

```sql
EXPLAIN WITH summary AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
  WHERE
    sa.allele_index > 0
), effect_gene AS (
  SELECT
    *,
    UNNEST(effect_gene) AS eg
  FROM summary
), effect_gene_summary AS (
  SELECT
    *
  FROM effect_gene
  WHERE
    eg.effect_types IN ('3''UTR', '3''UTR-intron', '5''UTR', '5''UTR-intron', 'frame-shift', 'intergenic', 'intron', 'missense', 'no-frame-shift', 'no-frame-shift-newStop', 'noEnd', 'noStart', 'non-coding', 'non-coding-intron', 'nonsense', 'splice-site', 'synonymous', 'CDS', 'CNV+', 'CNV-')
), family AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    (
      8 & fa.inheritance_in_members
    ) = 0
    AND (
      32 & fa.inheritance_in_members
    ) = 0
    AND (
      150 & fa.inheritance_in_members
    ) <> 0
    AND fa.allele_index > 0
)
SELECT
  fa.bucket_index,
  fa.summary_index,
  fa.family_index,
  sa.allele_index,
  sa.summary_variant_data,
  fa.family_variant_data
FROM effect_gene_summary AS sa
JOIN family AS fa
  ON (
    fa.summary_index = sa.summary_index
    AND fa.bucket_index = sa.bucket_index
    AND fa.allele_index = sa.allele_index
  )
```

```
┌─────────────────────────────┐                                                        
│┌───────────────────────────┐│                                                        
││       Physical Plan       ││                                                        
│└───────────────────────────┘│                                                        
└─────────────────────────────┘                                                        
┌───────────────────────────┐                                                          
│         PROJECTION        │                                                          
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                                                          
│        bucket_index       │                                                          
│       summary_index       │                                                          
│        family_index       │                                                          
│        allele_index       │                                                                                                                                                                                         
│    summary_variant_data   │                                                          
│    family_variant_data    │                                                          
└─────────────┬─────────────┘                                                                                        
┌─────────────┴─────────────┐                                                          
│         HASH_JOIN         │                                                          
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                                                          
│           INNER           │                                                          
│allele_index = allele_index│                                                          
│bucket_index = bucket_index├──────────────┐                                           
│      summary_index =      │              │                                           
│        summary_index      │              │                                           
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │              │                                           
│      EC: 72278842322      │              │                                           
└─────────────┬─────────────┘              │                                                                         
┌─────────────┴─────────────┐┌─────────────┴─────────────┐                             
│         PROJECTION        ││         PROJECTION        │                             
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ││   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
│        bucket_index       ││             #0            │                             
│       summary_index       ││             #1            │                             
│        allele_index       ││             #2            │                             
│        family_index       ││             #3            │                             
│    family_variant_data    ││                           │                             
└─────────────┬─────────────┘└─────────────┬─────────────┘                                                           
┌─────────────┴─────────────┐┌─────────────┴─────────────┐                             
│           FILTER          ││           FILTER          │                             
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ││   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
│        (((8 & CAST        ││    (allele_index >= 1)    │                             
│(inheritance_in_member...  ││   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
│       AND ((32 & CAST     ││        EC: 29419412       │                             
│(inheritance_in_member...  ││                           │                             
│     ) AND ((150 & CAST    ││                           │                             
│(inheritance_in_member...  ││                           │                             
│           != 0))          ││                           │                             
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ││                           │                             
│       EC: 875011592       ││                           │                             
└─────────────┬─────────────┘└─────────────┬─────────────┘                                                           
┌─────────────┴─────────────┐┌─────────────┴─────────────┐                             
│         SEQ_SCAN          ││         PROJECTION        │                             
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ││   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
│AGRE_WG38_CSHL_859_SCHEMA2_││             #0            │                             
│           family          ││             #1            │                             
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ││             #2            │                             
│   inheritance_in_members  ││             #4            │                             
│        allele_index       ││             #6            │                             
│        bucket_index       ││                           │                             
│       summary_index       ││                           │                             
│        family_index       ││                           │                             
│    family_variant_data    ││                           │                             
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ││                           │                             
│       EC: 875011592       ││                           │                             
└───────────────────────────┘└─────────────┬─────────────┘                                                           
                             ┌─────────────┴─────────────┐                             
                             │           FILTER          │                             
                             │   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
                             │(IN (...) AND (allele_index│                             
                             │            > 0))          │                             
                             │   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
                             │        EC: 29419412       │                             
                             └─────────────┬─────────────┘                                                           
                             ┌─────────────┴─────────────┐                             
                             │         HASH_JOIN         │                             
                             │   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
                             │            MARK           │                             
                             │    struct_extract(eg,     ├──────────────┐              
                             │    'effect_types') = #0   │              │              
                             │   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │              │              
                             │        EC: 29419412       │              │              
                             └─────────────┬─────────────┘                     │                                            
                             ┌─────────────┴─────────────┐┌─────────────┴─────────────┐
                             │           UNNEST          ││      COLUMN_DATA_SCAN     │
                             └─────────────┬─────────────┘└───────────────────────────┘    
                             ┌─────────────┴─────────────┐                             
                             │         PROJECTION        │                             
                             │   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
                             │        bucket_index       │                             
                             │       summary_index       │                             
                             │        allele_index       │                             
                             │        effect_gene        │                             
                             │    summary_variant_data   │                             
                             └─────────────┬─────────────┘                                                           
                             ┌─────────────┴─────────────┐                             
                             │         SEQ_SCAN          │                             
                             │   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
                             │AGRE_WG38_CSHL_859_SCHEMA2_│                             
                             │          summary          │                             
                             │   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
                             │        allele_index       │                             
                             │        bucket_index       │                             
                             │       summary_index       │                             
                             │        effect_gene        │                             
                             │    summary_variant_data   │                             
                             │   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
                             │Filters: allele_index>0 AND│                             
                             │  allele_index IS NOT NULL │                             
                             │   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                             
                             │        EC: 29419412       │                             
                             └───────────────────────────┘           
```

```sql
EXPLAIN WITH summary AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_summary AS sa
  WHERE
    sa.allele_index > 0
),family AS (
  SELECT
    *
  FROM AGRE_WG38_CSHL_859_SCHEMA2_family AS fa
  WHERE
    (
      8 & fa.inheritance_in_members
    ) = 0
    AND (
      32 & fa.inheritance_in_members
    ) = 0
    AND (
      150 & fa.inheritance_in_members
    ) <> 0
    AND fa.allele_index > 0
)
SELECT
  fa.bucket_index,
  fa.summary_index,
  fa.family_index,
  sa.allele_index,
  sa.summary_variant_data,
  fa.family_variant_data
FROM summary AS sa
JOIN family AS fa
  ON (
    fa.summary_index = sa.summary_index
    AND fa.bucket_index = sa.bucket_index
    AND fa.allele_index = sa.allele_index
  )
```
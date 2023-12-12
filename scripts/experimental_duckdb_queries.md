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
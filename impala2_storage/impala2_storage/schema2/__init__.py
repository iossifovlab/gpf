"""Implementation for the next version (v2) of the DB schema.

Variants schema separated into two separate tables: summary allele and
family variant.

- supported on BigQuery and Impala (specified via Dialect)
- parquet generation outputs two separate parquet files

"""

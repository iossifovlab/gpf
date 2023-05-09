.. code:: yaml

    genotype_storage:
        default: inmemory

        storages:
        - id: duckdb_inplace
          storage_type: duckdb

        - id: duckdb_parquet
          storage_type: duckdb
          studies_path: "%(wd)s/duckdb_parquet"

        # This is how the internal one is configured
        # - id: internal
        #   storage_type: inmemory
        #   dir: "%(wd)s/internal_storage"
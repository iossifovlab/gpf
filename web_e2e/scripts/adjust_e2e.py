#!/usr/bin/env python
from adjustments import main


ADJUSTMENTS = {
    "instance_id": "data_hg19_startup_genotype_impala",
    "impala_hosts": ["impala"],
    "hdfs_host": "impala",
    "available_studies": None,
}


if __name__ == "__main__":
    main(ADJUSTMENTS)

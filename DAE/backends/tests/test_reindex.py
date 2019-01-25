from __future__ import print_function, unicode_literals, absolute_import

from pyspark.sql import Row
from ..thrift.reindex import collect_summary_index_max, \
    summary_index_shift, \
    shift_variants


def test_spark_context(spark, spark_context):
    assert spark is not None
    rdd = spark_context.parallelize(
        [
            Row(chrom="1", summary_variant_index=0),
            Row(chrom="1", summary_variant_index=1),
            Row(chrom="2", summary_variant_index=0),
            Row(chrom="2", summary_variant_index=1),
        ]
    )
    df = spark.createDataFrame(rdd)
    print(df.columns)

    summary_index_max = collect_summary_index_max(df)
    print(summary_index_max)

    shift = summary_index_shift(summary_index_max)
    print(shift)

    assert shift["1"] == 0
    assert shift["2"] == 2

    rdf = shift_variants(shift, df)
    print(rdf)

    pdf = rdf.toPandas()
    print(pdf)

    assert pdf.summary_variant_index[0] == 0
    assert pdf.summary_variant_index[3] == 3

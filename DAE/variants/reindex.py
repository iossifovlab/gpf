from __future__ import print_function
from __future__ import unicode_literals
from builtins import zip
import pandas as pd


CHROMOSOMES = [
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
    '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
    '21', '22', 'X']


def collect_summary_index_max(summary_df):
    chroms = summary_df.groupby("chrom")
    summary_index_max = chroms\
        .max("summary_variant_index")\
        .toPandas()
    return summary_index_max


def summary_index_shift(summary_index_max):
    summary_index_max = summary_index_max.copy()
    summary_index_max["chrom_index"] = summary_index_max.index
    summary_index_max.set_index("chrom", inplace=True)
    summary_chroms = set(summary_index_max.index.values)
    print(summary_chroms)

    for index, chrom in enumerate(CHROMOSOMES):
        if chrom not in summary_chroms:
            continue
        summary_index_max.loc[chrom, "chrom_index"] = index

    summary_index_max.sort_values(by="chrom_index", inplace=True)
    summary_index_max.rename(columns={
        "max(summary_variant_index)": "max_index"
    }, inplace=True)
    shift_index = pd.Series(
        index=summary_index_max.index,
        data=summary_index_max.max_index.values)
    shift_index = shift_index + 1
    shift_index = shift_index.cumsum()

    shift = pd.Series(index=shift_index.index, data=0)
    for p, n in zip(CHROMOSOMES[0:-1], CHROMOSOMES[1:]):
        if p not in summary_chroms or n not in summary_chroms:
            continue
        shift.loc[n] = shift_index[p]

    return shift


def shift_variants(summary_shift, variants_df):
    shifted_df = []
    for chrom in CHROMOSOMES:
        if chrom not in set(summary_shift.index):
            continue
        chrom_shift = int(summary_shift[chrom])

        cdf = variants_df.\
            filter(variants_df.chrom == chrom).\
            withColumn(
                "summary_variant_index",
                variants_df.summary_variant_index + chrom_shift
            )
        shifted_df.append(cdf)
    rdf = shifted_df[0]
    for sdf in shifted_df[1:]:
        rdf = rdf.union(sdf)

    return rdf


def save_variants(variants_df, outname):
    variants_df.write.\
        partitionBy("chrom").\
        format("parquet").\
        mode("overwrite").\
        save(outname)

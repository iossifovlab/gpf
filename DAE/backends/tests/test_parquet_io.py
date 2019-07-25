import os
import pytest
import numpy as np
from backends.impala.parquet_io import ParquetSerializer, \
    VariantsParquetWriter


@pytest.mark.parametrize("gt", [
    np.array([[1, 1, 1], [0, 0, 0]], dtype=np.int8),
    np.array([[2, 1, 1], [1, 0, 0]], dtype=np.int8),
    np.array([[1, 1, 1, 1], [2, 2, 2, 2]], dtype=np.int8),
    np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.int8),
])
def test_genotype_serialize_deserialize(gt):
    data = ParquetSerializer.serialize_variant_genotype(gt)
    print("|{}|,|{}|".format(data, bytes(data, 'utf8')))
    gt2 = ParquetSerializer.deserialize_variant_genotype(data)
    print(data)
    print(gt)
    print(gt2)

    assert np.all(gt == gt2)


@pytest.mark.parametrize("alts", [
    ['A', 'C'],
    ['AA', 'CC'],
    ['AA'],
])
def test_alternatives_serialize_deserialize(alts):
    data = ParquetSerializer.serialize_variant_alternatives(alts)
    alts2 = ParquetSerializer.deserialize_variant_alternatives(data)

    assert alts == alts2[1:]


def test_variant_effects_serialize_deserialize(variants_vcf):
    fvars = variants_vcf("backends/effects_trio")
    vs = list(fvars.query_variants())

    for v in vs:
        data = ParquetSerializer.serialize_variant_effects(v.effects)
        effects2 = ParquetSerializer.deserialize_variant_effects(data)

        assert all([e1 == e2 for e1, e2 in zip(effects2[1:], v.effects)])


def test_variants_parquet_io(
        variants_vcf, temp_filename, test_hdfs,
        test_impala_helpers):
    fvars = variants_vcf("backends/effects_trio_dad")

    variants_writer = VariantsParquetWriter(
        fvars.families,
        fvars.full_variants_iterator())
    variants_writer.save_variants_to_parquet(
        temp_filename
    )

    assert os.path.exists(temp_filename)
    temp_dirname = test_hdfs.tempdir(prefix='variants_', suffix='_data')
    test_hdfs.mkdir(temp_dirname)
    test_hdfs.put(
        temp_filename, os.path.join(temp_dirname, "variant.parquet"))

    db = 'ala_bala_db'
    with test_impala_helpers.connection.cursor() as cursor:
        cursor.execute("""
            DROP DATABASE IF EXISTS {db} CASCADE
        """.format(db=db))

        cursor.execute("""
            CREATE DATABASE IF NOT EXISTS {db}
        """.format(db=db))

        test_impala_helpers.import_variant_files(
            cursor, db, "variant",
            [os.path.join(temp_dirname, "variant.parquet")]
        )

    with test_impala_helpers.connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                chrom,
                `position`,
                reference,
                alternatives_data,
                effect_data,
                family_id,
                genotype_data,
                frequency_data,
                genomic_scores_data,
                GROUP_CONCAT(DISTINCT CAST(allele_index AS string))
            FROM {db}.{variant}
            {where_clause}
            GROUP BY
                bucket_index,
                summary_variant_index,
                family_variant_index,
                chrom,
                `position`,
                reference,
                alternatives_data,
                effect_data,
                family_id,
                genotype_data,
                frequency_data,
                genomic_scores_data
            {limit_clause}
            """.format(
                db=db, variant="variant",
                where_clause="",
                limit_clause=""))

        parquet_serializer = variants_writer.parquet_serializer

        for row in cursor:
            print(row)

            chrom, position, reference, alternatives_data, \
                effect_data, family_id, genotype_data, \
                frequency_data, genomic_scores_data, \
                matched_alleles = row

            family = fvars.families[family_id]
            print(family)

            print(genotype_data)
            gt = parquet_serializer.deserialize_variant_genotype(
                genotype_data)
            print(gt)

            frequencies = parquet_serializer.deserialize_variant_frequency(
                frequency_data)
            print(frequencies)

            genomic_scores = \
                parquet_serializer.deserialize_variant_genomic_scores(
                    genomic_scores_data)
            print(genomic_scores)

            v = parquet_serializer.deserialize_variant(
                family, chrom, position, reference, alternatives_data,
                effect_data, genotype_data,
                frequency_data, genomic_scores_data
            )
            print(v)

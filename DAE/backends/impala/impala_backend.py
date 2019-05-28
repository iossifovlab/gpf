import os
from impala import dbapi
from impala.util import as_pandas

from RegionOperations import Region

from ..attributes_query import \
    QueryTreeToSQLTransformer, \
    role_query, sex_query, \
    inheritance_query,\
    variant_type_query

from variants.attributes import Role, Status, Sex
from backends.impala.parquet_io import HdfsHelpers


class ImpalaBackend(object):
    QUOTE = "'"
    WHERE = """
        WHERE
            {where}
    """

    def __init__(
            self, impala_host=None, impala_port=None,
            hdfs_host=None, hdfs_port=None):

        self.impala = self.get_impala(impala_host, impala_port)
        self.hdfs = self.get_hdfs(hdfs_host, hdfs_port)

    def import_variants(self, config):
        with self.impala.cursor() as cursor:
            cursor.execute("""
                DROP DATABASE IF EXISTS {db} CASCADE
            """.format(db=config.db))
            cursor.execute("""
                CREATE DATABASE IF NOT EXISTS {db}
            """.format(db=config.db))
            cursor.execute("""
                CREATE TABLE {db}.variant LIKE PARQUET '{variants}'
                STORED AS PARQUET
            """.format(db=config.db, variants=config.files.variants))
            cursor.execute("""
                LOAD DATA INPATH '{variants}' INTO TABLE {db}.variant
            """.format(db=config.db, variants=config.files.variants))

            cursor.execute("""
                CREATE TABLE {db}.pedigree LIKE PARQUET '{pedigree}'
                STORED AS PARQUET
            """.format(db=config.db, pedigree=config.files.pedigree))
            cursor.execute("""
                LOAD DATA INPATH '{pedigree}' INTO TABLE {db}.pedigree
            """.format(db=config.db, pedigree=config.files.pedigree))

    def drop_variants_database(self, dbname):
        with self.impala.cursor() as cursor:
            cursor.execute("""
                DROP DATABASE IF EXISTS {db} CASCADE
            """.format(db=dbname))

    @staticmethod
    def get_impala(impala_host=None, impala_port=None):
        if impala_host is None:
            impala_host = os.getenv("IMPALA_HOST", "127.0.0.1")
        if impala_port is None:
            impala_port = int(os.getenv("IMPALA_PORT", 21050))
        print("impala connecting to:", impala_host, impala_port)

        impala_connection = dbapi.connect(
            host=impala_host,
            port=impala_port)
        print("DONE impala connect...")

        return impala_connection

    @staticmethod
    def get_hdfs(hdfs_host=None, hdfs_port=None):

        if hdfs_host is None:
            hdfs_host = os.getenv("HDFS_HOST", "127.0.0.1")
        if hdfs_port is None:
            hdfs_port = int(os.getenv("HDFS_PORT", 8020))

        print("hdfs connecting to:", hdfs_host, hdfs_port)

        return HdfsHelpers(hdfs_host, hdfs_port)

    def load_pedigree(self, config):
        with self.impala.cursor() as cursor:
            q = """
                SELECT * FROM {db}.pedigree
            """.format(db=config.db)

            cursor.execute(q)
            ped_df = as_pandas(cursor)

        ped_df = ped_df.rename(columns={
            'personId': 'person_id',
            'familyId': 'family_id',
            'momId': 'mom_id',
            'dadId': 'dad_id',
            'sampleId': 'sample_id',
            'sex': 'sex',
            'status': 'status',
            'role': 'role',
            'generated': 'generated',
            'layout': 'layout',
            'phenotype': 'phenotype',
        })
        ped_df.role = ped_df.role.apply(lambda v: Role(v))
        ped_df.sex = ped_df.sex.apply(lambda v: Sex(v))
        ped_df.status = ped_df.status.apply(lambda v: Status(v))
        if 'layout' in ped_df:
            ped_df.layout = ped_df.layout.apply(lambda v: v.split(':')[-1])

        return ped_df

    def variants_schema(self, config):
        with self.impala.cursor() as cursor:
            q = """
                DESCRIBE {db}.{variant}
            """.format(db=config.db, variant=config.tables.variant)
            cursor.execute(q)
            df = as_pandas(cursor)
            records = df[['name', 'type']].to_records()
            schema = {
                col_name: col_type for (_, col_name, col_type) in records
            }
            return schema

    def query_variants(self, config, **kwargs):
        with self.impala.cursor() as cursor:
            query = self.build_query(config, **kwargs)
            print("FINAL QUERY: ", query)
            cursor.execute(query)
            for row in cursor:
                yield row

    def _build_regions_where(self, query_values):
        assert isinstance(query_values, list)
        where = []
        for region in query_values:
            assert isinstance(region, Region)
            where.append(
               "(`chrom` = {q}{chrom}{q} AND `position` >= {start} AND "
               "`position` <= {stop})"
               .format(
                    q=self.QUOTE,
                    chrom=region.chrom,
                    start=region.start,
                    stop=region.stop)
            )
        return ' OR '.join(where)

    def _build_iterable_string_attr_where(self, column_name, query_values):
        assert query_values is not None

        assert isinstance(query_values, list) or \
            isinstance(query_values, set)

        if not query_values:
            where = ' {column_name} IS NULL'.format(
                column_name=column_name
            )
            return where
        else:
            values = [
                ' {q}{val}{q} '.format(
                    q=self.QUOTE,
                    val=val.replace("'", "\\'"))
                for val in query_values]

            where = ' {column_name} in ( {values} ) '.format(
                column_name=column_name,
                values=','.join(values))
            return where

    def _build_complex_attr_where(
            self, column_name, query_value, query_transformer):
        assert query_value is not None
        parsed = query_value
        if isinstance(query_value, str):
            parsed = query_transformer.transform_query_string_to_tree(
                    query_value)
        transformer = QueryTreeToSQLTransformer(column_name)
        return transformer.transform(parsed)

    def _build_where(self, query):
        where = []
        if query.get('regions'):
            where.append(self._build_regions_where(query['regions']))
        if query.get('family_ids') is not None:
            where.append(self._build_iterable_string_attr_where(
                'family_id', query['family_ids']
            ))
        if query.get('person_ids') is not None:
            where.append(self._build_iterable_string_attr_where(
                'variant_in_member', query['person_ids']
            ))
        if query.get('effect_types') is not None:
            where.append(self._build_iterable_string_attr_where(
                'effect_type', query['effect_types']
            ))
        if query.get('genes') is not None:
            where.append(self._build_iterable_string_attr_where(
                'effect_gene', query['genes']
            ))
        if query.get("inheritance"):
            where.append(self._build_complex_attr_where(
                'inheritance_in_member', query['inheritance'],
                inheritance_query
            ))
        if query.get("roles"):
            where.append(self._build_complex_attr_where(
                'variant_in_role', query['roles'],
                role_query
            ))
        if query.get("sexes"):
            where.append(self._build_complex_attr_where(
                'variant_in_sex', query['sexes'],
                sex_query
            ))
        return where

    def build_query(self, config, **kwargs):
        where = self._build_where(kwargs)
        where_clause = ""
        if where:
            where_clause = self.WHERE.format(
                where=" AND ".join([
                    "( {} )".format(w) for w in where])
            )
        return """
            SELECT
                `data`, GROUP_CONCAT(DISTINCT CAST(allele_index AS string))
            FROM {db}.{variant}
            {where_clause}
            GROUP BY
                bucket_index,
                summary_variant_index,
                family_variant_index,
                `data`
            """.format(
            db=config.db, variant=config.tables.variant,
            where_clause=where_clause)

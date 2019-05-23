import os
from impala import dbapi
from impala.util import as_pandas

from variants.attributes import Role, Status, Sex
from backends.impala.parquet_io import HdfsHelpers


class ImpalaBackend(object):

    def __init__(
            self, impala_host=None, impala_port=None,
            hdfs_host=None, hdfs_port=None):

        self.impala = self.get_impala(impala_host, impala_port)
        self.hdfs = self.get_hdfs(hdfs_host, hdfs_port)

    def import_dataset(self, config):
        with self.impala.cursor() as cursor:
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

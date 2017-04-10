'''
Created on Apr 7, 2017

@author: lubo
'''
from pheno.models import ManagerBase


class MetaVariableCorrelationModel(object):
    SCHEMA_CREATE = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS {table} (
        variable_id varchar(128) NOT NULL,
        correlation_with varchar(128) NOT NULL,
        role varchar(16) NOT NULL,
        gender varchar(1) NOT NULL,
        coeff real NULL,
        pvalue real NULL,
        PRIMARY KEY (variable_id, correlation_with, role, gender)
    );
    COMMIT;
    """

    SCHEMA_DROP = """
    BEGIN;

    DROP TABLE IF EXISTS {table};

    COMMIT;
    """

    TABLE = 'meta_variable_correlation'

    COLUMNS = [
        'variable_id',
        'correlation_with',
        'role',
        'gender',
        'coeff',
        'pvalue',
    ]

    def __init__(self):
        self.variable_id = None
        self.correlation_with = None
        self.role = None
        self.gender = None
        self.coeff = None
        self.pvalue = None

    @staticmethod
    def to_tuple(v):
        return (
            v.variable_id,
            v.correlation_with,
            v.role,
            v.gender,
            v.coeff,
            v.pvalue,
        )

    @staticmethod
    def create_from_df(row):
        v = MetaVariableCorrelationModel()

        v.variable_id = row['variable_id']
        v.correlation_with = row['correlation_with']
        v.role = row['role']
        v.gender = row['gender']
        v.coeff = row['coeff']
        v.pvalue = row['pvalue']
        return v


class MetaVariableCorrelationManager(ManagerBase):

    MODEL = MetaVariableCorrelationModel

    def __init__(self, *args, **kwargs):
        super(MetaVariableCorrelationManager, self).__init__(*args, **kwargs)

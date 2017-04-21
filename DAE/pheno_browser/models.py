'''
Created on Apr 7, 2017

@author: lubo
'''
from pheno.models import ManagerBase


class VariableBrowserModel(object):
    SCHEMA_CREATE = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS {table} (
        measure_id varchar(128) NOT NULL,
        instrument_name varcahr(64) NOT NULL,
        measure_name varchar(64) NOT NULL,
        measure_type varchar(16),

        figure_distribution_small varchar(256),
        figure_distribution varchar(256),
        values_domain varchar(128),

        figure_correlation_nviq_small varchar(256),
        figure_correlation_nviq varchar(256),
        pvalue_correlation_nviq_male real,
        pvalue_correlation_nviq_female real,

        figure_correlation_age_small varchar(256),
        figure_correlation_age varchar(256),
        pvalue_correlation_age_male real,
        pvalue_correlation_age_female real,

        PRIMARY KEY (measure_id)
    );

    CREATE INDEX IF NOT EXISTS {table}_instrument_name
        ON {table} (instrument_name);

    COMMIT;
    """

    SCHEMA_DROP = """
    BEGIN;

    DROP TABLE IF EXISTS {table};

    COMMIT;
    """

    TABLE = 'variable_browser'

    COLUMNS = [
        'measure_id',
        'instrument_name',
        'measure_name',
        'measure_type',

        'figure_distribution_small',
        'figure_distribution',
        'values_domain',

        'figure_correlation_nviq_small',
        'figure_correlation_nviq',
        'pvalue_correlation_nviq_male',
        'pvalue_correlation_nviq_female',

        'figure_correlation_age_small',
        'figure_correlation_age',
        'pvalue_correlation_age_male',
        'pvalue_correlation_age_female',

    ]

    def __init__(self):
        self.measure_id = None
        self.instrument_name = None
        self.measure_name = None
        self.measure_type = None

        self.figure_distribution_small = None
        self.figure_distribution = None
        self.values_domain = None

        self.figure_correlation_nviq_small = None
        self.figure_correlation_nviq = None
        self.pvalue_correlation_nviq_male = None
        self.pvalue_correlation_nviq_female = None

        self.figure_correlation_age_small = None
        self.figure_correlation_age = None
        self.pvalue_correlation_age_male = None
        self.pvalue_correlation_age_female = None

    @staticmethod
    def to_tuple(v):
        return (
            v.measure_id,
            v.instrument_name,
            v.measure_name,
            v.measure_type,

            v.figure_distribution_small,
            v.figure_distribution,
            v.values_domain,

            v.figure_correlation_nviq_small,
            v.figure_correlation_nviq,
            v.pvalue_correlation_nviq_male,
            v.pvalue_correlation_nviq_female,

            v.figure_correlation_age_small,
            v.figure_correlation_age,
            v.pvalue_correlation_age_male,
            v.pvalue_correlation_age_female,
        )

    @staticmethod
    def create_from_df(row):
        v = VariableBrowserModel()

        v.measure_id = row['measure_id']
        v.instrument_name = row['instrument_name']
        v.measure_name = row['measure_name']
        v.measure_type = row['measure_type']

        v.figure_distribution_small = row['figure_distribution_small']
        v.figure_distribution = row['figure_distribution']
        v.values_domain = row['values_domain']

        v.figure_correlation_nviq_small = row['figure_correlation_nviq_small']
        v.figure_correlation_nviq = row['figure_correlation_nviq']
        v.pvalue_correlation_nviq_male = row['pvalue_correlation_nviq_male']
        v.pvalue_correlation_nviq_female = \
            row['pvalue_correlation_nviq_female']

        v.figure_correlation_age_small = row['figure_correlation_age_small']
        v.figure_correlation_age = row['figure_correlation_age']
        v.pvalue_correlation_age_male = row['pvalue_correlation_age_male']
        v.pvalue_correlation_age_female = row['pvalue_correlation_age_female']

        return v


class VariableBrowserModelManager(ManagerBase):

    MODEL = VariableBrowserModel

    def __init__(self, *args, **kwargs):
        super(VariableBrowserModelManager, self).__init__(*args, **kwargs)

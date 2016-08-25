'''
Created on Aug 25, 2016

@author: lubo
'''
from pheno.utils.load_raw import V15Loader, V14Loader
from pheno.models import VariableModel, VariableManager


class PrepareVariables(V15Loader):

    def __init__(self):
        super(PrepareVariables, self).__init__()

    @staticmethod
    def _variable_id(row):
        return "{}.{}".format(row['tableName'], row['name'])

    @staticmethod
    def _variable_description_from_main(row):
        return None

    @staticmethod
    def _variable_description_from_ssc(row):
        return None

    @staticmethod
    def _set_variable_from_row(var, row, build_description):
        var.variable_id = PrepareVariables._variable_id(row)
        var.table_name = row['tableName']
        var.variable_name = row['name']

        var.domain = row['domain']
        var.domain_choice_label = row['domainChoiceLabel']
        var.measurement_scale = row['measurementScale']

        var.description = build_description(row)

        var.has_values = None
        var.domain_rank = None
        var.individuals = None

        return var

    def _build_variable(self, row, build_description):
        var = VariableModel()
        PrepareVariables._set_variable_from_row(var, row, build_description)
        return var

    def _build_variable_dictionary(self, vm, df, build_description):

        for _index, row in df.iterrows():
            var = self._build_variable(row, build_description)
            vm.save(var)

    def prepare(self):
        loader = V14Loader()

        vm = VariableManager()
        vm.create_tables()
        vm.connect()

        df = loader.load_main()
        self._build_variable_dictionary(
            vm, df, PrepareVariables._variable_description_from_main)

        df = loader.load_cdv()
        self._build_variable_dictionary(
            vm, df, PrepareVariables._variable_description_from_ssc)

        df = loader.load_ocuv()
        self._build_variable_dictionary(
            vm, df, PrepareVariables._variable_description_from_ssc)

        vm.close()

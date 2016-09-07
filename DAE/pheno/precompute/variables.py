'''
Created on Aug 25, 2016

@author: lubo
'''
from pheno.models import VariableModel, VariableManager
from pheno.utils.load_raw import V15Loader, V14Loader


class PrepareVariables(V15Loader):

    def __init__(self, *args, **kwargs):
        super(PrepareVariables, self).__init__(*args, **kwargs)

    @staticmethod
    def _variable_id(row):
        return "{}.{}".format(row['tableName'].strip(), row['name'].strip())

    @staticmethod
    def _variable_description_from_main(row):
        display = [
            row['tableDisplayTitle'],
            row['variableDisplayTitle'],
        ]
        display = [d.strip() for d in display if isinstance(d, str)]
        if display:
            display = ': '.join(display)
        else:
            display = None

        descr = [
            display,
            row['variableDisplayHint'],
            row['variableNotes'],
        ]
        descr = [d.strip() for d in descr if isinstance(d, str)]

        if descr:
            return '\n\n'.join(descr)
        else:
            return None

    @staticmethod
    def _variable_description_from_ssc(row):
        descr = []
        variable_notes = row['variableNotes']
        calculation_documentation = row['calculationDocumentation']
        category = row['variableCategory']

        if isinstance(variable_notes, str):
            descr.append(variable_notes.strip())
        if isinstance(category, str):
            descr.append(category.strip())
        if isinstance(calculation_documentation, str):
            descr.append(calculation_documentation.strip())

        if descr:
            return '\n\n'.join(descr)
        else:
            return None

    @staticmethod
    def _set_variable_from_row(var, row, build_description, source):
        var.variable_id = PrepareVariables._variable_id(row)
        var.table_name = row['tableName'].strip()
        var.variable_name = row['name'].strip()

        var.domain = row['domain'].strip()
        var.domain_choice_label = row['domainChoiceLabel'].strip() \
            if isinstance(row['domainChoiceLabel'], str) else None
        var.measurement_scale = row['measurementScale'].strip()
        var.description = build_description(row)

        var.source = source
        var.has_values = None
        var.domain_rank = None
        var.individuals = None

        return var

    def _build_variable(self, row, build_description, source):
        var = VariableModel()
        PrepareVariables._set_variable_from_row(
            var, row, build_description, source)
        return var

    def _build_variable_dictionary(self, vm, df, build_description, source):

        for _index, row in df.iterrows():
            var = self._build_variable(row, build_description, source)
            vm.save(var)

    def prepare(self):
        loader = V14Loader()

        with VariableManager(config=self.config) as vm:
            vm.drop_tables()
            vm.create_tables()
            print("loading main dictionary")
            df = loader.load_main()
            self._build_variable_dictionary(
                vm, df, PrepareVariables._variable_description_from_main,
                'main')

            print("loading cdv dictionary")
            df = loader.load_cdv()
            self._build_variable_dictionary(
                vm, df, PrepareVariables._variable_description_from_ssc,
                'cdv: Core Descriptive Variables')

            print("loading ocuv dictionary")
            df = loader.load_ocuv()
            self._build_variable_dictionary(
                vm, df, PrepareVariables._variable_description_from_ssc,
                'ocuv: Other Commonly Used Variables')

'''
Created on Aug 12, 2016

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from pheno_db.models import VariableDescriptor, ValueFloat
from pheno_db.utils.load_raw import V15Loader
import numpy as np
import sys


class Command(BaseCommand):
    help = '''Loads Main Data Dictionary into the database'''

    BULK_SIZE = 200

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')

        tables = VariableDescriptor.objects.values('table_name').distinct()
        print(tables)

        loader = V15Loader()

        bulk = []

        for table in tables:
            table_name = table['table_name']
            variables = VariableDescriptor.objects.filter(
                table_name=table_name, measurement_scale='float')

            if(len(variables) == 0):
                continue
            print("processing table: {}".format(table_name))
            dfs = loader.load(table_name)
            if len(dfs) == 0:
                continue

            print(len(dfs))
            assert 1 == len(dfs)

            for df in dfs:
                available_variables = [v for v in variables
                                       if v.variable_name in df.columns]
                missing_variables = [v.variable_name for v in variables
                                     if v.variable_name not in df.columns]
                if missing_variables:
                    print("table {} missing variables {}".format(
                        table_name,
                        missing_variables)
                    )
                for _index, row in df.iterrows():
                    for var in available_variables:
                        if var.variable_name not in df.columns:
                            continue
                        if np.isnan(row[var.variable_name]):
                            continue

                        val = ValueFloat()

                        val.descriptor = var
                        val.person_id = row['individual']
                        val.person_role = 'prb'
                        val.family_id = row['individual'].split('.')[0]
                        val.variable_id = var.variable_id
                        val.value = row[var.variable_name]

                        bulk.append(val)
                    if len(bulk) >= self.BULK_SIZE:
                        ValueFloat.objects.bulk_create(bulk)
                        bulk = []
                        sys.stderr.write('.')

        if len(bulk) >= self.BULK_SIZE:
            ValueFloat.objects.bulk_create(bulk)
            bulk = []
            sys.stderr.write('.')

        print(" done")

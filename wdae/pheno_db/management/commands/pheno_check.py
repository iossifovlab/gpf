'''
Created on Aug 15, 2016

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError

from pheno_db.models import VariableDescriptor
from pheno_db.utils.values import ValuesLoader

import collections


class Command(BaseCommand):
    help = '''Check Pheno DB v15 data loaded into the database'''

    def _mark_float_variables_without_data(self):
        variables = VariableDescriptor.objects.filter(
            measurement_scale='float',
        )
        with_data = 0
        without_data = 0
        total = 0

        for vd in variables:
            loader = ValuesLoader(vd)
            df = loader.load_df()
            if len(df) == 0:
                without_data += 1
                vd.has_values = False
                vd.domain_rank = 0
                vd.individuals = 0
            else:
                vd.has_values = True
                with_data += 1
            vd.save()
            total += 1

        print("float variables: {}; with data: {}; without data: {}".format(
            total, with_data, without_data
        ))

    CUTOFF_INDIVIDUALS = 10
    CUTOFF_DOMAIN = 5

    def _check_float_variables_domain(self):
        variables = VariableDescriptor.objects.filter(
            measurement_scale='float',
            has_values=True,
        )

        problem_variables = collections.defaultdict(dict)
        good_variables = 0
        total = 0

        for vd in variables:
            total += 1
            loader = ValuesLoader(vd)

            df = loader.load_df()
            individuals = len(df)
            domain_rank = len(df.value.unique())
            vd.individuals = individuals
            vd.domain_rank = domain_rank
            vd.save()

            if individuals < self.CUTOFF_INDIVIDUALS:
                problem_variables[vd.variable_id]['individuals'] = \
                    len(df)
            if domain_rank < self.CUTOFF_DOMAIN:
                problem_variables[vd.variable_id]['domain'] = \
                    domain_rank
                problem_variables[vd.variable_id]['values'] = \
                    df.value.unique()
                problem_variables[vd.variable_id]['individuals'] = \
                    individuals

            if vd.variable_id not in problem_variables:
                good_variables += 1

        for variable_id, problem in problem_variables.items():
            print("{}:\n\t{}".format(variable_id, problem))

        print("total variables: {}; good values: {}; problem values: {}"
              .format(
                  total, good_variables, len(problem_variables)
              ))

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')

        self._mark_float_variables_without_data()
        self._check_float_variables_domain()

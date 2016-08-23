'''
Created on Aug 15, 2016

@author: lubo
'''

from django.core.management.base import BaseCommand, CommandError

from pheno_db.models import Individual

from pheno.precompute import individuals


class Command(BaseCommand):
    help = '''Loads Family Data into the pheno database'''
    BULK_SIZE = 200

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')

        prep = individuals.PrepareIndividuals()
        df = prep.prepare()
        prep.cache(df)

        individs = individuals.Individuals()
        individs.load()

        self._bulk_create(individs.df)

    def _bulk_create(self, df):
        bulk = []
        for _index, row in df.iterrows():
            individ = Individual()
            individ.person_id = row['personId']
            individ.role = row['role']
            individ.role_order = row['roleOrder']
            individ.role_id = row['roleId']
            individ.gender = row['gender']
            individ.race = 'unknown'
            individ.family_id = row['familyId']
            individ.collection = row['collection']

            individ.v1 = row['v1']
            individ.v2 = row['v2']
            individ.v3 = row['v3']
            individ.v4 = row['v4']
            individ.v5 = row['v5']
            individ.v6 = row['v6']
            individ.v7 = row['v7']
            individ.v8 = row['v8']
            individ.v9 = row['v9']
            individ.v10 = row['v10']
            individ.v11 = row['v11']
            individ.v12 = row['v12']
            individ.v13 = row['v13']
            individ.v14 = row['v14']
            individ.v15 = row['v15']

            bulk.append(individ)
            if len(bulk) >= self.BULK_SIZE:
                Individual.objects.bulk_create(bulk)
                bulk = []

        Individual.objects.bulk_create(bulk)
        bulk = []

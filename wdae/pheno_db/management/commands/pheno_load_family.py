'''
Created on Aug 15, 2016

@author: lubo
'''

from django.core.management.base import BaseCommand, CommandError

from pheno_db.models import Person

from pheno.precompute import individuals
from helpers.default_ssc_study import get_ssc_denovo_studies


class Command(BaseCommand):
    help = '''Loads Family Data into the pheno database'''
    BULK_SIZE = 200

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')

        # prep = individuals.PrepareIndividuals()
        # df = prep.prepare()
        # prep.cache(df)

        individs = individuals.Individuals()
        individs.load()

        self._bulk_create(individs.df)
        self._mark_ssc_dataset()

    def _create_person(self, row):
        p = Person()
        p.person_id = row['personId']
        p.role = row['role']
        p.role_order = row['roleOrder']
        p.role_id = row['roleId']
        p.gender = row['gender']
        p.race = 'unknown'
        p.family_id = row['familyId']
        p.collection = row['collection']
        p.ssc_dataset = True
        p.v1 = row['v1']
        p.v2 = row['v2']
        p.v3 = row['v3']
        p.v4 = row['v4']
        p.v5 = row['v5']
        p.v6 = row['v6']
        p.v7 = row['v7']
        p.v8 = row['v8']
        p.v9 = row['v9']
        p.v10 = row['v10']
        p.v11 = row['v11']
        p.v12 = row['v12']
        p.v13 = row['v13']
        p.v14 = row['v14']
        p.v15 = row['v15']
        return p

    def _bulk_create(self, df):
        bulk = []
        for _index, row in df.iterrows():
            p = self._create_person(row)

            bulk.append(p)
            if len(bulk) >= self.BULK_SIZE:
                Person.objects.bulk_create(bulk)
                bulk = []

        Person.objects.bulk_create(bulk)
        bulk = []

    def _mark_ssc_dataset(self):
        persons = {}
        for p in Person.objects.all():
            persons[p.person_id] = []

        for st in get_ssc_denovo_studies():
            for _fid, fam in st.families.items():
                for p in fam.memberInOrder:
                    if p.personId not in persons:
                        print("person: {} from study: {} not found in PhenoDB"
                              .format(p.personId, st.name))
                        continue
                    persons[p.personId].append(st.name)

        for pid, studies in persons.items():
            if len(studies) == 0:
                p = Person.objects.get(person_id=pid)
                p.ssc_dataset = False
                p.save()

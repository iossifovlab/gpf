'''
Created on Aug 15, 2016

@author: lubo
'''

from django.core.management.base import BaseCommand, CommandError

from pheno_db.models import Individual
from pheno_db.utils.load_raw import V15Loader


class Command(BaseCommand):
    help = '''Loads Family Data into the pheno database'''
    BULK_SIZE = 200

    @staticmethod
    def _individual_role(person_id):
        fid, pid = person_id.split('.')
        if pid == 'fa':
            role = 'father'
        elif pid == 'mo':
            role = 'mother'
        elif pid[0] == 'p':
            role = 'prb'
        elif pid[0] == 's':
            role = 'sib'
            if pid[1] != '1':
                role = 'other sib'
        else:
            raise ValueError("unknown role: {}".format(person_id))
        return fid, role

    def _load_individuals(self):
        loader = V15Loader()
        df = loader.load_individuals()
        individuals = {}
        for _index, row in df.iterrows():
            individual = Individual()
            if not row['Version 15: 2013-08-06']:
                continue
            individual.person_id = row['SSC ID']

            individual.collection = row['Collection']
            if individual.collection != 'Simons Simplex Collection':
                continue

            fid, role = self._individual_role(individual.person_id)
            individual.fid = fid
            individual.role = role

            if role == 'other sib':
                continue

            if role == 'father':
                individual.gender = 'M'
            elif role == 'mother':
                individual.gender = 'F'

            individuals[individual.person_id] = individual

        print("individuals {} loaded".format(len(individuals)))
        return individuals

    @staticmethod
    def _parse_gender(sex):
        if sex == 'male':
            return 'M'
        elif sex == 'female':
            return 'F'
        raise ValueError('unexpected gender: {}'.format(sex))

    def _load_genders(self, individuals):
        loader = V15Loader()
        dfs = loader.load(
            'ssc_core_descriptive',
            roles=['prb', 'sib', ]
        )
        for df in dfs:
            for _index, row in df.iterrows():
                try:
                    person_id = row['individual']
                    gender = self._parse_gender(row['sex'])
                    if person_id in individuals:
                        individuals[person_id].gender = gender
                except ValueError as e:
                    print("problem parsing: {}".format(person_id))
                    raise e

    def _parse_individual_race(self, dfs, individuals, race_column):
        for df in dfs:
            for _index, row in df.iterrows():
                try:
                    person_id = row['individual']
                    race = row[race_column]
                    if person_id in individuals:
                        individuals[person_id].race = race
                except ValueError as e:
                    print "problem parsing: {}".format(person_id)
                    raise e

    def _load_races(self, individuals):
        loader = V15Loader()
        dfs = loader.load(
            'ssc_core_descriptive',
            roles=['prb', 'sib', ]
        )
        self._parse_individual_race(dfs, individuals, 'race')

        dfs = loader.load(
            'ssc_commonly_used',
            roles=['father', 'mother', ]
        )
        self._parse_individual_race(dfs, individuals, 'race_parents')

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')

        individuals = self._load_individuals()
        self._load_genders(individuals)
        self._load_races(individuals)

        Individual.objects.bulk_create(
            individuals.values()
        )

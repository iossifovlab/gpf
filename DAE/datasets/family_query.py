from collections import defaultdict
import itertools

from DAE import vDB


class FamilyQuery(object):

    def __init__(self, study_names, pheno_db, pheno_measures=[]):
        self._studies = None
        self._families = None
        self._persons = None
        self.study_names = study_names
        self.pheno_db = pheno_db
        self.pheno_measures = pheno_measures
        self.load_families()

    @property
    def families(self):
        if self._families is None:
            self.load_families()
        return self._families

    @property
    def studies(self):
        if self._studies is None:
            studies = [vDB.get_studies(st) for st in self.study_names]
            self._studies = [
                st for st in itertools.chain.from_iterable(studies)
            ]
            for st in self._studies:
                st._load_family_data()
        return self._studies

    @property
    def persons(self):
        if self._persons is None:
            self.load_families()
        return self._persons

    def load_families(self):
        self._load_geno_families()
        self._load_pheno_families()
        self._load_pheno_columns()

    def _load_geno_families(self):
        families = {}
        for st in self.studies:
            families.update(st.families)
        self._families = families
        self._persons = {}
        for fam in self._families.values():
            for p in fam.memberInOrder:
                p.familyId = fam.familyId
                self._persons[p.personId] = p

    def _load_pheno_families(self):
        self.geno2pheno_families = defaultdict(set)
        self.pheno2geno_families = defaultdict(set)

        self.pheno_families = defaultdict(dict)
        self.pheno_persons = {}
        if not self.pheno_db:
            return

        person_df = self.pheno_db.get_persons_df()
        persons = person_df.to_dict(orient='records')
        for p in persons:
            pid = p['person_id']
            self.pheno_persons[pid] = p
            self.pheno_families[p['family_id']][pid] = p
            if pid in self._persons:
                geno_person = self._persons[pid]
                geno_fid = geno_person.familyId
                self.geno2pheno_families[geno_fid].add(p['family_id'])
                self.pheno2geno_families[p['family_id']].add(geno_fid)

    def _load_pheno_columns(self):
        for measure in self.pheno_measures:
            assert self.pheno_db.has_measure(measure), \
                'missing measure {}'.format(measure)
            values = self.pheno_db.get_persons_values_df([measure])
            values.dropna(inplace=True)

            for index, row in values.iterrows():
                person = self._persons.get(row['person_id'], None)
                if person is not None:
                    person.atts[measure] = row[measure]

            #for pheno_fid in values['family_id'].unique():
            #    fvalues = values[values.family_id == pheno_fid]
            #    if len(fvalues) == 0:
            #        continue
            #    geno_fids = self.pheno2geno_families[pheno_fid]
            #    for fid in geno_fids:
            #        geno_fam = self._families.get(fid)
            #        if not geno_fam:
            #            continue
            #        geno_fam.atts[attr] = fvalues[source].values[0]
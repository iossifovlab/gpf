class Study(object):

    def __init__(self, name, backend, study_config):
        self.name = name
        self.backend = backend
        self.study_config = study_config
        self._study_type_lowercase = self.study_type.lower()

    def query_variants(self, **kwargs):
        study_types_filter = kwargs.get('studyTypes', None)
        if study_types_filter:
            if not isinstance(study_types_filter, list):
                raise RuntimeError("alabalaa")
            study_types_filter = [s.lower() for s in study_types_filter]
            if self._study_type_lowercase not in study_types_filter:
                return []

        kwargs = self.add_people_with_phenotype(kwargs)

        return self.backend.query_variants(**kwargs)

    def add_people_with_phenotype(self, kwargs):
        people_with_phenotype = set()
        if 'pedigreeSelector' in kwargs and\
                kwargs['pedigreeSelector'] is not None:
            pedigree_selector = kwargs.pop('pedigreeSelector')

            for family in self.families.values():
                family_members_with_phenotype = set(
                    [person.person_id for person in
                        family.get_people_with_phenotypes(
                            pedigree_selector['source'],
                            pedigree_selector['checkedValues'])])
                people_with_phenotype.update(family_members_with_phenotype)

            kwargs['person_ids'] = list(people_with_phenotype)

        return kwargs

    def get_phenotype_values(self, pheno_column='phenotype'):
        return set(self.backend.ped_df[pheno_column])

    @property
    def families(self):
        return self.backend.families

    @property
    def description(self):
        return self.study_config.description

    @property
    def phenotypes(self):
        return self.study_config.phenotypes

    @property
    def has_denovo(self):
        return self.study_config.hasDenovo

    @property
    def has_transmitted(self):
        return self.study_config.hasTransmitted

    @property
    def has_complex(self):
        return self.study_config.hasComplex

    @property
    def has_CNV(self):
        return self.study_config.hasCNV

    @property
    def study_type(self):
        return self.study_config.studyType

    @property
    def study_types(self):
        return [self.study_config.studyType]

    # FIXME: fill these with real data

    @property
    def year(self):
        return None

    @property
    def years(self):
        return None

    @property
    def pub_med(self):
        return None

    @property
    def pub_meds(self):
        return None

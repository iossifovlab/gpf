import logging

import pandas as pd
from sqlalchemy.sql import select, text
from sqlalchemy import not_

from collections import defaultdict, OrderedDict

from dae.pedigrees.family import Person, Family
from dae.pheno.db import DbManager
from dae.pheno.common import MeasureType
from dae.pheno.utils.config import PhenoConfigParser

from dae.variants.attributes import Sex, Status, Role


LOGGER = logging.getLogger(__name__)


class Instrument(object):
    """
    Instrument object represents phenotype instruments.

    Common fields are:

    * `instrument_name`

    * `measures` -- dictionary of all measures in the instrument
    """

    def __init__(self, name):
        self.instrument_name = name
        self.measures = OrderedDict()

    def __repr__(self):
        return "Instrument({}, {})".format(
            self.instrument_name, len(self.measures))


class Measure(object):
    """
    Measure objects represent phenotype measures.

    Common fields are:

    * `instrument_name`

    * `measure_name`

    * `measure_id` - formed by `instrument_name`.`measure_name`

    * `measure_type` - one of 'continuous', 'ordinal', 'categorical'

    * `description`

    * `min_value` - for 'continuous' and 'ordinal' measures

    * `max_value` - for 'continuous' and 'ordinal' measures

    * `value_domain` - string that represents the values

    """

    def __init__(self, name):
        self.name = name
        self.measure_name = name
        self.measure_type = MeasureType.other
        self.values_domain = None

    def __repr__(self):
        return "Measure({}, {}, {})".format(
            self.measure_id, self.measure_type, self.values_domain)

    @classmethod
    def _from_dict(cls, row):
        """
        Creates `Measure` object from pandas data frame row.
        """
        assert row['measure_type'] is not None

        m = Measure(row['measure_name'])
        m.measure_id = row['measure_id']
        m.instrument_name = row['instrument_name']
        m.measure_name = row['measure_name']
        m.measure_type = row['measure_type']

        m.description = row['description']
        m.default_filter = row['default_filter']
        m.values_domain = row.get('values_domain')
        m.min_value = row.get('min_value')
        m.max_value = row.get('max_value')

        return m


class PhenotypeData():

    def get_persons_df(self, roles, person_ids, family_ids):
        raise NotImplementedError()

    def get_persons_values_df(self, measure_ids, person_ids,
                              family_ids, roles):
        raise NotImplementedError()

    def get_persons(self, roles, person_ids, family_ids):
        raise NotImplementedError()

    def has_measure(self, measure_id):
        raise NotImplementedError()

    def get_measure(self, measure_id):
        raise NotImplementedError()

    def get_measures(self, instrument, measure_type):
        raise NotImplementedError()

    def get_measure_values_df(self, measure_id, person_ids, family_ids, roles):
        raise NotImplementedError()

    def get_measure_values(self, measure_id, person_ids, family_ids, roles):
        raise NotImplementedError()

    def get_values_df(self, measure_ids, person_ids, family_ids, roles):
        raise NotImplementedError()

    def get_values(self, measure_ids, person_ids, family_ids, roles):
        raise NotImplementedError()

    def get_instrument_values_df(self, instrument_df, person_ids,
                                 family_ids, roles):
        raise NotImplementedError()

    def get_instrument_values(self, instrument_df, person_ids,
                              family_ids, roles):
        raise NotImplementedError()


class PhenotypeDataStudy(PhenotypeData):
    """
    Main class for accessing phenotype database in DAE.

    To access the phenotype database create an instance of this class
    and call the method *load()*.

    Common fields of this class are:

    * `families` -- list of all families in the database

    * `persons` -- list of all individuals in the database

    * `instruments` -- dictionary of all instruments

    * `measures` -- dictionary of all measures
    """

    def __init__(self, dbfile):

        self.families = None
        self.persons = None
        self.instruments = None
        self.measures = {}
        self.db = DbManager(dbfile=dbfile)
        self.db.build()
        self._load()

    def _get_measures_df(self, instrument=None, measure_type=None):
        """
        Returns data frame containing measures information.

        `instrument` -- an instrument name which measures should be
        returned. If not specified all type of measures are returned.

        `measure_type` -- a type ('continuous', 'ordinal' or 'categorical')
        of measures that should be returned. If not specified all
        type of measures are returned.

        Each row in the returned data frame represents given measure.

        Columns in the returned data frame are: `measure_id`, `measure_name`,
        `instrument_name`, `description`, `stats`, `min_value`, `max_value`,
        `value_domain`, `has_probands`, `has_siblings`, `has_parents`,
        `default_filter`.
        """
        assert instrument is None or instrument in self.instruments
        assert measure_type is None or \
            measure_type in set([
                'continuous', 'ordinal', 'categorical', 'unknown'])

        measure = self.db.measure
        columns = [
            measure.c.measure_id,
            measure.c.instrument_name,
            measure.c.measure_name,
            measure.c.description,
            measure.c.measure_type,
            measure.c.individuals,
            measure.c.default_filter,
            measure.c.values_domain,
            measure.c.min_value,
            measure.c.max_value,
        ]
        s = select(columns)
        s = s.where(not_(measure.c.measure_type.is_(None)))
        if instrument is not None:
            s = s.where(measure.c.instrument_name == instrument)
        if measure_type is not None:
            s = s.where(measure.c.measure_type == measure_type)

        df = pd.read_sql(s, self.db.engine)

        df_columns = [
            'measure_id', 'measure_name', 'instrument_name',
            'description', 'individuals', 'measure_type',
            'default_filter',
            'values_domain',
            'min_value',
            'max_value',
        ]
        res_df = df[df_columns]
        return res_df

    def get_measures(
            self, instrument=None, measure_type=None):
        """
        Returns a dictionary of measures objects.

        `instrument` -- an instrument name which measures should be
        returned. If not specified all type of measures are returned.

        `measure_type` -- a type ('continuous', 'ordinal' or 'categorical')
        of measures that should be returned. If not specified all
        type of measures are returned.

        """
        df = self._get_measures_df(
            instrument, measure_type)

        res = OrderedDict()
        for row in df.to_dict('records'):
            m = Measure._from_dict(row)
            res[m.measure_id] = m
        return res

    def _load_instruments(self):
        instruments = OrderedDict()

        df = self._get_measures_df()
        instrument_names = list(df.instrument_name.unique())
        instrument_names = sorted(instrument_names)

        for instrument_name in instrument_names:
            instrument = Instrument(instrument_name)
            measures = OrderedDict()
            measures_df = df[df.instrument_name == instrument_name]

            for row in measures_df.to_dict('records'):
                m = Measure._from_dict(row)
                measures[m.measure_name] = m
                self.measures[m.measure_id] = m
            instrument.measures = measures
            instruments[instrument.instrument_name] = instrument

        self.instruments = instruments

    def _load_families(self):
        families = defaultdict(list)
        persons = self.get_persons()

        for p in list(persons.values()):
            families[p.family_id].append(p)

        self.persons = persons
        self.families = {}

        for family_id, members in list(families.items()):
            f = Family(family_id)
            f.memberInOrder = members
            f.familyId = family_id
            self.families[family_id] = f

    def _load(self):
        '''
        Loads basic families, instruments and measures data from
        the phenotype database.
        '''
        if self.families is None:
            self._load_families()
        if self.instruments is None:
            self._load_instruments()

    def get_persons_df(self, roles=None, person_ids=None, family_ids=None):
        """
        Returns a individuals information form phenotype database as a data
        frame.

        `roles` -- specifies persons of which role should be returned. If not
        specified returns all individuals from phenotype database.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        Each row of the returned data frame represnts a person from phenotype
        database.

        Columns returned are: `person_id`, `family_id`, `role`, `sex`.
        """

        columns = [
            self.db.family.c.family_id,
            self.db.person.c.person_id,
            self.db.person.c.role,
            self.db.person.c.status,
            self.db.person.c.sex,
        ]
        s = select(columns)
        s = s.select_from(
            self.db.family.join(self.db.person)
        )
        if roles is not None:
            s = s.where(self.db.person.c.role.in_(roles))
        if person_ids is not None:
            s = s.where(
                self.db.person.c.person_id.in_(person_ids)
            )
        if family_ids is not None:
            s = s.where(
                self.db.family.c.family_id.in_(family_ids)
            )
        df = pd.read_sql(s, self.db.engine)
        # df.rename(columns={'sex': 'sex'}, inplace=True)
        return df[['person_id', 'family_id', 'role', 'sex', 'status']]

    def get_persons(self, roles=None, person_ids=None, family_ids=None):
        """Returns individuals data from phenotype database.

        `roles` -- specifies persons of which role should be returned. If not
        specified returns all individuals from phenotype database.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        Returns a dictionary of (`personId`, `Person()`) where
        the `Person` object is the same object used into `VariantDB` families.
        """
        persons = {}
        df = self.get_persons_df(roles=roles, person_ids=person_ids,
                                 family_ids=family_ids)

        for row in df.to_dict('records'):
            person_id = row['person_id']

            p = Person(**row)
            # p.person_id = person_id
            # p.family_id = family_id
            assert row['role'] in Role, \
                "{} not a valid role".format(row['role'])
            assert row['sex'] in Sex, \
                "{} not a valid sex".format(row['sex'])
            assert row['status'] in Status, \
                "{} not a valid status".format(row['status'])

            persons[person_id] = p
        return persons

    def get_measure(self, measure_id):
        """
        Returns a measure by measure_id.
        """
        assert measure_id in self.measures, measure_id
        return self.measures[measure_id]

    def _build_default_filter_clause(self, m, default_filter):
        if default_filter == 'skip' or m.default_filter is None:
            return None
        elif default_filter == 'apply':
            return "value {}".format(m.default_filter)
        elif default_filter == 'invert':
            return "NOT (value {})".format(m.default_filter)
        else:
            raise ValueError(
                "bad default_filter value: {}".format(default_filter))

    def _raw_get_measure_values_df(
            self, measure, person_ids=None, family_ids=None, roles=None,
            default_filter='skip'):

        measure_type = measure.measure_type
        if measure_type is None:
            raise ValueError(
                "bad measure: {}; unknown value type".format(
                    measure.measure_id))
        value_table = self.db.get_value_table(measure_type)
        columns = [
            self.db.family.c.family_id,
            self.db.person.c.person_id,
            self.db.person.c.sex,
            self.db.person.c.status,
            value_table.c.value,
        ]

        s = select(columns)
        s = s.select_from(
            value_table.
            join(self.db.measure).
            join(self.db.person).
            join(self.db.family)
        )
        s = s.where(self.db.measure.c.measure_id == measure.measure_id)

        if roles is not None:
            s = s.where(self.db.person.c.role.in_(roles))
        if person_ids is not None:
            s = s.where(
                self.db.person.c.person_id.in_(person_ids)
            )
        if family_ids is not None:
            s = s.where(
                self.db.family.c.family_id.in_(family_ids)
            )

        if measure.default_filter is not None:
            filter_clause = self._build_default_filter_clause(
                measure, default_filter)
            if filter_clause is not None:
                s = s.where(text(filter_clause))

        df = pd.read_sql(s, self.db.engine)
        df.rename(columns={'value': measure.measure_id}, inplace=True)
        return df

    def get_measure_values_df(self, measure_id,
                              person_ids=None, family_ids=None,
                              roles=None,
                              default_filter='apply'):
        """
        Returns a data frame with values for the specified `measure_id`.

        `measure_id` -- a measure ID which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are retuned.

        `default_filter` -- one of ('`skip`', '`apply`', '`invert`'). When
        the measure has a `default_filter` this argument specifies whether
        the filter should be applied or skipped or inverted.

        The returned data frame contains two columns: `person_id` for
        individuals IDs and column named as `measure_id` values of the measure.
        """

        assert measure_id in self.measures, measure_id
        measure = self.measures[measure_id]

        df = self._raw_get_measure_values_df(
            measure,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=roles,
            default_filter=default_filter)

        return df[['person_id', measure_id]]

    def get_measure_values(self, measure_id, person_ids=None, family_ids=None,
                           roles=None,
                           default_filter='apply'):
        """
        Returns a dictionary with values for the specified `measure_id`.

        `measure_id` -- a measure ID which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are returned.

        `default_filter` -- one of ('`skip`', '`apply`', '`invert`'). When
        the measure has a `default_filter` this argument specifies whether
        the filter should be applied or skipped or inverted.

        The returned dictionary contains values of the measure for
        each individual. The person_id is used as key in the dictionary.
        """

        df = self.get_measure_values_df(measure_id, person_ids, family_ids,
                                        roles,
                                        default_filter)
        res = {}
        for row in df.to_dict('records'):
            res[row['person_id']] = row[measure_id]
        return res

    def get_values_df(self, measure_ids, person_ids=None, family_ids=None,
                      roles=None,
                      default_filter='apply'):
        """
        Returns a data frame with values for given list of measures.

        Values are loaded using consecutive calls to
        `get_measure_values_df()` method for each measure in `measure_ids`.
        All data frames are joined in the end and returned.

        `measure_ids` -- list of measure ids which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are returned.
        """
        assert isinstance(measure_ids, list)
        assert len(measure_ids) >= 1
        assert all([self.has_measure(m) for m in measure_ids])

        dfs = [self.get_measure_values_df(m, person_ids, family_ids,
                                          roles, default_filter)
               for m in measure_ids]

        res_df = dfs[0]
        for i, df in enumerate(dfs[1:]):
            res_df = res_df.join(
                df.set_index('person_id'), on='person_id', how='outer',
                rsuffix='_val_{}'.format(i))

        return res_df

    def _values_df_to_dict(self, df):
        res = {}
        for row in df.to_dict('records'):
            person_id = row['person_id']
            res[person_id] = row

        return res

    def get_values(self, measure_ids, person_ids=None, family_ids=None,
                   roles=None):
        """
        Returns dictionary dictionaries with values for all `measure_ids`.

        The returned dictionary uses `person_id` as key. The value for each key
        is a dictionary of measurement values for each ID in `measure_ids`
        keyed measure_id.

        `measure_ids` -- list of measure IDs which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are returned.

        """
        df = self.get_values_df(measure_ids, person_ids, family_ids, roles)
        return self._values_df_to_dict(df)

    def get_persons_values_df(self, measure_ids, person_ids=None,
                              family_ids=None, roles=None):
        """
        Returns a data frame with values for all measures in `measure_ids`
        joined with a data frame returned by `get_persons_df`.
        """
        persons_df = self.get_persons_df(roles=roles, person_ids=person_ids,
                                         family_ids=family_ids)

        value_df = self.get_values_df(
            measure_ids,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=roles)

        df = persons_df.join(
            value_df.set_index('person_id'),
            on='person_id', how='right', rsuffix='_val')

        return df

    def _get_instrument_measures(self, instrument_name):
        """
        Returns measures for given instrument.
        """
        assert instrument_name in self.instruments
        instrument = self.instruments[instrument_name]
        measure_ids = [
            m.measure_id for m in list(instrument.measures.values())
        ]
        return measure_ids

    def get_instrument_values_df(
            self, instrument_id, person_ids=None, family_ids=None, role=None):
        """
        Returns a dataframe with values for all measures in given
        instrument (see **get_values_df**).
        """
        measure_ids = self._get_instrument_measures(instrument_id)
        res = self.get_values_df(measure_ids, person_ids, family_ids, role)
        return res

    def get_instrument_values(
            self, instrument_id, person_ids=None, family_ids=None, role=None):
        """
        Returns a dictionary with values for all measures in given
        instrument (see :func:`get_values`).
        """
        measure_ids = self._get_instrument_measures(instrument_id)
        df = self.get_values_df(measure_ids, person_ids, family_ids, role)
        return self._values_df_to_dict(df)

    def has_measure(self, measure_id):
        """
        Checks is `measure_id` is value ID for measure in our phenotype DB.
        """
        return measure_id in self.measures


class PhenotypeDataGroup(PhenotypeData):
    # TODO Implement
    pass


class PhenoDb(object):

    def __init__(self, dae_config):
        super(PhenoDb, self).__init__()
        assert dae_config

        self.config = PhenoConfigParser.read_directory_configurations(
            dae_config.phenotype_data.dir)

        self.pheno_cache = {}

    def get_dbfile(self, pheno_data_id):
        return self.config[pheno_data_id].dbfile

    def get_dbconfig(self, pheno_data_id):
        return self.config[pheno_data_id]

    def has_phenotype_data(self, pheno_data_id):
        return pheno_data_id in self.config

    def get_phenotype_data_ids(self):
        return list(self.config.keys())

    def get_phenotype_data(self, pheno_data_id):
        if not self.has_phenotype_data(pheno_data_id):
            raise ValueError('cannot find phenotype data {};'
                             ' available phenotype data: {}'
                             .format(pheno_data_id,
                                     self.get_phenotype_data_ids()))
        if pheno_data_id in self.pheno_cache:
            phenotype_data = self.pheno_cache[pheno_data_id]
        else:
            LOGGER.info('loading pheno db <{}>'.format(pheno_data_id))
            phenotype_data = PhenotypeDataStudy(
                dbfile=self.get_dbfile(pheno_data_id)
            )
            self.pheno_cache[pheno_data_id] = phenotype_data
        return phenotype_data

    def get_all_phenotype_data(self):
        return [
            self.get_phenotype_data(pheno_id)
            for pheno_id in self.get_phenotype_data_ids()
        ]

    def get_phenotype_data_config(self, pheno_data_id):
        return self.config.get(pheno_data_id)

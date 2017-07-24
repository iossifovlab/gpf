'''
Created on Sep 10, 2016

@author: lubo
'''
import numpy as np
import pandas as pd
from sqlalchemy.sql import select
from sqlalchemy import or_, not_

from collections import defaultdict, OrderedDict

from pheno.utils.configuration import PhenoConfig
from pheno.models import  \
    RawValueManager,\
    MetaVariableCorrelationManager,\
    ValueModel
from VariantsDB import Person, Family
import copy
from pheno.db import DbManager


class Instrument(object):
    """
    Instrument object represents phenotype instruments.

    Common fields are:

    * `instrument_name`

    * `masures` -- dictionary of all measures in the instrument

    * `has_probands` -- if any of measures is applied to probands

    * `has_siblings` -- if any of measures is applied to siblings

    * `has_parents` -- if any of measures is applied to parents
    """

    def __init__(self, name):
        self.name = name

        self.measures = OrderedDict()
        self.has_probands = None
        self.has_siblings = None
        self.has_parents = None

    def __repr__(self):
        return "Instrument({}, {})".format(self.name, len(self.measures))


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

    * `has_probands` - returns True if this measure is applied to probands

    * `has_siblings` - returns True if this measrue is applied to siblings

    * `has_parents` - returns True if this measure is applied to parents

    """

    def __init__(self, name):
        self.name = name
        self.measure_name = name

    def __repr__(self):
        return "Measure({}, {}, {})".format(
            self.measure_id, self.measure_type,
            self.value_domain)

    @classmethod
    def _from_df(cls, row):
        """
        Creates `Measure` object from pandas data frame row.
        """
        assert row['measure_type'] is not None

        m = Measure(row['measure_name'])
        m.measure_id = row['measure_id']
        m.instrument_name = row['instrument_name']
        m.measure_type = row['measure_type']

        m.description = row['description']
        m.min_value = None
        m.max_value = None
        if m.measure_type == 'continuous' or m.measure_type == 'ordinal':
            m.min_value = row['min_value']
            m.max_value = row['max_value']
#             assert m.max_value >= m.min_value, \
#                 "%s, %s, %s" % (m.measure_id, m.min_value, m.max_value)
        m.value_domain = row['value_domain']
        m.has_probands = row['has_probands']
        m.has_siblings = row['has_siblings']
        m.has_parents = row['has_parents']

        if isinstance(row['default_filter'], float) and \
                np.isnan(row['default_filter']):
            m.default_filter = None
        else:
            m.default_filter = row['default_filter']

        return m


class MeasureMeta(Measure):
    """
    **this class should be moved out of this package.**

    Represents additional meta information about given `Measure`.
    """

    def __init__(self, name):
        super(MeasureMeta, self).__init__(name)


class PhenoDB(PhenoConfig):
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

    def __init__(
            self, pheno_db='ssc',
            config=None, *args, **kwargs):
        super(PhenoDB, self).__init__(pheno_db=pheno_db,
                                      config=config,
                                      *args, **kwargs)

        self.families = None
        self.persons = None
        self.instruments = None
        self.measures = {}
        self.age = self._load_common_config('age')
        self.nonverbal_iq = self._load_common_config('nonverbal_iq')
        self.db = DbManager(dbfile=self.get_dbfile())
        self.db.build()

    def _load_common_config(self, name):
        if self.config.has_option(self.pheno_db, name):
            age = self.config.get(self.pheno_db, name)
            parts = age.split(':')
            if len(parts) == 1:
                instrument_name = None
                measure_name = parts[0]
            elif len(parts) == 2:
                instrument_name = parts[0]
                measure_name = parts[1]
            return {
                'name': name,
                'instrument_name': instrument_name,
                'measure_name': measure_name,
            }

    def get_age_measure_id(self, measure_id):
        age = copy.copy(self.age)
        return self._get_configured_measure_id(age, measure_id)

    def get_nonverbal_iq_measure_id(self, measure_id):
        nonverbal_iq = copy.copy(self.nonverbal_iq)
        return self._get_configured_measure_id(nonverbal_iq, measure_id)

    def _get_configured_measure_id(self, base_measure_config, measure_id):
        assert self.has_measure(measure_id)
        if base_measure_config.get('instrument_name', None) is None:
            measure = self.get_measure(measure_id)
            base_measure_config['instrument_name'] = measure.instrument_name
        age_id = "{instrument_name}.{measure_name}".format(
            **base_measure_config)
        if self.has_measure(age_id):
            return age_id
        else:
            return None

    @staticmethod
    def _check_nan(val):
        if val is None:
            return None

        if not isinstance(val, float):
            raise ValueError("unexpected value: {}".format(val))

        if np.isnan(val):
            return None
        else:
            return val

    @staticmethod
    def _rename_forward(df, mapping):
        names = df.columns.tolist()
        for n, f in mapping:
            if n in names:
                names[names.index(n)] = f
        df.columns = names

    def _where_variables(self, variable_ids):
        return 'variable_id IN ({})'.format(
            ','.join(["'{}'".format(v) for v in variable_ids]))

    def get_measures_corellations_df(
            self, measures_df, correlations_with, role):
        """
        **this method should be moved out of this package**
        """

        def names(correlation_with, role, gender):
            suffix = '{}.{}.{}'.format(
                role,
                gender,
                correlation_with)
            return (
                'coeff.{}'.format(suffix),
                'pvalue.{}'.format(suffix)
            )
        assert measures_df is not None

        dfs = [measures_df]
        for correlation_with in correlations_with:
            for gender in ['M', 'F']:
                where_variables = self._where_variables(
                    measures_df.measure_id.unique())
                where = "correlation_with = '{}' AND " \
                    "role = '{}' AND " \
                    "gender = '{}' AND {}".format(
                        correlation_with,
                        role, gender,
                        where_variables)
                with MetaVariableCorrelationManager(
                        dbfile=self.get_dbfile()) as vm:
                    df = vm.load_df(where)
                    self._rename_forward(df, [('variable_id', 'measure_id')])
                    df = df[['measure_id', 'coeff', 'pvalue']]
                    self._rename_forward(
                        df, zip(
                            ['coeff', 'pvalue'],
                            names(correlation_with, role, gender)))
                    dfs.append(df)

        res_df = dfs[0]
        for i, df in enumerate(dfs[1:]):
            res_df = res_df.join(
                df.set_index('measure_id'), on='measure_id',
                rsuffix='_val_{}'.format(i))

        return res_df

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

        variable = self.db.variable
        meta_variable = self.db.meta_variable

        columns = [
            variable.c.variable_id,
            variable.c.table_name,
            variable.c.variable_name,
            variable.c.description,
            variable.c.individuals,
            variable.c.stats,
            variable.c.value_domain,
            meta_variable.c.min_value,
            meta_variable.c.max_value,
            meta_variable.c.has_probands,
            meta_variable.c.has_siblings,
            meta_variable.c.has_parents,
            meta_variable.c.default_filter,
        ]
        s = select(columns)
        s = s.select_from(
            variable.join(
                meta_variable,
                variable.c.variable_id == meta_variable.c.variable_id
            )
        )
        s = s.where(not_(variable.c.stats.is_(None)))
        if instrument is not None:
            s = s.where(variable.c.table_name == instrument)
        if measure_type is not None:
            s = s.where(variable.c.stats == measure_type)

        df = pd.read_sql(s, self.db.engine)

        res_df = df[[
            'variable_id', 'variable_name', 'table_name',
            'description', 'individuals', 'stats',
            'min_value', 'max_value', 'value_domain',
            'has_probands', 'has_siblings', 'has_parents',
            'default_filter'
        ]]
        mapping = [
            ('variable_id', 'measure_id'),
            ('variable_name', 'measure_name'),
            ('stats', 'measure_type'),
            ('table_name', 'instrument_name'),
        ]
        self._rename_forward(res_df, mapping)

        return res_df

    def get_measures(self, instrument=None, measure_type=None):
        """
        Returns a dictionary of measures objects.

        `instrument` -- an instrument name which measures should be
        returned. If not specified all type of measures are returned.

        `measure_type` -- a type ('continuous', 'ordinal' or 'categorical')
        of measures that should be returned. If not specified all
        type of measures are returned.

        """
        df = self._get_measures_df(instrument, measure_type)
        res = OrderedDict()
        for _index, row in df.iterrows():
            m = Measure._from_df(row)
            res[m.measure_id] = m
        return res

    def _load_instruments(self):
        instruments = OrderedDict()

        df = self._get_measures_df()
        instrument_names = df.instrument_name.unique()

        for instrument_name in instrument_names:
            instrument = Instrument(instrument_name)
            measures = OrderedDict()
            measures_df = df[df.instrument_name == instrument_name]
            instrument.has_probands = np.any(measures_df.has_probands)
            instrument.has_siblings = np.any(measures_df.has_siblings)
            instrument.has_parents = np.any(measures_df.has_parents)

            for _index, row in measures_df.iterrows():
                m = Measure._from_df(row)
                m.instrument = instrument
                measures[m.name] = m
                self.measures[m.measure_id] = m
            instrument.measures = measures
            instruments[instrument.name] = instrument

        self.instruments = instruments

    def _load_families(self):
        families = defaultdict(list)
        persons = self.get_persons()

        for p in persons.values():
            families[p.atts['family_id']].append(p)

        self.persons = persons
        self.families = {}

        for family_id, members in families.items():
            f = Family()
            f.memberInOrder = members
            f.familyId = family_id
            self.families[family_id] = f

    def load(self):
        """Loads basic families, instruments and measures data from
        the phenotype database."""
        if self.families is None:
            self._load_families()
        if self.instruments is None:
            self._load_instruments()

    def get_persons_df(self, roles=None, person_ids=None, family_ids=None,
                       present=1):
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

        Columns returned are: `person_id`, `family_id`, `role`, `gender`.
        """

        s = select([self.db.person])
        s = s.where(self.db.person.c.ssc_present == present)
        if roles:
            s = s.where(or_(
                *[self.db.person.c.role == r for r in roles]
            ))
        df = pd.read_sql(s, self.db.engine)
        df.sort_values(['family_id', 'role_order'], inplace=True)

        if person_ids:
            df = df[df.person_id.isin(person_ids)]
        if family_ids:
            df = df[df.family_id.isin(family_ids)]

        return df[['person_id', 'family_id', 'role', 'gender']]

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
        persons = OrderedDict()
        df = self.get_persons_df(roles=roles, person_ids=person_ids,
                                 family_ids=family_ids)

        for _index, row in df.iterrows():
            person_id = row['person_id']
            family_id = row['family_id']

            atts = {
                'family_id': family_id,
                'person_id': person_id,
                'role': row['role'],
                'gender': row['gender'],
            }
            p = Person(atts)
            p.personId = person_id
            p.role = atts['role']
            p.gender = atts['gender']

            persons[person_id] = p
        return persons

    def get_measure(self, measure_id):
        """
        Returns a measure by measure_id.
        """
        assert measure_id in self.measures
        return self.measures[measure_id]

    def _get_values_df(self, value_manager, where):
        with value_manager(dbfile=self.get_dbfile()) as vm:
            df = vm.load_df(where=where)
            return df

        return None

    @staticmethod
    def _rename_value_column(measure_id, df):
        names = df.columns.tolist()
        names[names.index('value')] = measure_id
        df.columns = names

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

    @staticmethod
    def _roles_clause(roles, column_name):
        clauses = ["{} = '{}'".format(column_name, role) for role in roles]
        return " ( {} ) ".format(' or '.join(clauses))

    def _raw_get_measure_values_df(
            self, measure, person_ids=None, family_ids=None, roles=None,
            default_filter='skip'):

        value_type = measure.measure_type
        if value_type is None:
            raise ValueError(
                "bad measure: {}; unknown value type".format(
                    measure.measure_id))
        value_manager = ValueModel.get_value_manager(value_type)
        clauses = ["variable_id = '{}'".format(measure.measure_id)]
        if roles:
            roles_clause = self._roles_clause(roles, 'person_role')
            clauses.append(roles_clause)
        if measure.default_filter is not None:
            filter_clause = self._build_default_filter_clause(
                measure, default_filter)
            if filter_clause is not None:
                clauses.append(filter_clause)
        where = ' and '.join(clauses)
        df = self._get_values_df(value_manager, where)
        if person_ids:
            df = df[df.person_id.isin(person_ids)]
        if family_ids:
            df = df[df.family_id.isin(family_ids)]
        self._rename_value_column(measure.measure_id, df)
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

        assert measure_id in self.measures
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
        for _index, row in df.iterrows():
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
                df.set_index('person_id'), on='person_id',
                rsuffix='_val_{}'.format(i))

        return res_df

    def _values_df_to_dict(self, measure_ids, df):
        res = {}
        for _index, row in df.iterrows():
            person_id = row.person_id
            vals = {}
            for mid in measure_ids:
                vals[mid] = row[mid]

            res[person_id] = vals

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
        return self._values_df_to_dict(measure_ids, df)

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
            value_df.set_index('person_id'), on='person_id', rsuffix='_val')
        df.dropna(inplace=True)

        return df

    def get_instrument_measures(self, instrument_id):
        """
        Returns measures for given instrument.
        """
        assert instrument_id in self.instruments
        measure_ids = [m.measure_id for
                       m in self.instruments[instrument_id].measures.values()]
        return measure_ids

    def get_instrument_values_df(
            self, instrument_id, person_ids=None, family_ids=None, role=None):
        """
        Returns a dataframe with values for all measures in given
        instrument (see **get_values_df**).
        """
        measure_ids = self.get_instrument_measures(instrument_id)
        res = self.get_values_df(measure_ids, person_ids, family_ids, role)
        return res

    def get_instrument_values(
            self, instrument_id, person_ids=None, family_ids=None, role=None):
        """
        Returns a dictionary with values for all measures in given
        instrument (see :ref:`get_values`).
        """
        measure_ids = self.get_instrument_measures(instrument_id)
        df = self.get_values_df(measure_ids, person_ids, family_ids, role)
        return self._values_df_to_dict(measure_ids, df)

    def get_instruments(self, person_id):
        """
        Returns dictionary with all instruments applied to given
        individual.

        """
        query = "SELECT DISTINCT table_name FROM variable WHERE " \
            "variable_id IN " \
            "(SELECT variable_id FROM value_raw WHERE person_id='{}')" \
            .format(person_id)
        with RawValueManager(dbfile=self.get_dbfile()) as vm:
            instruments = vm._execute(query)
        return dict([(i[0], self.instruments[i[0]]) for i in instruments
                     if i[0] in self.instruments])

    @staticmethod
    def _split_measure_id(measure_id):
        if '.' not in measure_id:
            return (None, measure_id)
        else:
            [instrument_name, measure_name] = measure_id.split('.')
            return (instrument_name, measure_name)

    def has_measure(self, measure_id):
        """
        Checks is `measure_id` is value ID for measure in our phenotype DB.
        """
        return measure_id in self.measures

import os
import re
import logging
from collections import defaultdict, OrderedDict

import numpy as np
import pandas as pd
from multiprocessing import Pool
from box import Box

from dae.pheno.db import DbManager
from dae.pheno.common import RoleMapping, MeasureType
from dae.variants.attributes import Role
from dae.pedigrees.loader import FamiliesLoader, PED_COLUMNS_REQUIRED
from dae.pheno.prepare.measure_classifier import (
    MeasureClassifier,
    convert_to_string,
    convert_to_numeric,
    ClassifierReport,
)


logger = logging.getLogger(__name__)


class PrepareCommon(object):
    PID_COLUMN = "$PID"
    PERSON_ID = "person_id"
    PED_COLUMNS_REQUIRED = tuple(PED_COLUMNS_REQUIRED)


class PrepareBase(PrepareCommon):
    def __init__(self, config):
        assert config is not None
        self.config = config
        self.db = DbManager(self.config.db.filename)
        self.db.build()
        self.persons = None

    def get_persons(self, force=False):
        if not self.persons or force:
            self.persons = self.db.get_persons()
        return self.persons


class PreparePersons(PrepareBase):
    def __init__(self, config):
        super(PreparePersons, self).__init__(config)

    def _prepare_families(self, ped_df):
        if self.config.family.composite_key:
            pass
        return ped_df

    def _map_role_column(self, ped_df):
        assert self.config.person.role.type == "column"
        role_column = self.config.person.role.column
        assert (
            role_column in ped_df.columns
        ), "can't find column '{}' into pedigree file".format(role_column)
        mapping_name = self.config.person.role.mapping
        mapping = getattr(RoleMapping(), mapping_name)
        assert mapping is not None, "bad role mapping '{}'".format(
            mapping_name
        )

        roles = pd.Series(ped_df.index)
        for index, row in ped_df.iterrows():
            if type(row["role"]) is not Role:
                role = mapping.get(row["role"])
            else:
                role = row["role"]
            # roles[index] = role.value
            roles[index] = role
        ped_df["role"] = roles
        return ped_df

    def _prepare_persons(self, ped_df):
        assert self.config.person.role.type != "guess", (
            "Guessing roles has been deprecated - "
            " please provide a column with roles!"
        )

        if self.config.person.role.type == "column":
            ped_df = self._map_role_column(ped_df)
        # elif self.config.person.role.type == 'guess':
        #     ped_df = PedigreeRoleGuesser.guess_role_nuc(ped_df)
        return ped_df

    def prepare_pedigree(self, ped_df):
        assert set(self.PED_COLUMNS_REQUIRED) <= set(ped_df.columns)
        ped_df = self._prepare_families(ped_df)
        ped_df = self._prepare_persons(ped_df)
        logger.info(f"pedigree columns: {ped_df.columns}")
        return ped_df

    def _save_families(self, ped_df):
        families = [{"family_id": fid} for fid in ped_df["family_id"].unique()]
        ins = self.db.family.insert()
        with self.db.pheno_engine.connect() as connection:
            connection.execute(ins, families)

    @staticmethod
    def _build_sample_id(sample_id):
        if isinstance(sample_id, float) and np.isnan(sample_id):
            return None
        elif sample_id is None:
            return None

        return str(sample_id)

    def _save_persons(self, ped_df):
        families = self.db.get_families()
        persons = []
        for _index, row in ped_df.iterrows():
            p = {
                "family_id": families[row["family_id"]].id,
                self.PERSON_ID: row["person_id"],
                "role": row["role"],
                "status": row["status"],
                "sex": row["sex"],
                "sample_id": self._build_sample_id(row.get("sample_id")),
            }
            persons.append(p)
        ins = self.db.person.insert()
        with self.db.pheno_engine.connect() as connection:
            connection.execute(ins, persons)

    def save_pedigree(self, ped_df):
        self._save_families(ped_df)
        self._save_persons(ped_df)

    def build_pedigree(self, pedfile):
        ped_df = FamiliesLoader.flexible_pedigree_read(pedfile)
        ped_df = self.prepare_pedigree(ped_df)
        self.save_pedigree(ped_df)
        self.pedigree_df = ped_df
        return ped_df


class Task(PrepareCommon):
    def run(self):
        raise NotImplementedError()

    def done(self):
        raise NotImplementedError()

    def __next__(self):
        raise NotImplementedError()

    def __call__(self):
        return self.run()


class ClassifyMeasureTask(Task):
    def __init__(
        self, config, instrument_name, measure_name, measure_desc, df
    ):
        self.config = config
        self.mdf = df[[self.PERSON_ID, self.PID_COLUMN, measure_name]].copy()
        self.mdf.rename(columns={measure_name: "value"}, inplace=True)
        self.measure = self.create_default_measure(
            instrument_name, measure_name, measure_desc
        )

    @staticmethod
    def create_default_measure(instrument_name, measure_name, measure_desc):
        measure = {
            "measure_type": MeasureType.other,
            "measure_name": measure_name,
            "instrument_name": instrument_name,
            "measure_id": "{}.{}".format(instrument_name, measure_name),
            "description": measure_desc,
            "individuals": None,
            "default_filter": None,
            "min_value": None,
            "max_value": None,
            "values_domain": None,
            "rank": None,
        }
        measure = Box(measure)
        return measure

    def build_meta_measure(self):
        measure_type = self.measure.measure_type

        if measure_type in set([MeasureType.continuous, MeasureType.ordinal]):
            min_value = np.min(self.classifier_report.numeric_values)
            max_value = np.max(self.classifier_report.numeric_values)
        else:
            min_value = None
            max_value = None
        if measure_type in set([MeasureType.continuous, MeasureType.ordinal]):
            values_domain = "[{}, {}]".format(min_value, max_value)
        else:
            distribution = self.classifier_report.calc_distribution_report()
            unique_values = [v for (v, _) in distribution if v.strip() != ""]
            values_domain = ", ".join(sorted(unique_values))

        self.measure.min_value = min_value
        self.measure.max_value = max_value
        self.measure.values_domain = values_domain
        self.rank = self.classifier_report.count_unique_values

    def run(self):
        try:
            logging.info("classifying measure {self.measure.measure_id}")
            values = self.mdf["value"]
            classifier = MeasureClassifier(self.config)
            self.classifier_report = classifier.meta_measures(values)
            self.measure.individuals = self.classifier_report.count_with_values
            self.measure.measure_type = classifier.classify(
                self.classifier_report
            )
            self.build_meta_measure()
        except Exception:
            logger.exception(
                f"problem processing measure: {self.measure.measure_id}")
        return self

    def done(self):
        return self.measure, self.classifier_report, self.mdf


class MeasureValuesTask(Task):
    def __init__(self, measure, mdf):
        self.measure = measure
        self.mdf = mdf

    def run(self):
        measure_id = self.measure.db_id
        measure = self.measure

        values = OrderedDict()
        measure_values = self.mdf.to_dict(orient="records")
        for record in measure_values:
            pid = int(record[self.PID_COLUMN])
            assert pid, measure.measure_id
            k = (pid, measure_id)
            value = record["value"]
            if MeasureType.is_text(measure.measure_type):
                value = convert_to_string(value)
                if value is None:
                    continue
                assert isinstance(value, str), record["value"]
            elif MeasureType.is_numeric(measure.measure_type):
                value = convert_to_numeric(value)
                if np.isnan(value):
                    continue
            else:
                assert False, measure.measure_type.name
            v = {self.PERSON_ID: pid, "measure_id": measure_id, "value": value}

            if k in values:
                logger.info(
                    f"updating measure {measure.measure_id} "
                    f"for person {record['person_id']} value "
                    f"{values[k]['value']} "
                    f"with {value}")
            values[k] = v
        self.values = values
        return self

    def done(self):
        return self.measure, self.values


class TaskQueue(object):
    def __init__(self):
        self.queue = []

    def put(self, task):
        self.queue.append(task)

    def empty(self):
        return len(self.queue) == 0

    def get(self):
        return self.queue.pop(0)


class PrepareVariables(PreparePersons):
    def __init__(self, config):
        super(PreparePersons, self).__init__(config)
        self.sample_ids = None
        self.classifier = MeasureClassifier(config)

        self.pool = Pool(processes=self.config.parallel)

    def _get_person_column_name(self, df):
        if self.config.person.column:
            person_id = self.config.person.column
        else:
            person_id = df.columns[0]
        logger.debug(f"Person ID: {person_id}")
        return person_id

    def load_instrument(self, instrument_name, filenames):
        assert filenames
        assert all([os.path.exists(f) for f in filenames])

        # instrument_names = [
        #     os.path.splitext(os.path.basename(f))[0] for f in filenames
        # ]
        # assert len(set(instrument_names)) == 1
        # assert instrument_name == instrument_names[0]

        dataframes = []
        sep = ","

        if self.config.instruments.tab_separated:
            sep = "\t"

        for filename in filenames:
            logger.info(f"reading instrument: {filename}")
            df = pd.read_csv(
                filename, sep=sep, low_memory=False, encoding="ISO-8859-1"
            )
            person_id = self._get_person_column_name(df)
            logging.info(
                f"renaming column '{person_id}' to '{self.PERSON_ID}' "
                f"in instrument: {instrument_name}"
            )

            df = df.rename(columns={person_id: self.PERSON_ID})
            dataframes.append(df)
        assert len(dataframes) >= 1

        if len(dataframes) == 1:
            df = dataframes[0]
        else:
            assert len(set([len(f.columns) for f in dataframes])) == 1
            df = pd.concat(dataframes, ignore_index=True)

        assert df is not None
        if len(df) == 0:
            return df

        df = self._augment_person_ids(df)
        df = self._adjust_instrument_measure_names(instrument_name, df)
        return df

    def _adjust_instrument_measure_names(self, instrument_name, df):
        if len(df) == 0:
            return df

        columns = {}
        for index in range(1, len(df.columns)):
            name = df.columns[index]
            parts = [p.strip() for p in name.split(".")]
            parts = [p for p in parts if p != instrument_name]
            columns[name] = ".".join(parts)
        df.rename(columns=columns, inplace=True)
        return df

    @property
    def log_filename(self):
        db_filename = self.config.db.filename
        if self.config.report_only:
            filename = self.config.report_only
            assert db_filename == "memory"
            return filename
        else:
            filename, _ext = os.path.splitext(db_filename)
            filename = filename + "_report_log.tsv"
            return filename

    def log_header(self):
        with open(self.log_filename, "w") as log:
            log.write(ClassifierReport.header_line())
            log.write("\n")

    def log_measure(self, measure, classifier_report):
        classifier_report.set_measure(measure)
        logging.info(classifier_report.log_line(short=True))

        with open(self.log_filename, "a") as log:
            log.write(classifier_report.log_line())
            log.write("\n")

    def save_measure(self, measure):
        to_save = measure.to_dict()
        assert "db_id" not in to_save, to_save
        ins = self.db.measure.insert().values(**to_save)
        with self.db.pheno_engine.begin() as connection:
            result = connection.execute(ins)
            measure_id = result.inserted_primary_key[0]

        return measure_id

    def save_measure_values(self, measure, values):
        if len(values) == 0:
            logging.warning(
                f"skiping measure {measure.measure_id} without values"
            )
            return
        logging.info(
            f"saving measure {measure.measure_id} values {len(values)}")
        value_table = self.db.get_value_table(measure.measure_type)
        ins = value_table.insert()

        with self.db.pheno_engine.begin() as connection:
            connection.execute(ins, list(values.values()))

    def _collect_instruments(self, dirname):
        regexp = re.compile("(?P<instrument>.*)(?P<ext>\\.csv.*)")
        instruments = defaultdict(list)
        for root, _dirnames, filenames in os.walk(dirname):
            for filename in filenames:
                basename = os.path.basename(filename)
                basename = basename.lower()
                res = regexp.match(basename)
                if not res:
                    logger.debug(
                        f"filename {basename} is not an instrument; "
                        f"skipping...")
                    continue
                logger.debug(
                    f"instrument matched: {res.group('instrument')}; "
                    f"file extension: {res.group('ext')}")
                instruments[res.group("instrument")].append(
                    os.path.abspath(os.path.join(root, filename))
                )
        return instruments

    def build_variables(self, instruments_dirname, description_path):
        self.log_header()

        self.build_pheno_common()

        instruments = self._collect_instruments(instruments_dirname)
        descriptions = PrepareVariables.load_descriptions(description_path)
        for instrument_name, instrument_filenames in list(instruments.items()):
            assert instrument_name is not None
            df = self.load_instrument(instrument_name, instrument_filenames)
            if len(df) == 0:
                logger.info(
                    f"instrument {instrument_name} is empty; skipping")
                continue
            self.build_instrument(instrument_name, df, descriptions)

    def _augment_person_ids(self, df):
        persons = self.get_persons()
        pid = pd.Series(df.index)
        for index, row in df.iterrows():
            p = persons.get(row[self.PERSON_ID])
            if p is None:
                pid[index] = np.nan
                logging.info(
                    f"measure for missing person: {row[self.PERSON_ID]}")
            else:
                assert p is not None
                assert p.person_id == row[self.PERSON_ID]
                pid[index] = p.id

        df[self.PID_COLUMN] = pid
        if len(df) > 0:
            df = df[np.logical_not(np.isnan(df[self.PID_COLUMN]))].copy()
        return df

    def build_pheno_common(self):
        pheno_common_measures = set(self.pedigree_df.columns) - (
            set(self.PED_COLUMNS_REQUIRED) | set(["sampleId", "role"])
        )

        df = self.pedigree_df.copy(deep=True)
        df.rename(columns={"personId": self.PERSON_ID}, inplace=True)
        assert self.PERSON_ID in df.columns
        df = self._augment_person_ids(df)

        pheno_common_columns = [
            self.PERSON_ID,
            self.PID_COLUMN,
        ]
        pheno_common_columns.extend(pheno_common_measures)
        self.build_instrument("pheno_common", df[pheno_common_columns])

    def build_instrument(self, instrument_name, df, descriptions=None):

        assert df is not None
        assert self.PERSON_ID in df.columns

        classify_queue = TaskQueue()
        save_queue = TaskQueue()

        for measure_name in df.columns:
            if (
                measure_name == self.PID_COLUMN
                or measure_name == self.PERSON_ID
            ):
                continue

            if descriptions:
                measure_desc = descriptions(instrument_name, measure_name)
            else:
                measure_desc = None

            classify_task = ClassifyMeasureTask(
                self.config, instrument_name, measure_name, measure_desc, df
            )
            res = self.pool.apply_async(classify_task)
            classify_queue.put(res)
        while not classify_queue.empty():
            res = classify_queue.get()
            task = res.get()
            measure, classifier_report, _mdf = task.done()
            self.log_measure(measure, classifier_report)
            if measure.measure_type == MeasureType.skipped:
                logging.info(
                    f"skip saving measure: {measure.measure_id}; "
                    f"measurings: {classifier_report.count_with_values}")
                continue
            save_queue.put(task)

        if self.config.report_only:
            return

        values_queue = TaskQueue()
        while not save_queue.empty():
            task = save_queue.get()
            measure, classifier_report, mdf = task.done()

            measure_id = self.save_measure(measure)
            measure.db_id = measure_id
            values_task = MeasureValuesTask(measure, mdf)
            res = self.pool.apply_async(values_task)
            values_queue.put(res)

        while not values_queue.empty():
            res = values_queue.get()
            values_task = res.get()
            measure, values = values_task.done()
            self.save_measure_values(measure, values)

        return df

    @staticmethod
    def create_default_measure(instrument_name, measure_name):
        measure = {
            "measure_type": MeasureType.other,
            "measure_name": measure_name,
            "instrument_name": instrument_name,
            "measure_id": "{}.{}".format(instrument_name, measure_name),
            "individuals": None,
            "default_filter": None,
        }
        measure = Box(measure)
        return measure

    def classify_measure(self, instrument_name, measure_name, df):
        measure = self.create_default_measure(instrument_name, measure_name)
        values = df["value"]

        classifier_report = self.classifier.meta_measures(values)
        measure.individuals = classifier_report.count_with_values
        measure.measure_type = self.classifier.classify(classifier_report)

        return classifier_report, measure

    @staticmethod
    def load_descriptions(description_path):
        if not description_path:
            return None
        assert os.path.exists(
            os.path.abspath(description_path)
        ), description_path

        df = pd.read_csv(description_path, sep="\t")

        class DescriptionDf:
            def __init__(self, desc_df):
                self.desc_df = desc_df
                assert all(
                    [
                        col in list(desc_df)
                        for col in [
                            "instrumentName",
                            "measureName",
                            "measureId",
                            "description",
                        ]
                    ]
                ), list(desc_df)

            def __call__(self, iname, mname):
                if (
                    "{}.{}".format(iname, mname)
                    not in self.desc_df["measureId"].values
                ):
                    return None
                row = self.desc_df.query(
                    (
                        "(instrumentName == @iname) and "
                        "(measureName == @mname)"
                    )
                )
                return row.iloc[0]["description"]

        return DescriptionDf(df)


# class PrepareMetaMeasures(PrepareBase):
#
#     def __init__(self, config):
#         super(PrepareMetaMeasures, self).__init__(config)
#         self.pheno = PhenoDB(dbfile=self.db.dbfile)
#         self.pheno.load(skip_meta=True)
#
#     def build_meta(self):
#         measures = self.db.get_measures()
#         for m in measures.values():
#             self.build_meta_measure(m)
#
#     def build_meta_measure(self, measure):
#         print("processing meta measures for {}".format(measure.measure_id))
#         df = self.pheno.get_measure_values_df(measure.measure_id)
#         measure_type = measure.measure_type
#         values = df[measure.measure_id]
#         rank = len(values.unique())
#
#         if measure_type in \
#                 set([MeasureType.continuous, MeasureType.ordinal]):
#             min_value = values.values.min()
#             max_value = values.values.max()
#         else:
#             min_value = None
#             max_value = None
#         if measure_type == MeasureType.continuous:
#             values_domain = "[{}, {}]".format(min_value, max_value)
#         else:
#             unique_values = sorted(values.unique())
#             unique_values = [str(v) for v in unique_values]
#             values_domain = ",".join(unique_values)
#
#         meta = {
#             'measure_id': measure.id,
#             'min_value': min_value,
#             'max_value': max_value,
#             'values_domain': values_domain,
#             'rank': rank,
#         }
#         try:
#             insert = self.db.meta_measure.insert().values(**meta)
#             with self.db.engine.begin() as connection:
#                 connection.execute(insert)
#         except Exception:
#             del meta['measure_id']
#             update = self.db.meta_measure.update().values(**meta).where(
#                 self.db.meta_measure.c.measure_id == measure.id
#             )
#             with self.db.engine.begin() as connection:
#                 connection.execute(update)

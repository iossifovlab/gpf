'''
Created on Apr 10, 2017

@author: lubo
'''
import os


class PreparePhenoBrowserBase(object):

    LARGE_DPI = 300
    SMALL_DPI = 16

    def __init__(self, pheno_db, output_dir):
        assert os.path.exists(output_dir)
        self.output_dir = output_dir
        self.pheno_db = pheno_db

    def load_measure(self, measure):
        df = self.pheno_db.get_persons_values_df([measure.measure_id])
        df.loc[df.role == 'mom', 'role'] = 'parent'
        df.loc[df.role == 'dad', 'role'] = 'parent'
        return df

    def _augment_measure_values_df(self, augment, measure):
        augment_instrument = augment['instrument_name']
        augment_measure = augment['measure_name']

        if augment_instrument is not None:
            augment_id = '{}.{}'.format(
                augment_instrument, augment_measure)
        else:
            augment_id = '{}.{}'.format(
                measure.instrument_name, augment_measure)

        df = self.pheno_db.get_persons_values_df(
            [augment_id, measure.measure_id])
        df.loc[df.role == 'mom', 'role'] = 'parent'
        df.loc[df.role == 'dad', 'role'] = 'parent'

        columns = list(df.columns)
        columns[columns.index(augment_id)] = augment['name']
        df.columns = columns
        return df

    def load_measure_and_age(self, measure):
        return self._augment_measure_values_df(
            self.pheno_db.age, measure)

    def load_measure_and_nonverbal_iq(self, measure):
        return self._augment_measure_values_df(
            self.pheno_db.nonverbal_iq, measure)

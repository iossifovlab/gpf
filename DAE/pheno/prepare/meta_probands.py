'''
Created on Oct 14, 2016

@author: lubo
'''
import numpy as np
import statsmodels.api as sm

from pheno.pheno_db import PhenoDB
from pheno.models import MetaVariableManager, MetaVariableModel,\
    MetaVariableCorrelationManager, MetaVariableCorrelationModel


class PrepareMetaProbands(object):

    def __init__(self):
        self.phdb = PhenoDB()
        self.phdb.load()

    def create_tables(self):
        with MetaVariableManager() as vm:
            vm.create_tables()
        with MetaVariableCorrelationManager() as vm:
            vm.create_tables()

    def drop_tables(self):
        with MetaVariableManager() as vm:
            vm.drop_tables()
        with MetaVariableCorrelationManager() as vm:
            vm.drop_tables()

    def load_measure(self, m):
        df = self.phdb.get_persons_values_df(
            ['pheno_common.age', 'pheno_common.non_verbal_iq', m.measure_id])
        df.loc[df.role == 'mom', 'role'] = 'parent'
        df.loc[df.role == 'dad', 'role'] = 'parent'
        return df

    def _build_regression(self, df, m, correlation_with, role, gender):
        assert m.measure_id in df.columns
        assert correlation_with in df.columns

        with MetaVariableCorrelationManager() as vm:
            v = MetaVariableCorrelationModel()
            v.variable_id = m.measure_id
            v.correlation_with = correlation_with
            v.role = role
            v.gender = gender

            dd = df[np.logical_and(df.role == role, df.gender == gender)]
            dd = dd.dropna()

            if len(dd) <= 5:
                print("SKIPPING REGRESSION: {}, {}".format(role, gender))
                return

            x = dd[correlation_with]
            X = sm.add_constant(x)
            y = dd[m.measure_id]
            res = sm.OLS(y, X).fit()

            v.coeff = res.params[1]
            v.pvalue = res.pvalues[1]

            vm.save(v)

    def run(self):
        for instrument in self.phdb.instruments.values():
            # instrument = self.phdb.instruments['ssc_commonly_used']
            for m in instrument.measures.values():
                if m.stats == 'continuous':
                    print("handling measure: {}".format(m.measure_id))
                    df = self.load_measure(m)

                    with MetaVariableManager() as vm:
                        v = MetaVariableModel()
                        v.variable_id = m.measure_id
                        v.min_value = df[m.measure_id].min()
                        v.max_value = df[m.measure_id].max()
                        v.has_probands = (len(df[df.role == 'prb']) > 7)
                        v.has_siblings = (len(df[df.role == 'sib']) > 7)
                        v.has_parents = (len(df[df.role == 'parent']) > 7)

                        vm.save(v)

                    if len(df[df.role == 'prb']) == 0:
                        print("NO PROBANDS: skipping regressions...")
                        continue

                    self._build_regression(
                        df, m, 'pheno_common.non_verbal_iq', 'prb', 'M')
                    self._build_regression(
                        df, m, 'pheno_common.non_verbal_iq', 'prb', 'F')
                    self._build_regression(
                        df, m, 'pheno_common.age', 'prb', 'M')
                    self._build_regression(
                        df, m, 'pheno_common.age', 'prb', 'F')

    def prepare(self):
        self.drop_tables()
        self.create_tables()
        self.run()


if __name__ == '__main__':
    prepare = PrepareMetaProbands()
    prepare.prepare()

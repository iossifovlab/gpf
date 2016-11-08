'''
Created on Oct 18, 2016

@author: lubo
'''
from pheno.utils.load_raw import V15Loader
from pheno.models import MetaVariableManager


class PrepareDefaultFilters(V15Loader):
    DEFAULT_FILTERS_CSV = 'default_filters.csv'

    def __init__(self, *args, **kwargs):
        super(PrepareDefaultFilters, self).__init__(*args, **kwargs)

    def load_default_filters(self):
        df = self._load_df(self.DEFAULT_FILTERS_CSV)
        return df

    def prepare(self):
        df = self.load_default_filters()
        with MetaVariableManager(config=self.config) as vm:
            for _index, row in df.iterrows():
                mv = vm.get(
                    where="variable_id = '{}'".format(
                        row['measure_id']))
                mv.default_filter = row['default_filter']
                vm.save(mv)


if __name__ == '__main__':
    prepare = PrepareDefaultFilters()
    prepare.prepare()

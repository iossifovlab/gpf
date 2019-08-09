import pandas as pd


class GenomicValues(object):

    def __init__(self, name, *args, **kwargs):
        super(GenomicValues, self).__init__(*args, **kwargs)
        self.name = name

        self.df = None
        self._dict = None

    def _load_data(self):
        assert self.filename is not None

        df = pd.read_csv(self.filename)
        assert self.name in df.columns, \
            "{} not found in {}".format(self.name, df.columns)

        self.df = df[[self.genomic_values_col, self.name]].copy()

        return self.df

    def values(self):
        return self.df[self.name].values

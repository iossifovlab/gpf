import pandas as pd


class GenomicValues(object):

    def __init__(self, value_id):
        super(GenomicValues, self).__init__()
        self.id = value_id

        self.df = None
        self._dict = None

    def _load_data(self):
        assert self.filename is not None

        df = pd.read_csv(self.filename)
        assert self.id in df.columns, \
            "{} not found in {}".format(self.id, df.columns)

        self.df = df[[self.genomic_values_col, self.id]].copy()

        return self.df

    def values(self):
        return self.df[self.id].values

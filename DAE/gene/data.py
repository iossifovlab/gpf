import pandas as pd


class Data(object):

    def __init__(self, *args, **kwargs):
        super(Data, self).__init__(*args, **kwargs)
        self.name = self.section_name.split('.')[-1]

        self.df = None
        self._dict = None
        self._load_data()

    def _load_data(self):
        assert self.filename is not None

        df = pd.read_csv(self.filename)
        assert self.name in df.columns

        self.df = df[[self.data_col, self.name]].copy()
        self.df.dropna(inplace=True)

        return self.df

    def values(self):
        return self.df[self.name].values

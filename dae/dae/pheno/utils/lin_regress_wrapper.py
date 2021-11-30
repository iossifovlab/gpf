import numpy as np
from scipy.stats import linregress


class LinearRegressionWrapper:
    def __init__(self, x, y):
        self.x_values = x
        self.y_values = y
        self._results = linregress(x, y)

    @property
    def slope(self):
        return self._results.slope

    @property
    def intercept(self):
        return self._results.intercept

    @property
    def rvalue(self):
        return self._results.rvalue

    @property
    def pvalue(self):
        return self._results.pvalue

    @property
    def stderr(self):
        return self._results.stderr

    @property
    def intercept_stderr(self):
        return self._results.stderr

    def _predict_value(self, x):
        return x * self.slope + self.intercept

    def predict(self):
        return np.array([
            self._predict_value(x) for x in self.x_values
        ])

    def resid(self):
        values = zip(self.x_values, self.y_values)
        return np.array([
            y - self._predict_value(x) for x, y in values
        ])

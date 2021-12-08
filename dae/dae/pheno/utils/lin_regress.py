import numpy as np
import scipy as sp
from sklearn.linear_model import LinearRegression as LinearRegressionSK
from scipy.stats import t


class LinearRegression(LinearRegressionSK):
    def __init__(self, *args, **kwargs):

        super(LinearRegression, self).__init__(*args, **kwargs)

        self._pvalues = None
        self._tvalues = None

    def fit(self, X, y, sample_weight=None):
        super().fit(X, y, sample_weight)
        n = len(y)

        pinv_x, rank = sp.linalg.pinv(X, return_rank=True)

        df_resid = X.shape[0] - np.linalg.matrix_rank(X)

        resid = y - self.predict(X)

        scale = np.dot(resid, resid) / df_resid

        cov_params = np.dot(pinv_x, pinv_x.T) * scale

        beta = np.dot(pinv_x, y)
        bse = np.sqrt(np.diag(cov_params))

        tvalues = beta / bse

        pvalues = t.sf(np.abs(tvalues), n-rank) * 2

        self._tvalues = tvalues
        self._pvalues = pvalues
        return self

    @property
    def tvalues(self):
        return self._tvalues

    @property
    def pvalues(self):
        return self._pvalues

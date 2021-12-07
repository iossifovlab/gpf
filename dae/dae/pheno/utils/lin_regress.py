import numpy as np
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

        x_consts = np.column_stack([np.ones(X.shape[0]), X])

        pinv_x, singular_vals = self._pinv_extended(x_consts)

        df_resid = x_consts.shape[0] - np.linalg.matrix_rank(x_consts)

        resid = y - self.predict(X)

        scale = np.dot(resid, resid) / df_resid

        cov_params = np.dot(pinv_x, pinv_x.T) * scale

        beta = np.dot(pinv_x, y)
        bse = np.sqrt(np.diag(cov_params))

        tvalues = beta / bse

        rank = np.linalg.matrix_rank(np.diag(singular_vals))

        pvalues = t.sf(np.abs(tvalues), n-rank) * 2

        self._tvalues = tvalues
        self._pvalues = pvalues
        return self

    def _pinv_extended(self, x, rcond=1e-15):
        """
        Return the pinv of an array X as well as the singular values
        used in computation.

        Code adapted from numpy.
        """
        x = np.asarray(x)
        x = x.conjugate()
        u, s, vt = np.linalg.svd(x, False)
        s_orig = np.copy(s)
        m = u.shape[0]
        n = vt.shape[1]
        cutoff = rcond * np.maximum.reduce(s)
        for i in range(min(n, m)):
            if s[i] > cutoff:
                s[i] = 1./s[i]
            else:
                s[i] = 0.
        res = np.dot(np.transpose(vt), np.multiply(s[:, np.core.newaxis], u.T))
        return res, s_orig

    @property
    def tvalues(self):
        return self._tvalues

    @property
    def pvalues(self):
        return self._pvalues

import numpy as np
from sklearn.linear_model import LinearRegression as LinearRegressionSK
from scipy.stats import t


class LinearRegression(LinearRegressionSK):
    def __init__(self, *args, **kwargs):

        super(LinearRegression, self).__init__(*args, **kwargs)

        self._pvalues = None
        self._tvalues = None

    def fit(self, X, y, sample_weight=None):
        self = super().fit(X, y, sample_weight)
        beta_hat = [self.intercept_] + self.coef_.tolist()
        n = len(X)

        # compute the p-values
        # add ones column
        X1 = np.column_stack((np.ones(n), X))
        # standard deviation of the noise.
        sigma_hat = np.sqrt(
            np.sum(np.square(y - X1@beta_hat)) / (n - X1.shape[1])
        )
        # estimate the covariance matrix for beta
        beta_cov = np.linalg.inv(X1.T@X1)
        # the t-test statistic for each variable
        tvalues = beta_hat / (sigma_hat * np.sqrt(np.diagonal(beta_cov)))
        # compute 2-sided p-values.
        pvalues = t.sf(np.abs(tvalues), n-X1.shape[1])*2

        self._tvalues = tvalues
        self._pvalues = pvalues
        return self

    @property
    def tvalues(self):
        return self._tvalues

    @property
    def pvalues(self):
        return self._pvalues

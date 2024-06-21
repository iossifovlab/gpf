from __future__ import annotations

from typing import Any, Optional, Union

import numpy as np
import pandas as pd
import scipy as sp
from scipy.stats import t
from sklearn.linear_model import LinearRegression as LinearRegressionSK


class LinearRegression(LinearRegressionSK):
    """Class to build linear regression models."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self._pvalues: Optional[np.ndarray] = None
        self._tvalues: Optional[np.ndarray] = None

    def fit(
        self, X: np.ndarray, y: Union[pd.Series, np.ndarray],
        sample_weight: Optional[float] = None,
    ) -> LinearRegression:
        super().fit(X, y, sample_weight)
        n = len(y)  # pylint: disable=invalid-name

        x_consts = np.column_stack([np.ones(X.shape[0]), X])
        pinv_x, rank = sp.linalg.pinv(x_consts, return_rank=True)

        df_resid = x_consts.shape[0] - np.linalg.matrix_rank(x_consts)

        resid = y - self.predict(X)

        scale = np.dot(resid, resid) / df_resid

        cov_params = np.dot(pinv_x, pinv_x.T) * scale

        beta = np.dot(pinv_x, y)
        bse = np.sqrt(np.diag(cov_params))

        tvalues = beta / bse

        pvalues = t.sf(np.abs(tvalues), n - rank) * 2

        self._tvalues = tvalues
        self._pvalues = pvalues

        return self

    @property
    def tvalues(self) -> Optional[np.ndarray]:
        return self._tvalues

    @property
    def pvalues(self) -> Optional[np.ndarray]:
        return self._pvalues

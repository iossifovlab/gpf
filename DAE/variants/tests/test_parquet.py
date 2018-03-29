'''
Created on Mar 7, 2018

@author: lubo
'''
# import pandas as pd
# import pyarrow as pa
#
#
# def test_parquet_experiment():
#     df = pd.DataFrame(['a', 'b'])
#     print(df.head())
#
#     s = pd.Series(index=df.index)
#     s[0] = ','.join(['t1', 't2'])
#     s[1] = ','.join(['s1', 's2'])
#
#     df['ar'] = s
#
#     print(df.head())
#
#     pt = pa.Table.from_pandas(df)  # @UndefinedVariable
#     assert pt is not None

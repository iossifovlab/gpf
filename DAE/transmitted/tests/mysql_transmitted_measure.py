'''
Created on Oct 15, 2015

@author: lubo
'''
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from past.utils import old_div
import timeit
from .mysql_transmitted_std_queries import *  # @UnusedWildImport


def measure_function(fun, count):
    t = timeit.Timer("{}()".format(fun),
                     setup="from __main__ import {}".format(fun))
    meas = t.timeit(count)
    return {'fun': fun,
            'count': count,
            'time': old_div(meas, count)}


def measure_print(m):
    print("{}: {} time average: {}s".format(m['fun'], m['count'], m['time']))


def measure_all(to_measure, count=3):

    results = []
    for task in to_measure:
        res = measure_function(task['fun'], count)
        results.append(res)

    for m in results:
        measure_print(m)


if __name__ == "__main__":
    #     dae_to_measure = [
    #         {'fun': 'dae_query_q101'},
    #         {'fun': 'dae_query_q201'},
    #         {'fun': 'dae_query_q301'},
    #         {'fun': 'dae_query_q401'},
    #         {'fun': 'dae_query_q501'},
    #         {'fun': 'dae_query_q601'},
    #         {'fun': 'dae_query_q701'},
    #         {'fun': 'dae_query_q801'},
    #     ]
    #     measure_all(dae_to_measure)

    mysql_to_measure = [
        {'fun': 'mysql_query_q101'},
        {'fun': 'mysql_query_q201'},
        {'fun': 'mysql_query_q301'},
        {'fun': 'mysql_query_q401'},
        {'fun': 'mysql_query_q501'},
        {'fun': 'mysql_query_q601'},
        {'fun': 'mysql_query_q701'},
        {'fun': 'mysql_query_q801'},
    ]
    measure_all(mysql_to_measure)

    mysql_limit_to_measure = [
        {'fun': 'mysql_query_q101_limit'},
        {'fun': 'mysql_query_q201_limit'},
        {'fun': 'mysql_query_q301_limit'},
        {'fun': 'mysql_query_q401_limit'},
        {'fun': 'mysql_query_q501_limit'},
        {'fun': 'mysql_query_q601_limit'},
        {'fun': 'mysql_query_q701_limit'},
        {'fun': 'mysql_query_q801_limit'},
    ]
    measure_all(mysql_limit_to_measure)

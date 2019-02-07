'''
Created on Nov 6, 2015

@author: lubo

'''
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import next
from builtins import zip
from past.utils import old_div
from builtins import object
import requests
import io
import csv
import copy
from multiprocessing.pool import ThreadPool


def run_request(url, params):
    req = requests.post(url, params, verify=False)

    fin = Stringio.StringIO(req.text)
    csvin = csv.reader(fin)
    header = next(csvin)

    return (req.status_code, header, csvin)


def csv_column_check_equal(header, columname, expected_value):
    index = header.index(columname)
    if index == -1:
        return None
    return lambda line: (line[0].startswith("#") or
                         line[index] == expected_value)


def assert_csv_colum_value(header, res, columnname, expected_value):
    check = csv_column_check_equal(header, columnname, expected_value)
    count = 0
    for line in res:
        count += 1
        assert check(line)
    return count


class TestRequest(object):

    def __init__(self, url, params, expected_len):
        self.url = url
        self.params = params
        self.expected_len = expected_len
        self.result = None
        self.header = None

    def _request(self):
        res = requests.post(self.url, self.params, verify=False)
        assert 200 == res.status_code

        fin = Stringio.StringIO(res.text)
        csvin = csv.reader(fin)
        self.header = next(csvin)
        result = []
        for line in csvin:
            result.append(line)
        return result

    def initial_request(self):
        self.result = self._request()
        print("assert {} == {}".format(self.expected_len, len(self.result)))
        assert self.expected_len == len(self.result)
        return self.result

    def test_request(self):
        result = self._request()
        lines = [x_y[0] == x_y[1] for x_y in zip(self.result, result)]
        return all(lines)


class AsyncSSCTest(object):
    params = {
        "denovoStudies": "ALL SSC",
        "effectTypes": "Frame-shift,Intergenic,Intron,Missense,"
        "Non coding,No-frame-shift,Nonsense,Splice-site,"
        "Synonymous,noEnd,noStart,3'UTR,5'UTR,CNV+,CNV-,3'-UTR,5'-UTR",
        "families": "familyIds",
        "familyIds": "11110",
        "gender": "female,male",
        "genes": "All",
        "presentInChild": "autism and unaffected,"
        "autism only,neither,unaffected only",
        "presentInParent": "father only,mother and father,mother only,neither",
        "rarity": "all",
        "variantTypes": "CNV,del,ins,sub",
    }

    def __init__(self, base_url, families):
        self.url = base_url + "/api/ssc_query_variants"
        self.reqs = []
        for family_id, expected_len in families:
            params = copy.deepcopy(self.params)
            params["familyIds"] = family_id
            req = TestRequest(self.url, params, expected_len)
            self.reqs.append(req)

    def initial_requests(self):
        for req in self.reqs:
            req.initial_request()

    def async_requests(self, count=10, pool_size=2):
        repeat = old_div(count, len(self.reqs)) + 1
        reqs = (self.reqs * repeat)[:count]

        pool = ThreadPool(processes=pool_size)
        result = pool.map((lambda req: req.test_request()), reqs)
        assert all(result)


def main():
    families = [("11110", 32677),
                ("13398", 32575),
                ("12854", 35221)]

    # families = [("11110", 32677), ]

    ssc_test = AsyncSSCTest("http://localhost:8000",
                            families)
    ssc_test.initial_requests()

    ssc_test.async_requests(count=50, pool_size=5)


if __name__ == "__main__":

    main()

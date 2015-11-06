'''
Created on Nov 6, 2015

@author: lubo

'''
import requests
import StringIO
import csv


def run_request(url, params):
    req = requests.post(url, params, verify=False)

    fin = StringIO.StringIO(req.text)
    csvin = csv.reader(fin)
    header = csvin.next()

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
        self.url = url,
        self.params = params
        self.expected_len = expected_len
        self.result = None
        self.header = None

    def _request(self):
        res = requests.post(url, params, verify=False)
        assert 200 == res.status_code

        fin = StringIO.StringIO(res.text)
        csvin = csv.reader(fin)
        self.header = csvin.next()
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
        assert self.result is not None
        result = self._request()
        assert self.result == result


if __name__ == "__main__":
    params = {
        "denovoStudies": "ALL SSC",
        "effectTypes": "Frame-shift,Intergenic,Intron,Missense,"
        "Non coding,Non-frame-shift,Nonsense,Splice-site,"
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
    url = "https://seqpipe.setelis.com/dae/api/ssc_query_variants"

    req1 = TestRequest(url, params, 32677)
    req1.initial_request()
    req1.test_request()

    params = {
        "denovoStudies": "ALL SSC",
        "effectTypes": "Frame-shift,Intergenic,Intron,Missense,"
        "Non coding,Non-frame-shift,Nonsense,Splice-site,"
        "Synonymous,noEnd,noStart,3'UTR,5'UTR,CNV+,CNV-,3'-UTR,5'-UTR",
        "families": "familyIds",
        "familyIds": "13398",
        "gender": "female,male",
        "genes": "All",
        "presentInChild": "autism and unaffected,"
        "autism only,neither,unaffected only",
        "presentInParent": "father only,mother and father,mother only,neither",
        "rarity": "all",
        "variantTypes": "CNV,del,ins,sub",
    }
    url = "https://seqpipe.setelis.com/dae/api/ssc_query_variants"

    req2 = TestRequest(url, params, 32575)
    req2.initial_request()
    req2.test_request()

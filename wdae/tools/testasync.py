import urllib2
import json

from threading import Thread


class AsyncTest:

        def __init__(self, url=None, user=None, passwd=None,
                     realm=None):
                self.url = url
                self.user = user
                self.passwd = passwd
                self.realm = realm
                self.queries = []
                self.responses = []
                self.__install_basic_auth_handler()

        def add_query(self, query):
                self.queries.append(query)

        def __install_basic_auth_handler(self):
                if self.passwd is None or self.user is None or \
                   self.realm is None:
                        return

                auth_handler = urllib2.HTTPBasicAuthHandler()
                auth_handler.add_password(uri=self.url,
                                          user=self.user,
                                          passwd=self.passwd,
                                          realm=self.realm)

                opener = urllib2.build_opener(auth_handler)
                urllib2.install_opener(opener)

        def initial_requests(self):
                for q in self.queries:
                        self.responses.append(self.__send_request(q))

        def __send_request(self, query):
                req = urllib2.Request(self.url)
                req.add_header('Content-Type', 'application/json')
                rsp = urllib2.urlopen(req, json.dumps(query))
                content = rsp.read()
                return content

        def __compare_results(self, query, pattern, index):
                res = self.__send_request(query)
                if res != pattern:
                        print "error!!!"
                        print res, pattern
                else:
                        print '.%d' % index,

        def __execute_async_task(self, count, query, pattern, index):
                for i in range(count):
                        self.__compare_results(query, pattern, index)

        def start_async_tasks(self, count):
                for (q, p, i) in zip(self.queries, self.responses, range(len(self.queries))):
                        t = Thread(target=AsyncTest.__execute_async_task,
                                   args=(self, count, q, p, i))
                        t.start()


if __name__ == '__main__':
        #
        # tst = AsyncTest(url='http://localhost:8000/api/query_variants')

        tst = AsyncTest(url='http://seqpipe.setelis.com/dae/api/query_variants',
                        realm='seqpipe',
                        user='lubo',
                        passwd='anilubo64')

        # # Lubo: not working... returns '500 internal server error'
        # # apache error log should be checked...
        # tst = AsyncTest(url='http://wigserv2.cshl.edu/dae/api/query_variants',
        #                 realm='Please Log In',
        #                 user='world',
        #                 passwd='autismpass')

        tst.add_query({'denovoStudies': ["DalyWE2012"],
                       'transmittedStudies': ["none"],
                       'inChild': "prbF",
                       'effectTypes': "LGDs",
                       'variantTypes': "All",
                       'rarity': "ultraRare",
                       'genes': 'All'})

        tst.add_query({'denovoStudies': ["DalyWE2012"],
                       'transmittedStudies': ["none"],
                       'inChild': "prbM",
                       'effectTypes': "missense",
                       'variantTypes': "All",
                       'rarity': "ultraRare",
                       'genes': 'All'})

        tst.initial_requests()

        tst.start_async_tasks(1000)

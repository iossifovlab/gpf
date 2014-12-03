import unittest
import pprint
from functional_helpers import *


class VariantsBase(unittest.TestCase):

    def set_context(self, url, browser, data_dir, download_dir, results_dir,
                    index, request, *args, **kwargs):
        
        self.url = url
        self.browser = browser
        self.data_dir = data_dir
        self.download_dir = download_dir
        self.index = index
        self.request = request
        self.results_dir = results_dir
        
    def setUp(self):
        self.assertTrue(assert_request_content(self.data_dir,
                                               self.index,
                                               self.request))
        
        self.browser.get(self.url)
        fill_variants_form(self.browser, self.request)

    def runTest(self):
        raise NotImplementedError

    def __repr__(self):
        return "%s;\ndata dir: %s;\nresults_dir: %s;\nrequest: %s" % \
            (str(self),
             self.data_dir,
             self.results_dir,
             self.request)

    def __str__(self):
        return "%50s: %03d" % \
            (self.__class__.__name__,
             self.index)


class VariantsPreviewTest(VariantsBase):

    def runTest(self):
        preview = click_the_preview_button(self.browser)
        save_preview_content(self.results_dir,
                             self.index,
                             preview, "test")
        self.assertTrue(assert_preview_content(self.data_dir,
                                               self.index,
                                               preview),
                        repr(self))
        
class VariantsChromesTest(VariantsBase):

    def runTest(self):
        chroms = click_the_chroms_button(self.browser)
        save_chroms_content(self.results_dir,
                            self.index,
                            chroms, "test")
        
        self.assertTrue(assert_chroms_content(self.data_dir,
                                              self.index,
                                              chroms),
                        repr(self))

class VariantsDownloadTest(VariantsBase):
    def runTest(self):
        down = click_the_download_button(self.browser,
                                         self.download_dir)
        down_result = save_download_content(self.results_dir,
                                            self.index,
                                            down,
                                            "test")
        self.assertTrue(assert_download_content(self.data_dir,
                                                self.index,
                                                down_result),
                        repr(self))
        

class SeqpipeTestResult(unittest.TestResult):
	
    def __init__(self, *args, **kwargs):
        super(SeqpipeTestResult, self).__init__(args, kwargs)
        self.successes = []
            	
    def addSuccess(self, test):
    	super(SeqpipeTestResult, self).addSuccess(test)
    	self.successes.append((test, "OK"))
    	
def test_report(result):
    for (test, msg) in result.failures:
        print("-----------------------------------------------------------------------")
        print("FAILURE: %s" % repr(test))
        # print(msg)
        
    for (test, msg) in result.errors:
        print("-----------------------------------------------------------------------")
        print("ERROR: %s" % repr(test))
        # print(msg)

    print("-----------------------------------------------------------------------")
    for (test, msg) in result.successes:
        print("PASS:\t %s" % str(test))

def build_variants_test_suite(url, variants_requests, data_dir, results_dir, **context):
    data = load_dictionary(variants_requests)
    (browser, download_dir) = start_browser()

    context = {'data_dir': data_dir,
               'download_dir': download_dir,
               'browser': browser,
               'url': url,
               'results_dir': data_dir}

    suite = unittest.TestSuite()
    for (index, request) in enumerate(data):
        context['index']=index
        context['request']=request
        
        test_case = VariantsPreviewTest()
        test_case.set_context(**context)
        suite.addTest(test_case)

        test_case = VariantsChromesTest()
        test_case.set_context(**context)
        suite.addTest(test_case)

        test_case = VariantsDownloadTest()
        test_case.set_context(**context)
        suite.addTest(test_case)
        
    return (context, suite)

def cleanup_variants_test(**context):
    stop_browser(context['browser'])
    shutil.rmtree(context['download_dir'])
    

if __name__ == "__main__":
    variants_context = {'variants_requests': "variants_tests/variants_requests.txt",
                        'data_dir': "variants_tests/",
                        'results_dir': "variants_tests/",
                        'url': "http://seqpipe-vm.setelis.com/dae",
                    }
    context, suite = build_variants_test_suite(**variants_context)
    
    runner = unittest.TextTestRunner(resultclass = SeqpipeTestResult)
    result = runner.run(suite)

    cleanup_variants_test(**context)
    
    test_report(result)
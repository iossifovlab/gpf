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
        
    def runTest(self):
        self.assertTrue(self.compare_requests(),
                        "requests does not match;\n%s" % repr(self))        
        content = self.implementation()
        self._save_content(content, self._result_filename())
        self.assertTrue(self.compare_content(content),
                        repr(self))

    def name(self):
        raise NotImplementedError

    def implementation(self):
        raise NotImplementedError

    def compare_requests(self):
        fullname = self._request_filename()
        with open(fullname, "r") as f:
            orig = f.read()
        return str(self.request) == orig

    def compare_content(self, content):
        fullname = self._output_filename()
        with open(fullname, "r") as f:
            orig = f.read()
        return content == orig

    def _output_filename(self):
        return os.path.join(self.data_dir,
                            "%03d_%s.out" % (self.index, self.name()))

    def _result_filename(self):
        return os.path.join(self.results_dir,
                            "%03d_%s.test" % (self.index, self.name()))

    def _request_filename(self):
        return os.path.join(self.data_dir,
                            "%03d_%s_request.out" % (self.index, self.name()))

    def _save_request(self):
        self._save_content(str(self.request),
                           self._request_filename())
        
    def _save_content(self, content, filename):
        with open(filename, "w") as f:
            f.write(content)
            
    def save_test(self):
        self._save_request()
        content = self.implementation()
        self._save_content(content, self._output_filename())

        
    def __repr__(self):
        return "%s;\ndata:    %s;\nresults: %s;\nrequest: %s" % \
            (str(self),
             self._output_filename(),
             self._result_filename(),
             self._request_filename())

    def __str__(self):
        return "%50s: %03d" % \
            (self.__class__.__name__,
             self.index)


class VariantsPreviewTest(VariantsBase):

    def name(self):
        return "variants_preview_test"
        
    def implementation(self):
        self.browser.get(self.url)
        fill_variants_form(self.browser, self.request)
        return click_the_preview_button(self.browser)
        
class VariantsChromesTest(VariantsBase):

    def name(self):
        return "variants_chromes_test"

    def implementation(self):
        self.browser.get(self.url)
        fill_variants_form(self.browser, self.request)
        return click_the_chroms_button(self.browser)

class VariantsDownloadTest(VariantsBase):
    def name(self):
        return "variants_download_test"

    def implementation(self):
        self.browser.get(self.url)
        fill_variants_form(self.browser, self.request)
        down_filename = click_the_download_button(self.browser,
                                                  self.download_dir)
        with open(down_filename, 'r') as f:
            content = f.read()
        os.remove(down_filename)
        
        return content


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
               'results_dir': results_dir}

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
    

def save_test_suite(suite):
    for test in suite:
        test.save_test()

def run_test_suite(suite):
    for test in suite:
        test.runTest()
    
if __name__ == "__main__":
    variants_context = {'variants_requests': "variants_tests/variants_requests.txt",
                        'data_dir': "variants_tests/",
                        'results_dir': "tmp/",
                        'url': "http://seqpipe-vm.setelis.com/dae",
                    }
    context, suite = build_variants_test_suite(**variants_context)
    

    save_test_suite(suite)
    # run_test_suite(suite)
    runner = unittest.TextTestRunner(resultclass = SeqpipeTestResult)
    result = runner.run(suite)
    test_report(result)
    
    cleanup_variants_test(**context)
    

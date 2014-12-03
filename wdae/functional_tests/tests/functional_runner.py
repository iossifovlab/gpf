import unittest
import pprint
from functional_helpers import *


class VariantsBase(unittest.TestCase):

    def set_context(self, url, browser, data_dir, download_dir, index, request, *args, **kwargs):
        self.url = url
        self.browser = browser
        self.data_dir = data_dir
        self.download_dir = download_dir
        self.index = index
        self.request = request
        
    def setUp(self):
        self.browser.get(self.url)
        fill_variants_form(self.browser, self.request)

    def runTest(self):
        raise NotImplementedError


class VariantsPreviewTest(VariantsBase):

    def runTest(self):
        preview = click_the_preview_button(self.browser)
        save_preview_content(self.data_dir,
                             self.index,
                             preview, "test")
        self.assertTrue(assert_preview_content(self.data_dir,
                                               self.index,
                                               preview))
class VariantsChromesTest(VariantsBase):

    def runTest(self):
        chroms = click_the_chroms_button(self.browser)
        save_chroms_content(self.data_dir,
                            self.index,
                            chroms, "test")
        
        self.assertTrue(assert_chroms_content(self.data_dir,
                                              self.index,
                                              chroms))

class VariantsDownloadTest(VariantsBase):
    def runTest(self):
        down = click_the_download_button(self.browser,
                                         self.download_dir)
        down_in_rdir = save_download_content(rdir, idx, down, "test")
        self.assertTrue(assert_download_content(rdir, idx, down_in_rdir))
        

class SeqpipeTestResult(unittest.TestResult):
	
    def __init__(self, *args, **kwargs):
        super(SeqpipeTestResult, self).__init__(args, kwargs)
        self.successes = []
            	
    def addSuccess(self, test):
    	super(SeqpipeTestResult, self).addSuccess(test)
    	self.successes.append((test, "OK"))
    	
                        
if __name__ == "__main__":
    data = load_dictionary("variants_tests/variants_requests.txt")
    # data = load_dictionary("data_dict_variants.txt")
    data_dir = "variants_tests/"
    # data_dir = "results_dir/"
    url = "http://seqpipe-vm.setelis.com/dae"
    
    (browser, download_dir) = start_browser()

    suite = unittest.TestSuite()
    for (index, request) in enumerate(data):
        test_case = VariantsPreviewTest()
        test_case.set_context(url, browser, data_dir, download_dir, index, request)
        suite.addTest(test_case)
        print "instance of : ", test_case.__class__.__name__

        test_case = VariantsChromesTest()
        test_case.set_context(url, browser, data_dir, download_dir, index, request)
        suite.addTest(test_case)

    print("staring test suite...")
    
    runner = unittest.TextTestRunner(resultclass = SeqpipeTestResult)
    result = runner.run(suite)
    print "number of tests represented by this test object : ", suite.countTestCases()

    stop_browser(browser)
    print(result.errors)
    print(result.failures)

    print(result.successes)
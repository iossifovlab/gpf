import unittest
import pprint
from functional_helpers import *



class VariantsBase(unittest.TestCase):

    def set_context(self, url, browser, data_dir, index, request, *args, **kwargs):
        self.url = url
        self.browser = browser
        self.data_dir = data_dir
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
        
class MyTestResult(unittest.TestResult):
	
    def __init__(self):
    	self.shouldStop = False
    	self.buffer = False
    	self.testsRun = 0
        self.failures = []
        self.errors = []
        self.success = []
        self._mirrorOutput = False
        
        self.tests_run = []
        
    def getTestsReport(self):
    	return self.tests_run
	
    def addError(self, test, err):
    	super(MyTestResult, self).addError(test, err)
    	err_desc = self._exc_info_to_string(err, test)
    	#print "Error Description : ", err_desc
    	#print "Test Description : "
    	#pprint.pprint(test.request)
    	#print "Test index --> ", test.index
    	self.errors.append((test.__class__.__name__, test.index, test.request, self._exc_info_to_string(err, test)))
    	self._mirrorOutput = True
    	self.tests_run.append([test.__class__.__name__, test.request,self.testsRun, self._exc_info_to_string(err, test)])
    	
    def addFailure(self, test, err):
    	super(MyTestResult, self).addFailure(test, err)
    	err_desc = self._exc_info_to_string(err, test)
    	#print "Error Description : ", err_desc
    	#print "Test Description : "
    	#pprint.pprint(test.request)
    	#print "Test index --> ", test.index
    	#print "Short Description : ", test.shortDescription()
    	#print "Test id : ", test.id()
    	self.failures.append((test.__class__.__name__, test.index, test.request, self._exc_info_to_string(err, test)))
    	self._mirrorOutput = True
    	self.tests_run.append([test.__class__.__name__, self.testsRun, test.request, self._exc_info_to_string(err, test)])
    	
    def addSuccess(self, test):
    	super(MyTestResult, self).addSuccess(test)
    	print "tests run : ", self.testsRun
    	#print "Success"
    	#print "Test Description : "
    	#pprint.pprint(test.request)
    	#print "Test index --> ", test.index
    	self.success.append((test.__class__.__name__, test.index, test.request, "OK"))
    	self._mirrorOutput = True
    	self.tests_run.append([test.__class__.__name__, test.request,self.testsRun, "OK"])
    	
                        
if __name__ == "__main__":
    #data = load_dictionary("variants_tests/variants_requests.txt")
    data = load_dictionary("data_dict_variants.txt")
    #data_dir = "variants_tests/"
    data_dir = "results_dir/"
    url = "http://seqpipe-vm.setelis.com/dae"
    
    (browser, download_dir) = start_browser()

    suite = unittest.TestSuite()
    for (index, request) in enumerate(data):
        test_case = VariantsPreviewTest()
        test_case.set_context(url, browser, data_dir, index, request)
        suite.addTest(test_case)
        print "instance of : ", test_case.__class__.__name__

        test_case = VariantsChromesTest()
        test_case.set_context(url, browser, data_dir, index, request)
        suite.addTest(test_case)

    print("staring test suite...")
    
    runner = unittest.TextTestRunner()
    #testRes = unittest.TestResult()
    #result = runner.run(suite)
    results = MyTestResult() 
    print "number of tests represented by this test object : ", suite.countTestCases()
    suite.run(results)
    #print "The total number of tests run so far", testRes.testsRun
    #print "A list containing 2-tuples of TestCase instances and strings holding formatted tracebacks : " , testRes.errors
    #print "A list containing 2-tuples of TestCase instances and strings holding formatted tracebacks : " , testRes.failures
    stop_browser(browser)
    pprint.pprint(results.getTestsReport())

    #print "End Results : " , testRes
    #results.printErrors()
    
import unittest

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
                        
if __name__ == "__main__":
    data = load_dictionary("variants_tests/variants_requests.txt")
    data_dir = "variants_tests/"
    url = "http://seqpipe-vm.setelis.com/dae"
    
    (browser, download_dir) = start_browser()

    suite = unittest.TestSuite()
    for (index, request) in enumerate(data):
        test_case = VariantsPreviewTest()
        test_case.set_context(url, browser, data_dir, index, request)
        
        suite.addTest(test_case)
                        
        test_case = VariantsChromesTest()
        test_case.set_context(url, browser, data_dir, index, request)
        suite.addTest(test_case)

    print("staring test suite...")

    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    stop_browser(browser)

    print result
    result.printErrors()
    
import unittest
import filecmp
import pprint
import os
from operator import itemgetter
from functional_helpers import *
from django.template import Template, Context, loader
from django.conf import settings

template_path = os.path.realpath(os.path.dirname(__file__))
settings.configure(TEMPLATE_DIRS=(template_path+"/django_templates",))

class FunctionalBase(unittest.TestCase):

    def set_context(self, url, browser, data_dir, tmp_dir, results_dir,
                    index, request, **kwargs):
        
        self.url = url
        self.browser = browser
        self.data_dir = data_dir
        self.tmp_dir = tmp_dir
        self.index = index
        self.request = request
        self.results_dir = results_dir
        
    def runTest(self):
        self.assertTrue(self.compare_requests(),
                        "requests does not match;\n%s" % repr(self))        
        datafile = self.implementation()
        
        shutil.move(datafile, self._result_filename())
        self.assertTrue(self.compare_content(),
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

    def compare_content(self):
        return filecmp.cmp(self._result_filename(), self._output_filename())

    def _output_filename(self):
        return os.path.join(self.data_dir,
                            "%03d_%s.out" % (self.index, self.name()))

    def _result_filename(self):
        return os.path.join(self.results_dir,
                            "%03d_%s.test" % (self.index, self.name()))

    def _request_filename(self):
        return os.path.join(self.data_dir,
                            "%03d_%s_request.out" % (self.index, self.name()))

    def _tmp_filename(self):
        return os.path.join(self.tmp_dir,
                            "%03d_%s.tmp" % (self.index, self.name()))
    def _save_request(self):
        self._save_content(str(self.request),
                           self._request_filename())
        
    def _save_content(self, content, filename):
        with open(filename, "w") as f:
            f.write(content)
        return filename

    def save_data(self, content):
        return self._save_content(content,
                                  self._tmp_filename())
        
    def save_test(self):
        self._save_request()
        datafile = self.implementation()
        shutil.move(datafile, self._output_filename())
        
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


class VariantsPreviewTest(FunctionalBase):

    def name(self):
        return "variants_preview_test"
       
    def link(self):
    	return link
       
    def implementation(self):
        self.browser.get(self.url)
        fill_variants_form(self.browser, self.request)
        content = click_the_preview_button(self.browser)
        setattr(self, "link", self.browser.current_url)
        return self.save_data(content)
        
class VariantsChromesTest(FunctionalBase):

    def name(self):
        return "variants_chromes_test"

    def implementation(self):
        self.browser.get(self.url)
        fill_variants_form(self.browser, self.request)
        content = click_the_chroms_button(self.browser)
        setattr(self, "link", self.browser.current_url)
        return self.save_data(content)

class VariantsDownloadTest(FunctionalBase):
    def name(self):
        return "variants_download_test"

    def implementation(self):
        self.browser.get(self.url)
        fill_variants_form(self.browser, self.request)
        setattr(self, "link", self.browser.current_url)
        return click_the_download_button(self.browser,
                                         self.tmp_dir)

class EnrichmentTest(FunctionalBase):
	
    def name(self):
        return "enrichment_test"

    def implementation(self):
    	self.browser.get(self.url)
    	#wait_button_to_be_clickable(self.browser)
        click_enrichment_link(self.browser)
    	fill_enrichment_form(self.browser, self.request)
    	content = click_the_enrichment_button(self.browser)
    	setattr(self, "link", self.browser.current_url)
        return self.save_data(content)
     
def set_attribute(obj, attr_name, attr_value):
    setattr(obj, attr_name, attr_value)

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
        
    for (test, msg) in result.errors:
        print("-----------------------------------------------------------------------")
        print("ERROR: %s" % repr(test))

    print("-----------------------------------------------------------------------")
    for (test, msg) in result.successes:
        print("PASS:\t %s" % str(test))

def result_to_dict(result):
    
    result_dict = {"varTest" : [],
                   "enrTest" : []}
    for i in range(0, len(result.failures)):
        result_dict[result.failures[i][0].name()[:3]  + "Test"].append({
    		            'index': result.failures[i][0].index,
    			    'request': result.failures[i][0].request,
    			    'name': result.failures[i][0].name(),
    			    'status': 'FAIL',
    			    'link': result.failures[i][0].link,
    			    'notes': result.failures[i][1]
    	                     })
    for i in range(0, len(result.errors)):
        result_dict[result.errors[i][0].name()[:3]  + "Test"].append({
    		            'index': result.errors[i][0].index,
    			    'request': result.errors[i][0].request,
    			    'name': result.errors[i][0].name(),
    			    'status': 'ERROR',
    			    'link': result.errors[i][0].link,
    			    'notes': result.errors[i][1]})
    for i in range(0, len(result.successes)):
        result_dict[result.successes[i][0].name()[:3]  + "Test"].append({
    		            'index': result.successes[i][0].index,
    			    'request': result.successes[i][0].request,
    			    'name': result.successes[i][0].name(),
    			    'status': 'OK',
    			    'link': result.successes[i][0].link,
    			    'notes': result.successes[i][1]})    
    result_dict["varTest"] = sorted(result_dict["varTest"], key=itemgetter('name', 'index'))
    result_dict["enrTest"] = sorted(result_dict["enrTest"], key=itemgetter('name','index'))
    return result_dict

def make_results_file(result):
    t=loader.get_template('results_template.html')
    page=Context({"result":result,
                  'class_name_success': 'status_passed',
		  'class_name_failure': 'status_failed'})
    f = open(template_path+"/django_templates/resultsSEQ.html", 'w+')
    f.write(t.render(page))
    f.close()

def build_test_suite(**context):

    (browser, tmp_dir) = start_browser()

    context['tmp_dir'] = tmp_dir
    context['browser'] = browser

    suite = unittest.TestSuite()
    print(context)
    
    variants_requests = context.get('variants_requests', None)
    if variants_requests:
        data = load_dictionary(variants_requests)

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
    
    enrichment_requests = context.get('enrichment_requests', None)
    if enrichment_requests:
        data = load_dictionary(enrichment_requests)

        for (index, request) in enumerate(data):
            context['index']=index
            context['request']=request
        
            test_case = EnrichmentTest()
            test_case.set_context(**context)
            suite.addTest(test_case)

    return (context, suite)

def cleanup_variants_test(**context):
    stop_browser(context['browser'])
    shutil.rmtree(context['tmp_dir'])
    

def save_test_suite(suite):
    for test in suite:
        test.save_test()

def run_test_suite(suite):
    for test in suite:
        test.runTest()
    
if __name__ == "__main__":
    test_context = {'variants_requests': "variants_tests/data_dict_variants.txt",
                    'enrichment_requests': 'variants_tests/data_dict_enrichment.txt',
                    'data_dir': "variants_tests/",
                    'results_dir': "results_dir/",
                    'url': "http://seqpipe-vm.setelis.com/dae",
                }
    context, suite = build_test_suite(**test_context)
    

    #save_test_suite(suite)
    #run_test_suite(suite)
    runner = unittest.TextTestRunner(resultclass = SeqpipeTestResult)
    result = runner.run(suite)
    #test_report(result)
    make_results_file(result_to_dict(result))
    cleanup_variants_test(**context)
    

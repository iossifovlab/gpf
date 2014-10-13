from .base import FunctionalTest
import test_get_variants
#from .test_get_variants import CheckPreviewTest

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains


from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import StaleElementReferenceException

from selenium.webdriver.support.ui import Select

import unittest
import os
import time
import random

class CheckBothVariantsAndEnrichment(FunctionalTest):
		
	def click_variants_link(self):
		
		variants_link = self.browser.find_element_by_css_selector(
				"#variants_btn > a"
			)
		actionChains = ActionChains(self.browser)
		actionChains.click(variants_link).perform()
		time.sleep(2)
		self.wait_for_variants_page_to_load()
		
	def click_enrichment_link(self):
		
		enrichment_link = self.browser.find_element_by_css_selector(
				"#enrichment > a"
			)
		actionChains = ActionChains(self.browser)
		actionChains.click(enrichment_link).perform()
		time.sleep(2)
		self.wait_for_enrichment_page_to_load()
		
	def wait_for_enrichment_page_to_load(self):
		
		try:
			element = WebDriverWait(self.browser, 30).until(
				EC.presence_of_element_located((By.ID,
					"pageContent"
					))
				)
		finally:
			pass
		
	def wait_for_variants_page_to_load(self):
		
		try:
			element = WebDriverWait(self.browser, 30).until(
				EC.presence_of_element_located((By.ID,
					"variantForm"
					))
				)
		finally:
			pass
		
	def multiple_tests_random(self , number_of_repetitions):
		
		functions_map = {
			
			'click_variants_link' : CheckBothVariantsAndEnrichment.click_variants_link,
			'click_enrichment_link' : CheckBothVariantsAndEnrichment.click_enrichment_link
		
		}
		
		key_array = [
			'click_variants_link',
			'click_enrichment_link' 
		]
				
		for i in range(0, number_of_repetitions):
			print "Test " ,i+1 , " ---------------------------------------"
			variations_of_functions = random.sample(key_array ,1 )
			print "The function is = " , variations_of_functions[0]
			functions_map[variations_of_functions[0]](self)
			if( variations_of_functions[0] == "click_variants_link" ):
				test = test_get_variants.CheckPreviewTest("multiple_tests_not_random")
				test.multiple_tests_not_random(1)
			else:
				pass
		
	def test_both_variants_and_enrichment(self):
		
		print "test_both"
		self.browser.get(self.server_url)
		#self.multiple_tests_random(5)

		
	def suite():
		
		suite = unittest.TestSuite()
		suite.addTest(test_get_variants.CheckPreviewTest("test_preview_button_multiple_times"))
		return suite
	
		





from .base import FunctionalTest

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

class CheckVariantReportTest(FunctionalTest):
	
	def random_variant_report(self):
		
		variant_report_option = Select(
			self.browser.find_element_by_id("reportSelect"))
		variant_report_option.select_by_visible_text(
			random.choice(variant_report_option.options).text)
		print variant_report_option.first_selected_option.text
		time.sleep(2)
		
	def wait_for_table(self):
		
		try:
			element = WebDriverWait(self.browser, 30).until(
				EC.presence_of_element_located((By.ID,
                                                "reportContainer"))
                                )
		finally:
			pass
		
		time.sleep(2)
		
	
	def multiple_tests_not_random(self, number_of_repetitions):
		
		for i in range(0, number_of_repetitions):
						
			self.random_variant_report()
			self.wait_for_table()
			
	def test_variant_report_mmultiple_times(self):
		
		self.browser.get(self.server_url)
		enrichment_button_elem = self.browser.find_element_by_css_selector(
			"#reports > a")
		enrichment_button_elem.click()
		
		try:
			element = WebDriverWait(self.browser, 10).until(
				EC.element_to_be_clickable((By.ID, 
					"reportSelect"))
			)
		finally:
			pass
		
		self.multiple_tests_not_random(self.ITER_COUNT)

		


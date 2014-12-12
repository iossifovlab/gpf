from .base import FunctionalTest
from .functional_helpers import *
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

class CheckEnrichmentTest(FunctionalTest):
	
	def random_denovo_gene_set_enrichment_page(self):
		
		denovo_gene_set_option = Select(
			self.browser.find_element_by_id("denovoStudiesInGeneSet"))
		denovo_gene_set_option.select_by_visible_text(
			random.choice(denovo_gene_set_option.options).text)
		print "Random denovo gene set : " , denovo_gene_set_option.first_selected_option.text
	
	def random_gene_set_main_enrichment_page(self):
		
		gene_set_main_option = Select(
			self.browser.find_element_by_id("geneSet"))
		gene_set_main_option.select_by_visible_text(
			random.choice(gene_set_main_option.options).text)
		print "Random gene set main : " , gene_set_main_option.first_selected_option.text
		if gene_set_main_option.first_selected_option.text == "Denovo":
			self.random_denovo_gene_set_enrichment_page()
		
	def random_gene_set_value_enrichment_page(self):
		gene_set_value_option = self.browser.find_element_by_xpath(
		    "//div[@id='preloadedBtn']/button")
		gene_set_value_option.click()
		
		WebDriverWait(self.browser, 10).until(
		    EC.presence_of_element_located(
			(By.CSS_SELECTOR, ".ui-autocomplete")))
	
		time.sleep(2)
		dropdown_menu =self.browser.find_elements_by_css_selector(
		    "ul.ui-autocomplete > li")
		random_value_from_dropdown_menu = str(random.randint(
		    1, len(dropdown_menu)))
		
		random_element = self.browser.find_element_by_xpath(
			"//ul[@class='ui-autocomplete " +
			"ui-front ui-menu ui-widget ui-widget-content " +
			"ui-corner-all']/li[" + random_value_from_dropdown_menu + "]"
		)
		random_element.click()
		
	def random_gene_set(self):
		
		self.random_gene_set_main_enrichment_page()
		self.random_gene_set_value_enrichment_page()
	
		
	def random_denovo_studies_enrichment_page(self):
		
		data = {}
		data['denovoStudies'] = random.choice(Select(
		    self.browser.find_element_by_id("denovoStudies")).options).text
		select_denovo_studies(self.browser, data)
		
	def wait_for_report_div(self):
		
		try:
			element = WebDriverWait(self.browser, 30).until(
				EC.presence_of_element_located((By.ID,
                                                "report"))
                                )
		finally:
			pass
		
		
		
	def wait_for_enrichment_table(self):
		
		try:
			element = WebDriverWait(self.browser, 30).until(
				EC.presence_of_element_located((By.ID,
                                                "enrichmentTable"))
                                )
                except:
                	self.wait_for_report_div()
		finally:
			pass
		
		
	def click_the_enrichment_test_button(self):
		
		preview_button = self.browser.find_element_by_id("downloadEnrichment")
		preview_button.click()
		self.wait_for_enrichment_table()
		
	def wait_for_enrichment_page_to_load(self):
		
		try:
			element = WebDriverWait(self.browser, 30).until(
				EC.presence_of_element_located((By.ID,
					"pageContent"
					))
				)
		finally:
			pass
		
	def check_reset_button_is_working_enrichment_page(self):
		
		genes_sets_radio = self.browser.find_element_by_id("geneSetsRadio")
		self.assertTrue(genes_sets_radio.is_selected())
		gene_set_row = self.browser.find_element_by_id("geneSetRow")
		self.assertTrue(gene_set_row.is_displayed())
		gene_syms_row = self.browser.find_element_by_id("geneSymsRow")
		self.assertFalse(gene_syms_row.is_displayed())
		gene_set = Select(self.browser.find_element_by_id("geneSet"))
		self.assertEqual("Main" , gene_set.first_selected_option.text)
		gene_set_input = self.browser.find_element_by_id("geneSetInput")
		self.assertEqual("Select or Start typing to search", gene_set_input.get_attribute("placeholder"))
		denovo_studies = Select(self.browser.find_element_by_id("denovoStudies"))
		self.assertEqual("allWEAndTG" , denovo_studies.first_selected_option.text)
		transmitted_studies = Select(self.browser.find_element_by_id("transmittedStudies"))
		self.assertEqual("w1202s766e611" , transmitted_studies.first_selected_option.text)
	
	def click_the_reset_button(self):
		
		reset_button = self.browser.find_element_by_id("resetEnrichment")
		reset_button.click()
		self.wait_for_enrichment_page_to_load()
		self.check_reset_button_is_working_enrichment_page()
		
		
	def multiple_tests_not_random(self, number_of_repetitions):
		
		for i in range(0, number_of_repetitions):
						
			self.random_gene_set()
			self.random_denovo_studies_enrichment_page()
			self.click_the_enrichment_test_button()
		
	def multiple_tests_random(self, number_of_repetitions):
		
		functions_map = {
			
			'random_gene_set' : CheckEnrichmentTest.random_gene_set,
			'random_denovo_studies_enrichment_page' : CheckEnrichmentTest.random_denovo_studies_enrichment_page,
			'click_the_reset_button' : CheckEnrichmentTest.click_the_reset_button
		
		}
		
		key_array_with_reset = [
			'random_gene_set',
			'random_denovo_studies_enrichment_page',
			'click_the_reset_button'
		]
		
		key_array = [
			'random_gene_set',
			'random_denovo_studies_enrichment_page'
		]
		
		for i in range(0, number_of_repetitions):
			
			print "Test " ,i+1 , " ---------------------------------------"
			random_integer = random.randint(1,3)
			variations_of_functions_with_reset = random.sample(key_array_with_reset,random_integer)
			for j in range(0, random_integer):
				print "The function is = " , variations_of_functions_with_reset[j]
				functions_map[variations_of_functions_with_reset[j]](self)
			variations_of_functions = random.sample(key_array, 2)
			for j in range(0, 2):
				print "The function is = " , variations_of_functions[j]
				functions_map[variations_of_functions[j]](self)
			print "The function is = click_the_preview_button"
			self.click_the_enrichment_test_button()
		
	def wait_button_to_be_clickable(self):
		
		try:
			random_element = WebDriverWait(self.browser, 10).until(
				EC.element_to_be_clickable((
					By.CSS_SELECTOR,
					"#enrichment > a"))
				)
		finally:
			pass
		
	def test_enrichment_multiple_times(self):
		
		self.browser.get(self.server_url)
		enrichment_button_elem = self.browser.find_element_by_css_selector(
			"#enrichment > a")
		enrichment_button_elem.click()
		try:
			element = WebDriverWait(self.browser, 10).until(
				EC.presence_of_element_located((By.ID, 
					"downloadEnrichment"))
			)
		finally:
			pass
		
		self.multiple_tests_not_random(0)
		

		
	def test_enrichment_random_clicks(self):
		
		self.browser.get(self.server_url)
		self.wait_button_to_be_clickable()
		enrichment_button_elem = self.browser.find_element_by_css_selector(
			"#enrichment > a")
		enrichment_button_elem.click()
		try:
			WebDriverWait(self.browser, 10).until(
				EC.presence_of_element_located((By.ID, 
					"downloadEnrichment"))
			)
		finally:
			pass
		
		self.multiple_tests_random(self.ITER_COUNT)
		
		

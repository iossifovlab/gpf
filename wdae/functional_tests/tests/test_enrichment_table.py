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

class CheckEnrichmentTest(FunctionalTest):
	
	def random_denovo_gene_set_enrichment_page(self):
		
		denovo_gene_set_option = Select(
			self.browser.find_element_by_id("denovoStudiesInGeneSet"))
		denovo_gene_set_option.select_by_visible_text(
			random.choice(denovo_gene_set_option.options).text)
		time.sleep(2)
	
	def random_gene_set_main_enrichment_page(self):
		
		gene_set_main_option = Select(
			self.browser.find_element_by_id("geneSet"))
		gene_set_main_option.select_by_visible_text(
			random.choice(gene_set_main_option.options).text)
		print gene_set_main_option.first_selected_option.text
		if gene_set_main_option.first_selected_option.text == "Denovo":
			self.random_denovo_gene_set_enrichment_page()
		time.sleep(2)
		
	def random_gene_set_value_enrichment_page(self):
		
		gene_set_value_option =self.browser.find_element_by_xpath(
			"//div[@id='preloadedBtn']/button")
		gene_set_value_option.click()
		time.sleep(5)
		try:
			element = WebDriverWait(self.browser, 10).until(
				EC.presence_of_element_located(
					(By.CSS_SELECTOR,".ui-autocomplete")))
		finally:
			pass
		
		dropdown_menu = self.browser.find_elements_by_css_selector(
			"ul.ui-autocomplete > li")
		
		print "dropdown_menu len" , len(dropdown_menu)
		
		random_value_from_dropdown_menu = str(random.randint(
			1,len(dropdown_menu)))
		
		print "random_value_from_dropdown_menu " , random_value_from_dropdown_menu
		
		"""
		try:
			random_element = WebDriverWait(self.browser, 10).until(
				EC.element_to_be_clickable((
					By.CSS_SELECTOR,
					"ul.ui-autocomplete > li:nth-child(" + random_value_from_dropdown_menu + ") > a"))
				)
		finally:
			pass
		"""
		
		random_element =lambda: self.browser.find_element_by_css_selector(
			"ul.ui-autocomplete > li:nth-child(" + random_value_from_dropdown_menu + ") > a")
		
		random_element().click()
		
	def random_gene_set(self):
		
		self.random_gene_set_main_enrichment_page()
		self.random_gene_set_value_enrichment_page()
	
		
	def random_denovo_studies_enrichment_page(self):
		
		denovo_studies = Select(
			self.browser.find_element_by_id("denovoStudies"))
		denovo_studies.select_by_visible_text(
			random.choice(denovo_studies.options).text)
		time.sleep(2)
		
		
	def wait_for_enrichment_table(self):
		
		try:
			element = WebDriverWait(self.browser, 30).until(
				EC.presence_of_element_located((By.ID,
                                                "enrichmentTable"))
                                )
		finally:
			pass
		
		time.sleep(2)
		
	def click_the_enrichment_test_button(self):
		
		preview_button = self.browser.find_element_by_id("downloadEnrichment")
		preview_button.click()
		self.wait_for_enrichment_table()
		
		
	def multiple_tests_not_random(self, number_of_repetitions):
		
		for i in range(0, number_of_repetitions):
						
			self.random_gene_set()
			self.random_denovo_studies_enrichment_page()
			self.click_the_enrichment_test_button()
		
	def multiple_tests_random(self, number_of_repetitions):
		
		functions_map = {
			
			'random_gene_set' : CheckEnrichmentTest.random_gene_set,
			'random_denovo_studies_enrichment_page' : CheckEnrichmentTest.random_denovo_studies_enrichment_page
		
		}
		
		key_array = [
			'random_gene_set',
			'random_denovo_studies_enrichment_page'
		]
		
		for i in range(0, number_of_repetitions):
			
			variations_of_functions = random.sample(key_array, 2)
			for j in range(0, 2):
				functions_map[variations_of_functions[j]](self)
			self.click_the_enrichment_test_button()
		
	def test_enrichment_multiple_times(self):
		
		self.browser.get(self.server_url)
		enrichment_button_elem = self.browser.find_element_by_css_selector(
			"#enrichment > a")
		enrichment_button_elem.click()
		time.sleep(3)
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
		enrichment_button_elem = self.browser.find_element_by_css_selector(
			"#enrichment > a")
		enrichment_button_elem.click()
		time.sleep(3)
		try:
			element = WebDriverWait(self.browser, 10).until(
				EC.presence_of_element_located((By.ID, 
					"downloadEnrichment"))
			)
		finally:
			pass
		
		self.multiple_tests_random(1000)
		
		

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

class CheckStudySummaries(FunctionalTest):
	
	def click_on_random_study_name(self):
		
		table = self.browser.find_element_by_id("summariesTable")
		table_size = self.browser.find_elements_by_css_selector(
				"#summariesTable > tbody > tr"
			)
		print "table size = " , len(table_size)
		random_number = str(random.randint(1,len(table_size)-1))
		study_name =self.browser.find_element_by_css_selector(
				"#summariesTable > tbody > tr:nth-child(" + random_number + ") > td:nth-child(1) > a" 
			)
		print "Click on random study name : " , study_name.text
		study_name_text = study_name.text
		study_name.click()
		self.wait_page_to_redirect()
		time.sleep(2)
		self.check_variant_report(study_name_text)
		
	def click_study_summaries_link(self):
		
		study_summaries_button = self.browser.find_element_by_css_selector(
				"#summaries > a"
			)
		actionChains = ActionChains(self.browser)
		actionChains.click(study_summaries_button).perform()
		
	def get_back(self):
		
		flag = random.randint(0,1)
		if(flag == 0):
			print "Click the back button"
			self.browser.back()
		else:
			print "Click the study summaries link"
			self.wait_button_to_be_clickable()
			study_summaries_button = self.browser.find_element_by_css_selector(
				"#summaries > a"
			)
			actionChains = ActionChains(self.browser)
			actionChains.click(study_summaries_button).perform()
			
		self.wait_summaries_table()

		
	def check_variant_report(self , string):
		
		variant_report_option = Select(
			self.browser.find_element_by_id("reportSelect"))
		self.assertEqual(string , variant_report_option.first_selected_option.text)
		studies_name = self.browser.find_element_by_css_selector(
				"#header > div:nth-child(1) > h5"
			)
		self.assertEqual("STUDIES: " + string, studies_name.text) 
		self.get_back()
		time.sleep(2)
		
	def wait_summaries_table(self):
		
		try:
			element = WebDriverWait(self.browser, 30).until(
				EC.presence_of_element_located((By.ID,
                                                "summariesTable"))
                                )
		finally:
			pass
		
		time.sleep(2)
	
	def wait_page_to_redirect(self):
		
		try:
			element = WebDriverWait(self.browser, 30).until(
				EC.presence_of_element_located((By.ID,
                                                "header"))
                                )
		finally:
			pass
		
		time.sleep(2)
		
	def wait_button_to_be_clickable(self):
		
		try:
			random_element = WebDriverWait(self.browser, 10).until(
				EC.element_to_be_clickable((
					By.CSS_SELECTOR,
					"#summaries > a"))
				)
		finally:
			pass
		
	def multiple_tests(self, number_of_repetitions):
		
		for i in range(0 , number_of_repetitions):
			
			print "Test ", i+1 ,"---------------------------------------"
			self.wait_button_to_be_clickable()
			self.click_study_summaries_link()
			self.click_on_random_study_name()
			
		
	def test_random_study_summaries(self):
		
		self.browser.get(self.server_url)
		#self.multiple_tests(self.ITER_COUNT)
		self.multiple_tests(0)

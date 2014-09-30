from .base import FunctionalTest

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import StaleElementReferenceException

from selenium.webdriver.support.ui import Select

import unittest
import os
import time
import random

class CheckPreviewTest(FunctionalTest):
	
	def is_element_stale(self,webelement):

    		try:
    			webelement
    		except StaleElementReferenceException:
    			return False
    		except:
    			pass
    
    		return True

	
	def random_families(self):
		
		families_radio_button = self.browser.find_element_by_id(
			random.choice(["allFamiliesRadio","familyAdvancedRadio"]))
		families_radio_button.click()
		
		if families_radio_button.get_attribute("value") == "advanced" :
			self.random_family_advanced_options()
		
		time.sleep(2)
	
	def random_effect_type_option(self):
		
		effect_type_option = Select(
			self.browser.find_element_by_id("effectType"))
		effect_type_option.select_by_visible_text(
			random.choice(effect_type_option.options).text)
		time.sleep(2)
	
	def random_variant_types_option(self):
		
		variant_types_option = Select(
			self.browser.find_element_by_id("variants"))
		variant_types_option.select_by_visible_text(
			random.choice(variant_types_option.options).text)
		time.sleep(2)
	
	def random_in_child_option(self):
		
		inChildOption = Select(
			self.browser.find_element_by_id("inChild"))
		inChildOption.select_by_visible_text(
			random.choice(inChildOption.options).text)
		time.sleep(2)
	
	def random_rare_radio_button_max(self):
		
		max_inputbox = lambda: self.browser.find_element_by_id("max")
		if max_inputbox().is_displayed():
			random_max_percentages = str(
				round(random.uniform(0,100),2))
			print "Random max percentages " + random_max_percentages
			max_inputbox().clear()
			max_inputbox().send_keys(random_max_percentages)
			time.sleep(2)
				
	def random_interval_max_min(self):
		
		min_inputbox = self.browser.find_element_by_id("min")
		max_inputbox = self.browser.find_element_by_id("max")
		if min_inputbox.is_displayed():
			random_min_percentages = str(
				round(random.uniform(0,100),2))
			print "Random min percentages " + random_min_percentages
			min_inputbox.clear()
			min_inputbox.send_keys(random_min_percentages)
			time.sleep(2)
				
		if min_inputbox.is_displayed():	
			random_max_percentages = str(round(random.uniform(
				float(random_min_percentages),100),2))
			print "Random max percentages " + random_max_percentages
			max_inputbox.clear()
			max_inputbox.send_keys(random_max_percentages)
			time.sleep(2)	
	
	def random_rarity_radio_buttons(self):
		
		random_integer = str(random.randrange(1, 5))
		select_random_rarity_option = self.browser.find_element_by_xpath(
			"//div[@id='rarity']/div/input[" + random_integer + "]")
		
		if select_random_rarity_option.is_displayed():
			select_random_rarity_option.click()
		time.sleep(2)
		
		if random_integer == "3":
			self.random_rare_radio_button_max()
				
		if random_integer == "4":
			self.random_interval_max_min()

		time.sleep(2)
	
	def random_transmitted_studies(self):
		
		transmitted_studies = Select(
			self.browser.find_element_by_id("transmittedStudies"))
		transmitted_studies.select_by_visible_text(
			random.choice(transmitted_studies.options).text)
		
		rarity_div = self.browser.find_element_by_id("rarity")
	
		if rarity_div.is_displayed():
			self.random_rarity_radio_buttons()

		time.sleep(2)
	
	def random_denovo_studies(self):
		
		denovo_studies = Select(
			self.browser.find_element_by_id("denovoStudies"))
		denovo_studies.select_by_visible_text(
			random.choice(denovo_studies.options).text)
		time.sleep(2)
	
	def random_denovo_gene_set(self):
		
		denovo_gene_set_option = Select(
			self.browser.find_element_by_id("denovoStudiesInGeneSet"))
		denovo_gene_set_option.select_by_visible_text(
			random.choice(denovo_gene_set_option.options).text)
		time.sleep(2)
	
	def random_gene_set_main(self):
		
		gene_set_main_option = Select(
			self.browser.find_element_by_xpath("//select[@id='geneSet']"))
		gene_set_main_option.select_by_visible_text(
			random.choice(gene_set_main_option.options).text)
		print gene_set_main_option.first_selected_option.text
		if gene_set_main_option.first_selected_option.text == "Denovo":
			self.random_denovo_gene_set()
		time.sleep(2)
		
	def random_gene_set_value(self):
		
		gene_set_value_option =self.browser.find_element_by_xpath(
			"//div[@id='preloadedBtn']/button")
		gene_set_value_option.click()
		time.sleep(5)
		dropdown_menu = self.browser.find_elements_by_xpath(
			"//ul[@id='ui-id-1']/li")
		
		random_value_from_dropdown_menu = str(random.randint(
			1,len(dropdown_menu)))
		
		print "I want this len = " , len(dropdown_menu)
		random_element =lambda: self.browser.find_element_by_xpath(
			"//ul[@id='ui-id-1']/li[" + 
			random_value_from_dropdown_menu + "]")
		
		#wait = WebDriverWait(self.browser, 10)
		#element = wait.until(lambda s: CheckPreviewTest.is_element_stale(self,random_element))
		
		"""try:
			element = WebDriverWait(self.browser, 30).until(
				        EC.element_to_be_clickable(
				        	(By.XPATH,
				        		"//ul[@id='ui-id-1']/li[" 
				        		+ random_value_from_dropdown_menu + "]"))
                                )
		finally:
			pass
		"""
		 
		random_element().click()
		time.sleep(2)
		
	def random_gene_sets_radio_buttons(self):
		
		self.random_gene_set_main()
		self.random_gene_set_value()
	
	def random_genes(self):
		
		time.sleep(5)
		
		genes_all_option = self.browser.find_element_by_id(
			random.choice(["allGenesRadio","geneSetsRadio"]))
			#random.choice(["geneSetsRadio"]))
		genes_all_option.click()
		
		time.sleep(5)
		
		if genes_all_option.get_attribute("id") == "geneSetsRadio":
			
			self.random_gene_sets_radio_buttons()
	
	def random_race_option(self):
		
		race_option = Select(self.browser.find_element_by_id("race"))
		race_option.select_by_visible_text(
			random.choice(race_option.options).text)
		time.sleep(2)
		
	def random_verbal_iq_low(self):
		
		verbal_IQ_low = self.browser.find_element_by_id("verbalIQLow")
		verbal_IQ_low.clear()
		verbal_IQ_low.send_keys(str(random.randrange(1,100)))
		time.sleep(2)
		
	def random_verbal_iq_high(self):
		
		verbal_IQ_high = self.browser.find_element_by_id("verbalIQHigh")
		verbal_IQ_high.clear()
		verbal_IQ_high.send_keys(str(random.randrange(int(
			self.browser.find_element_by_id(
				"verbalIQLow").get_attribute("value")
			),200)))
		time.sleep(2)
		
	def random_quad_trio(self):
		
		quad_trio_option = Select(self.browser.find_element_by_id("quad-trio"))
		quad_trio_option.select_by_visible_text(
			random.choice(quad_trio_option.options).text)
		time.sleep(2)
		
	def random_proband_gender(self):
		
		proband_gender_option = Select(
			self.browser.find_element_by_id("probandGender"))
		proband_gender_option.select_by_visible_text(
			random.choice(proband_gender_option.options).text)
		time.sleep(2)
		
	def random_sibling_gender(self):
		
		sibling_gender_option = Select(
			self.browser.find_element_by_id("siblingGender"))
		sibling_gender_option.select_by_visible_text(
			random.choice(sibling_gender_option.options).text)
		time.sleep(2)
	
	def random_family_advanced_options(self):
		
		self.random_race_option()
		self.random_verbal_iq_low()
		self.random_verbal_iq_high()
		self.random_quad_trio()
		self.random_proband_gender()
		self.random_sibling_gender()
	
	def wait_for_table(self):
		
		try:
			element = WebDriverWait(self.browser, 30).until(
				EC.presence_of_element_located((By.ID,
                                                "previewTable"))
                                )
		finally:
			pass
		
		time.sleep(2)
		
	def click_the_preview_button(self):
		
		preview_button = self.browser.find_element_by_id("previewBtn")
		preview_button.click()
		self.wait_for_table()
		
	def multiple_tests_not_random(self, number_of_repetitions):
		
		for i in range(0, number_of_repetitions):
						
			self.random_genes()
			self.random_denovo_studies()
			self.random_transmitted_studies()
			self.random_in_child_option()
			self.random_variant_types_option()
			self.random_effect_type_option()
			self.random_families()
			self.click_the_preview_button()
			
	def multiple_tests_random(self, number_of_repetitions):
		
		functions_map = {
			
			'random_families' : CheckPreviewTest.random_families,
			'random_effect_type_option' : CheckPreviewTest.random_effect_type_option,
			'random_variant_types_option' : CheckPreviewTest.random_variant_types_option,
			'random_in_child_option' : CheckPreviewTest.random_in_child_option,
			'random_transmitted_studies' : CheckPreviewTest.random_transmitted_studies,
			'random_denovo_studies' : CheckPreviewTest.random_denovo_studies,
			'random_genes' : CheckPreviewTest.random_genes,
			'click_the_preview_button': CheckPreviewTest.click_the_preview_button
		
		}
		
		key_array = ['random_families',
			'random_effect_type_option' ,
			'random_variant_types_option',
			'random_in_child_option' ,
			'random_transmitted_studies',
			'random_denovo_studies',
			'random_genes',
			'click_the_preview_button'
		]
		
		for i in range(0, number_of_repetitions):
			
			random_integer = random.randint(1,len(key_array))
			print "Random Integer = " , random_integer
			variations_of_functions = random.sample(key_array, random_integer)
			for j in range(0, random_integer):
				print "The function is = " , variations_of_functions[j]
				functions_map[variations_of_functions[j]](self)
			print "The function is = click_the_preview_button"
			self.click_the_preview_button()
	
			
		
	
	def test_preview_button_multiple_times(self):
		
		self.browser.get(self.server_url)
		self.multiple_tests_not_random(5)
		
	def test_preview_button_random_clicks(self):
		
		self.browser.get(self.server_url)
		self.multiple_tests_random(5)
		

			
	
	

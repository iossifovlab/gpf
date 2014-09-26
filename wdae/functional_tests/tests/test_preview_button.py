from .base import FunctionalTest

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.support.ui import Select

import unittest
import os
import time
import random

class CheckPreviewTest(FunctionalTest):
	
	def handle_families(self):
		
		families_radio_button = self.browser.find_element_by_id(random.choice(["allFamiliesRadio","familyAdvancedRadio"]))
		families_radio_button.click()
		
		if families_radio_button.get_attribute("value") == "advanced" :
			self.handle_family_advanced_options()
		
		time.sleep(2)
	
	def handle_effect_type_option(self):
		
		effect_type_option = Select(self.browser.find_element_by_id("effectType"))
		effect_type_option.select_by_visible_text(random.choice(effect_type_option.options).text)
		time.sleep(2)
	
	def handle_variant_types_option(self):
		
		variant_types_option = Select(self.browser.find_element_by_id("variants"))
		variant_types_option.select_by_visible_text(random.choice(variant_types_option.options).text)
		time.sleep(2)
	
	def handle_in_child_option(self):
		
		inChildOption = Select(self.browser.find_element_by_id("inChild"))
		inChildOption.select_by_visible_text(random.choice(inChildOption.options).text)
		time.sleep(2)
	
	def handle_rare(self):
		
		max_inputbox = self.browser.find_element_by_id("max")
		if max_inputbox.is_displayed():
			random_max_percentages = str(round(random.uniform(0,100),2))
			print "Random max percentages " + random_max_percentages
			max_inputbox.clear()
			max_inputbox.send_keys(random_max_percentages)
			time.sleep(2)
				
	def handle_interval(self):
		
		min_inputbox = self.browser.find_element_by_id("min")
		max_inputbox = self.browser.find_element_by_id("max")
		if min_inputbox.is_displayed():
			random_min_percentages = str(round(random.uniform(0,100),2))
			print "Random min percentages " + random_min_percentages
			min_inputbox.clear()
			min_inputbox.send_keys(random_min_percentages)
			time.sleep(2)
				
		if min_inputbox.is_displayed():	
			random_max_percentages = str(round(random.uniform(float(random_min_percentages),100),2))
			print "Random max percentages " + random_max_percentages
			max_inputbox.clear()
			max_inputbox.send_keys(random_max_percentages)
			time.sleep(2)	
	
	def handle_rarity_div(self):
		
		random_integer = str(random.randrange(1, 5))
		select_random_rarity_option = self.browser.find_element_by_xpath("//div[@id='rarity']/div/input[" + random_integer + "]")
		
		if select_random_rarity_option.is_displayed():
			select_random_rarity_option.click()
		time.sleep(2)
		
		if random_integer == "3":
			self.handle_rare()
				
		if random_integer == "4":
			self.handle_interval()

		time.sleep(2)
	
	def handle_transmitted_studies(self):
		
		transmitted_studies = Select(self.browser.find_element_by_id("transmittedStudies"))
		transmitted_studies.select_by_visible_text(random.choice(transmitted_studies.options).text)
		time.sleep(2)
	
	def handle_denovo_studies(self):
		
		denovo_studies = Select(self.browser.find_element_by_id("denovoStudies"))
		print "Denovo Studies" , denovo_studies.first_selected_option.text
		denovo_studies.select_by_visible_text(random.choice(denovo_studies.options).text)
		time.sleep(2)
	
	def handle_Denovo_gene_set(self):
		
		denovo_gene_set_option = Select(self.browser.find_element_by_id("denovoStudiesInGeneSet"))
		denovo_gene_set_option.select_by_visible_text(random.choice(denovo_gene_set_option.options).text)
		time.sleep(2)
	
	def handle_gene_set_main(self):
		
		gene_set_main_option = Select(self.browser.find_element_by_xpath("//select[@id='geneSet']"))
		gene_set_main_option.select_by_visible_text(random.choice(gene_set_main_option.options).text)
		print gene_set_main_option.first_selected_option.text
		if gene_set_main_option.first_selected_option.text == "Denovo":
			self.handle_Denovo_gene_set()
		time.sleep(2)
		
	def handle_gene_set_value(self):
		
		gene_set_value_option = self.browser.find_element_by_xpath("//div[@id='preloadedBtn']/button")
		gene_set_value_option.click()
		dropdown_menu = self.browser.find_elements_by_xpath("//ul[@id='ui-id-1']/li")
		random.choice(dropdown_menu).click()
		time.sleep(2)
		
	def handle_gene_sets_radio(self):
		
		self.handle_gene_set_main()
		self.handle_gene_set_value()
	
	def handle_Genes(self):
		
		genes_all_option = self.browser.find_element_by_id(random.choice(["allGenesRadio","geneSetsRadio"]))
		genes_all_option.click()
		
		time.sleep(5)
		
		if genes_all_option.get_attribute("id") == "geneSetsRadio":
			
			self.handle_gene_sets_radio()
	
	def handle_race_option(self):
		
		race_option = Select(self.browser.find_element_by_id("race"))
		race_option.select_by_visible_text(random.choice(race_option.options).text)
		time.sleep(2)
		
	def handle_verbal_IQ_low(self):
		
		verbal_IQ_low = self.browser.find_element_by_id("verbalIQLow")
		verbal_IQ_low.clear()
		verbal_IQ_low.send_keys(str(random.randrange(1,100)))
		time.sleep(2)
		
	def handle_verbal_IQ_high(self):
		
		verbal_IQ_high = self.browser.find_element_by_id("verbalIQHigh")
		verbal_IQ_high.clear()
		verbal_IQ_high.send_keys(str(random.randrange(int(
			self.browser.find_element_by_id("verbalIQLow").get_attribute("value")
			),200)))
		time.sleep(2)
		
	def handle_quad_trio(self):
		
		quad_trio_option = Select(self.browser.find_element_by_id("quad-trio"))
		quad_trio_option.select_by_visible_text(random.choice(quad_trio_option.options).text)
		time.sleep(2)
		
	def handle_proband_gender(self):
		
		proband_gender_option = Select(self.browser.find_element_by_id("probandGender"))
		proband_gender_option.select_by_visible_text(random.choice(proband_gender_option.options).text)
		time.sleep(2)
		
	def handle_sibling_gender(self):
		
		sibling_gender_option = Select(self.browser.find_element_by_id("siblingGender"))
		sibling_gender_option.select_by_visible_text(random.choice(sibling_gender_option.options).text)
		time.sleep(2)
	
	def handle_family_advanced_options(self):
		
		self.handle_race_option()
		self.handle_verbal_IQ_low()
		self.handle_verbal_IQ_high()
		self.handle_quad_trio()
		self.handle_proband_gender()
		self.handle_sibling_gender()
	
	def test_preview_button(self):
		
		self.browser.get(self.server_url)
		
		self.handle_Genes()
		self.handle_denovo_studies()
		self.handle_transmitted_studies()
		
		try:
			rarity_options = WebDriverWait(self.browser, 10).until(
				EC.presence_of_element_located((By.ID,
                                                "rarity"))
                                )
		finally:
			pass
		
		rarity_div = self.browser.find_element_by_id("rarity")

		if rarity_div.is_displayed():
			
			self.handle_rarity_div()
			
		self.handle_in_child_option()
		self.handle_variant_types_option()
		self.handle_effect_type_option()
		self.handle_families()
		
		preview_button = self.browser.find_element_by_id("previewBtn")
		preview_button.click()
		
		try:
			element = WebDriverWait(self.browser, 10).until(
				EC.presence_of_element_located((By.ID,
                                                "previewTable"))
                                )
		finally:
			pass
		
		time.sleep(2)
				
from .base import FunctionalTest
from .base_variants import base_select

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


class VariantsTest(FunctionalTest,base_select):
	
	def get_dictionary(self):
		return {'geneRegionType': 'on', 'familyVerbalIqLo': '45', 'geneTerm': 'BIOCARTA_BCELLSURVIVAL_PATHWAY', 'inChild': 'prb', 'popFrequencyMax': '14.31', 'familyPrbGender': 'All', 'transmittedStudies': 'w1202s766e611', 'popFrequencyMin': '12.34', 'geneSet': 'MSigDB.curated', 'families': 'advanced', 'familyIds': '', 'familyQuadTrio': 'All', 'genes': 'Gene Sets', 'effectTypes': 'tRNA:ANTICODON', 'familySibGender': 'All', 'variantTypes': 'del', 'familyRace': 'All', 'denovoStudies': 'sscPublishedWE', 'geneSyms': '', 'geneStudy': 'allWEAndTG', 'rarity': 'interval', 'familyVerbalIqHi': '145', 'geneRegion': ''}



	def select_gene_set_main(self,_dict):
		
		base_select(self).select_method_by_value("geneSet",_dict['geneSet'])
		
	def select_gene_set_value(self,_dict):
		
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
		selected_element =lambda: self.browser.find_element_by_xpath(
				"//ul[@class='ui-autocomplete ui-front ui-menu ui-widget ui-widget-content ui-corner-all']/li/a[contains(text(),'" + _dict['geneTerm'] +"')]"
			)
		
		print "Random gene set value : " , selected_element().text
		
		selected_element().click()
		
		time.sleep(2)
	
	def select_denovo_studies(self, _dict):
		
		base_select(self).select_method("denovoStudies",_dict['denovoStudies'])
	
	def select_in_child(self, _dict):
		
		base_select(self).select_method("inChild",_dict['inChild'])
		
	def select_effect_type(self,_dict):
		
		base_select(self).select_method("effectType",_dict['effectTypes'])
		
	def select_variant_type(self,_dict):
		
		base_select(self).select_method("variants",_dict['variantTypes'])
		
	def genes_radio_buttons(self,_dict):
		
		base_select(self).radio_button_select(_dict['genes'])
	
	
	def select_rare_max(self,_dict):
		
		base_select(self).type_method("max",_dict['popFrequencyMax'])
		
	def select_rare_interval(self,_dict):
		
		base_select(self).type_method("min",_dict['popFrequencyMin'])
		base_select(self).type_method("max",_dict['popFrequencyMax'])
	
	def select_rarity_radio_buttons(self,_dict):
		
		self.browser.find_element_by_id(_dict['rarity']).click()
		if _dict['rarity'] == "rare":
			self.select_rare_max(_dict)
		if _dict['rarity'] == "interval":
			self.select_rare_interval(_dict)
			
	
	def select_transmitted_studies(self, _dict):
		
		base_select(self).select_method("transmittedStudies",_dict['transmittedStudies'])
		rarity_div = self.browser.find_element_by_id("rarity")
		if rarity_div.is_displayed():
			self.select_rarity_radio_buttons(_dict)
	
	def select_gene_symbols(self,gene_list):
		
		gene_syms_radio = self.browser.find_element_by_id("geneSymsRadio")
		gene_syms_radio.click()
		gene_syms_text_area = self.browser.find_element_by_id("geneSyms")
		gene_syms_text_area.send_keys("\n".join(gene_list))
		time.sleep(2)
		
	def select_race_option(self,_dict):
		
		base_select(self).select_method("race",_dict['familyRace']);
	
	def select_verbal_iq_low(self,_dict):
		
		base_select(self).type_method("verbalIQLow",_dict['familyVerbalIqLo'])
		
	def select_verbal_iq_high(self,_dict):
		
		base_select(self).type_method("verbalIQHigh",_dict['familyVerbalIqHi'])
		
	def select_quad_trio(self,_dict):
		
		base_select(self).select_method("quad-trio",_dict['familyQuadTrio']);
		
	def select_proband_gender(self,_dict):
		
		base_select(self).select_method("probandGender",_dict['familyPrbGender']);
		
	def select_sibling_gender(self,_dict):
		
		base_select(self).select_method("siblingGender",_dict['familySibGender']);
		
	def select_family_advanced_options(self,_dict):
		
		self.select_race_option(_dict)
		self.select_verbal_iq_low(_dict)
		self.select_verbal_iq_high(_dict)
		self.select_quad_trio(_dict)
		self.select_proband_gender(_dict)
		self.select_sibling_gender(_dict)
		
	def select_families(self,_dict):
		
		self.browser.find_element_by_xpath("//div[@class='controls form-inline']//input[@value='" + _dict['families'] + "']").click()
		if _dict['families'] == "advanced":
			self.select_family_advanced_options(_dict)
		
	def dictionary_test(self,_dict):
	
		self.genes_radio_buttons(_dict)
		self.select_gene_set_main(_dict)
		self.select_gene_set_value(_dict)
		self.select_denovo_studies(_dict)
		self.select_transmitted_studies(_dict)
		self.select_in_child(_dict)
		self.select_variant_type(_dict)
		self.select_effect_type(_dict)
		self.select_families(_dict)
		
	def test_variants_with_predefined_values(self):
		
		self.browser.get(self.server_url)
		_dict = self.get_dictionary()
		print "keys : ", _dict.keys()
		self.dictionary_test(_dict)
		#self.select_gene_symbols(["a","b","c"])
		

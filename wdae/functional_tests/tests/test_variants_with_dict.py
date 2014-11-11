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
import ast
import filecmp


class VariantsTest(FunctionalTest,base_select):
	
	def get_dictionary(self):
		return {'geneRegionType': 'on', 'familyVerbalIqLo': '45', 'geneTerm': 'BIOCARTA_BCELLSURVIVAL_PATHWAY', 'inChild': 'prb', 'popFrequencyMax': '14.31', 'familyPrbGender': 'All', 'transmittedStudies': 'w1202s766e611', 'popFrequencyMin': '12.34', 'geneSet': 'MSigDB.curated', 'families': 'advanced', 'familyIds': '', 'familyQuadTrio': 'All', 'genes': 'Gene Sets', 'effectTypes': 'tRNA:ANTICODON', 'familySibGender': 'All', 'variantTypes': 'del', 'familyRace': 'All', 'denovoStudies': 'sscPublishedWE', 'geneSyms': '', 'geneStudy': 'allWEAndTG', 'rarity': 'interval', 'familyVerbalIqHi': '145', 'geneRegion': ''}



	def select_gene_set_main(self, data):
		
		base_select(self).select_method_by_value("geneSet",data['geneSet'])
		
	def select_gene_set_value(self,data):
		
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
				"//ul[@class='ui-autocomplete ui-front ui-menu ui-widget ui-widget-content ui-corner-all']/li/a[contains(text(),'" + data['geneTerm'] +"')]"
			)
		
		print "Random gene set value : " , selected_element().text
		
		selected_element().click()
		
		time.sleep(2)
	
	def select_denovo_studies(self, data):
		
		base_select(self).select_method("denovoStudies",data['denovoStudies'])
	
	def select_in_child(self, data):
		
		base_select(self).select_method("inChild",data['inChild'])
		
	def select_effect_type(self,data):
		
		base_select(self).select_method("effectType",data['effectTypes'])
		
	def select_variant_type(self,data):
		
		base_select(self).select_method("variants",data['variantTypes'])
		
	def genes_radio_buttons(self,data):
		
		base_select(self).radio_button_select(data['genes'])
	
	
	def select_rare_max(self,data):
		
		base_select(self).type_method("max",data['popFrequencyMax'])
		
	def select_rare_interval(self,data):
		
		base_select(self).type_method("min",data['popFrequencyMin'])
		base_select(self).type_method("max",data['popFrequencyMax'])
	
	def select_rarity_radio_buttons(self,data):
		
		self.browser.find_element_by_id(data['rarity']).click()
		if data['rarity'] == "rare":
			self.select_rare_max(data)
		if data['rarity'] == "interval":
			self.select_rare_interval(data)
			
	
	def select_transmitted_studies(self, data):
		
		base_select(self).select_method("transmittedStudies",data['transmittedStudies'])
		rarity_div = self.browser.find_element_by_id("rarity")
		if rarity_div.is_displayed():
			self.select_rarity_radio_buttons(data)
	
	def select_gene_symbols(self,gene_list):
		
		gene_syms_radio = self.browser.find_element_by_id("geneSymsRadio")
		gene_syms_radio.click()
		gene_syms_text_area = self.browser.find_element_by_id("geneSyms")
		gene_syms_text_area.send_keys(gene_list)
		time.sleep(2)
		
	def select_family_ids(self,family_list):
		
		family_ids_radio = self.browser.find_element_by_id(
			"familyIdsRadio")
		family_ids_radio.click()
		family_ids_text_area = self.browser.find_element_by_id("familyIds")
		family_ids_text_area.send_keys(family_list)
		time.sleep(2)
		
	def select_race_option(self,data):
		
		base_select(self).select_method("race",data['familyRace']);
	
	def select_verbal_iq_low(self,data):
		
		base_select(self).type_method("verbalIQLow",data['familyVerbalIqLo'])
		
	def select_verbal_iq_high(self,data):
		
		base_select(self).type_method("verbalIQHigh",data['familyVerbalIqHi'])
		
	def select_quad_trio(self,data):
		
		base_select(self).select_method("quad-trio",data['familyQuadTrio']);
		
	def select_proband_gender(self,data):
		
		base_select(self).select_method("probandGender",data['familyPrbGender']);
		
	def select_sibling_gender(self,data):
		
		base_select(self).select_method("siblingGender",data['familySibGender']);
		
	def select_family_advanced_options(self,data):
		
		self.select_race_option(data)
		self.select_verbal_iq_low(data)
		self.select_verbal_iq_high(data)
		self.select_quad_trio(data)
		self.select_proband_gender(data)
		self.select_sibling_gender(data)
		
	def select_families(self,data):
		
		self.browser.find_element_by_xpath(
			"//div[@class='controls form-inline']//input[@value='" + data['families'] + "']").click()
		if data['families'] == "advanced":
			self.select_family_advanced_options(data)
		if data['families'] == 'familyIds':
			self.select_family_ids(data['familyIds'])
			
	def wait_for_table(self):

		try:
		    element = WebDriverWait(self.browser, 60).until(
			EC.presence_of_element_located((By.ID,
							"previewTable"))
					)
		finally:
		    pass
	
		time.sleep(2)
		
	def wait_for_chroms(self):
		
		try:
		    element = WebDriverWait(self.browser, 60).until(
			EC.presence_of_element_located((By.CSS_SELECTOR,
							"div#preview > svg"))
					)
		finally:
		    pass
	
		time.sleep(2)

   	def click_the_preview_button(self):
	
		preview_button = self.browser.find_element_by_id("previewBtn")
		preview_button.click()
		self.wait_for_table()
		
	def click_the_chroms_button(self):
		
		preview_button = self.browser.find_element_by_id("chromsBtn")
		preview_button.click()
		self.wait_for_chroms()
		
	def get_table_content(self,idx):
		
		table_content = []
		temp = self.browser.find_elements_by_css_selector(
			"table#previewTable > tbody > tr")
		f = open('/home/alexanderpopov/Projects/SeqPipelineTesting/python/wdae/functional_tests/tests/table_results_' + str(idx) + '.txt', 'w+')
		for tr in temp:
			tds=tr.find_elements_by_css_selector('td')
			for td in tds:
				table_content.append(td.text)
		f.write(str([str(x) for x in table_content]))
		f.close()
		
	def get_chroms_content(self,idx):
		
		chroms_content = []
		temp = self.browser.find_element_by_css_selector(
			"div#preview > svg > svg > g")
		temp_rect = temp.find_elements_by_css_selector("rect")
		temp_path = temp.find_elements_by_css_selector("path")
		f = open('/home/alexanderpopov/Projects/SeqPipelineTesting/python/wdae/functional_tests/tests/chroms_results_' + str(idx) + '.txt', 'w+')
		for elem in temp_rect:
			f.write(str(elem.get_attribute("x")) + " / ")
			f.write(str(elem.get_attribute("y")) +" / ")
			f.write(str(elem.get_attribute("width"))+" / ")
			f.write(str(elem.get_attribute("height"))+ " / ")
			f.write(str(elem.get_attribute("style"))+ " / ")
			f.write("\n")
		for elem in temp_path:
			f.write(str(elem.get_attribute("d"))+" / ")
			f.write(str(elem.get_attribute("transform"))+ " / ")
			f.write(str(elem.get_attribute("style"))+ " / ")
			f.write("\n")		
		f.close()
		
	def wait_for_page_to_load(self):

		try:
		    element = WebDriverWait(self.browser, 30).until(
			EC.presence_of_element_located((By.ID,
			    "sammyContainer"
			    ))
			)
		finally:
			pass
	
	def click_the_reset_button(self):
	
		reset_button = self.browser.find_element_by_id("resetBtn")
		reset_button.click()
		time.sleep(2)
		self.wait_for_page_to_load()
		
	def compare_chroms_files(self):
		
		print filecmp.cmp('/home/alexanderpopov/Projects/SeqPipelineTesting/python/wdae/functional_tests/tests/chroms_results_0.txt' , '/home/alexanderpopov/Projects/SeqPipelineTesting/python/wdae/functional_tests/tests/chroms_results_0.txt')
		
	def dictionary_test(self,data,idx):
		
		self.compare_chroms_files()
		self.genes_radio_buttons(data)
		if data['genes'] == 'Gene Sets':
			self.select_gene_set_main(data)
			self.select_gene_set_value(data)
		if data['genes'] == 'Gene Symbols':
			self.select_gene_symbols(data['geneSyms'])
		self.select_denovo_studies(data)
		self.select_transmitted_studies(data)
		self.select_in_child(data)
		self.select_variant_type(data)
		self.select_effect_type(data)
		self.select_families(data)
		self.click_the_preview_button()
		self.get_table_content(idx)
		self.click_the_chroms_button()
		self.get_chroms_content(idx)
		self.click_the_reset_button()
		
	def test_variants_with_predefined_values(self):
		
		self.browser.get(self.server_url)
		data = self.get_dictionary()
		text_file = open(
			r'/home/alexanderpopov/Projects/SeqPipelineTesting/python/wdae/functional_tests/tests/data_dict.txt')
		lines = text_file.readlines()
		print len(lines)
		for idx,line in enumerate(lines):
			print "idx",idx
			temp_data = ast.literal_eval(line)
			self.dictionary_test(temp_data,idx)
		text_file.close()
		#self.dictionary_test(data)
		#self.select_gene_symbols(["a","b","c"])
		

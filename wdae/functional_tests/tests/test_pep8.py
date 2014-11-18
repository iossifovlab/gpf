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


class VariantsTest(FunctionalTest, base_select):

    location = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
    results_dir = '/results_dir/variants/'
    tests_defs = 'data_dict.txt'

    def get_dictionary(self):
        text_file = open(os.path.join(
            VariantsTest.location, 'data_dict.txt'), 'r')
        data=text_file.readlines()
        text_file.close()
        return data

    def select_denovo_gene_set(self, data):
    	base_select(self).select_method_by_value(
            "denovoStudiesInGeneSet", data['geneStudy'])

    def select_gene_set_main(self, data):

        base_select(self).select_method_by_value(
            "geneSet", data['geneSet'])
        if data['geneSet']=='denovo':
             self.select_denovo_gene_set(data)

    def select_gene_set_value(self, data):

        gene_set_value_option = self.browser.find_element_by_xpath(
            "//div[@id='preloadedBtn']/button")
        gene_set_value_option.click()
        time.sleep(5)

        try:
            element = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".ui-autocomplete")))
        finally:
            pass
        selected_element = lambda: self.browser.find_element_by_xpath(
            "//ul[@class='ui-autocomplete " +
            "ui-front ui-menu ui-widget ui-widget-content " +
            "ui-corner-all']/li/a[contains(text(),'" +
            data['geneTerm'] + "')]"
        )

        print "Random gene set value : ", selected_element().text

        selected_element().click()

        time.sleep(2)

    def select_denovo_studies(self, data):

        base_select(self).select_method(
            "denovoStudies", data['denovoStudies'])

    def select_in_child(self, data):

        base_select(self).select_method("inChild", data['inChild'])

    def select_effect_type(self, data):

        base_select(self).select_method(
            "effectType", data['effectTypes'])

    def select_variant_type(self, data):

        base_select(self).select_method(
            "variants", data['variantTypes'])

    def genes_radio_buttons(self, data):
        base_select(self).radio_button_select(data['genes'])
        if data['genes'] == 'Gene Sets':
            self.select_gene_set_main(data)
            self.select_gene_set_value(data)
        if data['genes'] == 'Gene Symbols':
            self.select_gene_symbols(data['geneSyms'])

    def select_rare_max(self, data):

        base_select(self).type_method("max", data['popFrequencyMax'])

    def select_rare_interval(self, data):

        base_select(self).type_method("min", data['popFrequencyMin'])
        base_select(self).type_method("max", data['popFrequencyMax'])

    def select_rarity_radio_buttons(self, data):

        self.browser.find_element_by_id(data['rarity']).click()
        if data['rarity'] == "rare":
            self.select_rare_max(data)
        if data['rarity'] == "interval":
            self.select_rare_interval(data)

    def select_transmitted_studies(self, data):

        base_select(self).select_method("transmittedStudies",
                                        data['transmittedStudies'])
        rarity_div = self.browser.find_element_by_id("rarity")
        if rarity_div.is_displayed():
            self.select_rarity_radio_buttons(data)

    def select_gene_symbols(self, gene_list):

        gene_syms_radio = self.browser.find_element_by_id(
            "geneSymsRadio")
        gene_syms_radio.click()
        gene_syms_text_area = self.browser.find_element_by_id(
            "geneSyms")
        gene_syms_text_area.send_keys(gene_list)
        time.sleep(2)

    def select_family_ids(self, family_list):

        family_ids_radio = self.browser.find_element_by_id(
            "familyIdsRadio")
        family_ids_radio.click()
        family_ids_text_area = self.browser.find_element_by_id(
            "familyIds")
        family_ids_text_area.send_keys(family_list)
        time.sleep(2)

    def select_race_option(self, data):

        base_select(self).select_method("race", data['familyRace'])

    def select_verbal_iq_low(self, data):

        base_select(self).type_method("verbalIQLow",
                                      data['familyVerbalIqLo'])

    def select_verbal_iq_high(self, data):

        base_select(self).type_method("verbalIQHigh",
                                      data['familyVerbalIqHi'])

    def select_quad_trio(self, data):

        base_select(self).select_method("quad-trio",
                                        data['familyQuadTrio'])

    def select_proband_gender(self, data):

        base_select(self).select_method("probandGender",
                                        data['familyPrbGender'])

    def select_sibling_gender(self, data):

        base_select(self).select_method("siblingGender",
                                        data['familySibGender'])

    def select_family_advanced_options(self, data):

        self.select_race_option(data)
        self.select_verbal_iq_low(data)
        self.select_verbal_iq_high(data)
        self.select_quad_trio(data)
        self.select_proband_gender(data)
        self.select_sibling_gender(data)

    def select_families(self, data):

        self.browser.find_element_by_xpath(
            "//div[@class='controls form-inline']//input[@value='" +
            data['families'] + "']").click()
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

    def get_preview_content(self, idx):

        preview_content = []
        temp = self.browser.find_elements_by_css_selector(
            "table#previewTable > tbody > tr")
        for tr in temp:
            tds = tr.find_elements_by_css_selector('td')
            for td in tds:
                preview_content.append(td.text)
        return preview_content

    def get_chroms_content(self, idx):
        
        chroms_content = []
        temp = self.browser.find_element_by_css_selector(
            "div#preview > svg > svg > g")
        temp_rect = temp.find_elements_by_css_selector("rect")
        temp_path = temp.find_elements_by_css_selector("path")

        for elem in temp_rect:
            chroms_content.append(elem.get_attribute("x"))
            chroms_content.append(elem.get_attribute("y"))
            chroms_content.append(elem.get_attribute("width"))
            chroms_content.append(elem.get_attribute("height"))
            chroms_content.append(elem.get_attribute("style"))
        for elem in temp_path:
            chroms_content.append(elem.get_attribute("d"))
            chroms_content.append(elem.get_attribute("transform"))
            chroms_content.append(elem.get_attribute("style"))
            
        return chroms_content
        
    def generate_file(self, idx, type_of_data):
    	return (VariantsTest.location + VariantsTest.results_dir +
    	       str(type_of_data)+str(idx)+'.txt')
        
    def save_content_to_file(self, data, idx, type_of_data):
    	filename=self.generate_file(idx, type_of_data)
    	f = open(os.path.join(filename), 'w+')
        #f.write(str([str(x) for x in data]))
        f.write(str(data))
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

    def compare_table_files(self):

        print filecmp.cmp(
            os.path.join(
                VariantsTest.location, 'table_results_0.txt'),
            os.path.join(
                VariantsTest.location, 'table_results_1.txt'))

    def compare_chroms_files(self):

        print filecmp.cmp(
            os.path.join(
                VariantsTest.location, 'chroms_results_0.txt'),
            os.path.join(
                VariantsTest.location, 'chroms_results_0.txt'))

    def download_file(self):
        download_button = self.browser.find_element_by_id(
            "submitBtn")
        download_button.click()
        time.sleep(3)
        
    def dictionary_test(self, data, idx):

        self.genes_radio_buttons(data)
        self.select_denovo_studies(data)
        self.select_transmitted_studies(data)
        self.select_in_child(data)
        self.select_variant_type(data)
        self.select_effect_type(data)
        self.select_families(data)
        self.download_file()
        self.click_the_preview_button()
        self.get_preview_content(idx)
        self.click_the_chroms_button()
        self.get_chroms_content(idx)
        self.click_the_reset_button()
        self.compare_table_files()
        self.compare_chroms_files()

    def fill_variants_form(self, data_defs):

        self.genes_radio_buttons(data_defs)
        self.select_denovo_studies(data_defs)
        self.select_transmitted_studies(data_defs)
        self.select_in_child(data_defs)
        self.select_variant_type(data_defs)
        self.select_effect_type(data_defs)
        self.select_families(data_defs)

    def read_content_from_file(self, idx, type_of_data):
    	f=open(VariantsTest.location+VariantsTest.results_dir+
    		'/'+str(type_of_data)+str(idx)+'.txt','r')
    	data=f.read()
    	f.close()
    	print ast.literal_eval(data)
        return ast.literal_eval(data)
    
    def execute(self, idx):

        #self.download_file()
        self.click_the_preview_button()
        preview_content=self.get_preview_content(idx)
        preview_content_from_file=self.read_content_from_file(idx,
        	                                             'preview_results_')
        self.assertTrue(preview_content==preview_content_from_file)
	self.click_the_chroms_button()
        chroms_content=self.get_chroms_content(idx)
        chroms_content_from_file=self.read_content_from_file(idx,
        	                                             'chroms_results_')
        self.assertTrue(chroms_content==chroms_content_from_file)
        self.click_the_reset_button()

    def save(self, idx):

        self.click_the_preview_button()
        preview_content=self.get_preview_content(idx)
        self.save_content_to_file(preview_content, idx, 'preview_results_')
        self.click_the_chroms_button()
        chroms_content=self.get_chroms_content(idx)
        self.save_content_to_file(chroms_content, idx, 'chroms_results_')
        self.download_file()
        #self.click_the_reset_button()

    def save_variants_results(self, data_defs, idx):

        self.fill_variants_form(data_defs)
        self.save(idx)
        self.execute(idx)

    def make_results_dir(self):
    	if not os.path.exists(os.path.dirname(
                VariantsTest.location + VariantsTest.results_dir)):
            print 'dir does not exists'
            os.makedirs(os.path.dirname(
                VariantsTest.location +
                VariantsTest.results_dir))

    def run_variants_tests(self):
    	self.make_results_dir()
        data_defs=self.get_dictionary()
        for idx, line in enumerate(data_defs):
            print "idx", idx
            temp_data_defs = ast.literal_eval(line)
            self.save_variants_results(temp_data_defs, idx)

    def test_variants_with_predefined_values(self):

        self.browser.get(self.server_url)
        self.run_variants_tests()

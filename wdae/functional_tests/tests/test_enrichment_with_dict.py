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


class EnrichmentTest(FunctionalTest):

    location = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
    results_dir = '/results_dir/enrichment/'
    tests_defs = 'data_dict_enrichment.txt'

    def get_dictionary(self):
        text_file = open(os.path.join(
            EnrichmentTest.location, EnrichmentTest.tests_defs), 'r')
        data = text_file.readlines()
        text_file.close()
        return data

    def select_denovo_gene_set(self, data):
        base_select(self).select_method_by_value(
            "denovoStudiesInGeneSet", data['geneStudy'])

    def select_gene_set_main(self, data):

        base_select(self).select_method_by_value(
            "geneSet", data['geneSet'])
        if data['geneSet'] == 'denovo':
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

    def genes_radio_buttons(self, data):
        base_select(self).radio_button_select(data['genes'])
        if data['genes'] == 'Gene Sets':
            self.select_gene_set_main(data)
            self.select_gene_set_value(data)
        if data['genes'] == 'Gene Symbols':
            self.select_gene_symbols(data['geneSyms'])

    def select_gene_symbols(self, gene_list):

        gene_syms_radio = self.browser.find_element_by_id(
            "geneSymsRadio")
        gene_syms_radio.click()
        gene_syms_text_area = self.browser.find_element_by_id(
            "geneSyms")
        gene_syms_text_area.send_keys(gene_list)
        time.sleep(2)

    def wait_for_table(self):

        try:
            element = WebDriverWait(self.browser, 60).until(
                EC.presence_of_element_located((By.ID,
                                                "enrichmentTable"))
            )
        finally:
            pass

        time.sleep(2)

    def click_the_enrichment_test_button(self):

        preview_button = self.browser.find_element_by_id("downloadEnrichment")
        preview_button.click()
        self.wait_for_table()

    def get_enrichment_content(self, idx):

        preview_content = []
        temp = self.browser.find_elements_by_css_selector(
            "table#enrichmentTable > tbody > tr")
        for tr in temp:
            tds = tr.find_elements_by_css_selector('td')
            for td in tds:
                preview_content.append(td.text)
        return preview_content

    def generate_file(self, idx, type_of_data):
        return (EnrichmentTest.location + EnrichmentTest.results_dir +
                str(type_of_data) + str(idx) + '.txt')

    def save_content_to_file(self, data, idx, type_of_data):
        filename = self.generate_file(idx, type_of_data)
        f = open(os.path.join(filename), 'w+')
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

    def fill_variants_form(self, data_defs):

        self.genes_radio_buttons(data_defs)
        self.select_denovo_studies(data_defs)

    def read_content_from_file(self, idx, type_of_data):
        f = open(VariantsTest.location + VariantsTest.results_dir +
                 '/' + str(type_of_data) + str(idx) + '.txt', 'r')
        data = f.read()
        f.close()
        print ast.literal_eval(data)
        return ast.literal_eval(data)

    def execute(self, idx):

        # self.download_file()
        self.click_the_enrichment_test_button()
        enrichment_content = self.get_enrichment_content(idx)
        enrichment_content_from_file = self.read_content_from_file(idx,
                                                                'enrichment_results_')
        self.assertTrue(enrichment_content == enrichment_content_from_file)
        self.click_the_reset_button()

    def save(self, idx):

        self.click_the_enrichment_test_button()
        enrichment_content = self.get_enrichment_content(idx)
        self.save_content_to_file(enrichment_content, idx, 'enrichment_results_')
        # self.click_the_reset_button()

    def execute_variants(self, data_defs, idx):

        self.fill_variants_form(data_defs)
        self.execute(idx)

    def save_variants(self, data_defs, idx):

        self.fill_variants_form(data_defs)
        self.save(idx)

    def make_results_dir(self):
        if not os.path.exists(os.path.dirname(
                EnrichmentTest.location + EnrichmentTest.results_dir)):
            print 'dir does not exist'
            os.makedirs(os.path.dirname(
                EnrichmentTest.location +
                EnrichmentTest.results_dir))

    def run_enrichment_tests(self):
        data_defs = self.get_dictionary()
        for idx, line in enumerate(data_defs):
            print "idx", idx
            temp_data_defs = ast.literal_eval(line)
            self.execute_variants(temp_data_defs, idx)

    def save_enrichment_tests(self):
        self.make_results_dir()
        data_defs = self.get_dictionary()
        for idx, line in enumerate(data_defs):
            print "idx", idx
            temp_data_defs = ast.literal_eval(line)
            self.save_variants(temp_data_defs, idx)
            
    def wait_button_to_be_clickable(self):
		
	try:
            random_element = WebDriverWait(self.browser, 10).until(
            	     EC.element_to_be_clickable((
		                                 By.CSS_SELECTOR,
		                                 "#enrichment > a"))
                     )
        finally:
            pass

    def test_enrichment_with_predefined_values(self):

        self.browser.get(self.server_url)
        self.wait_button_to_be_clickable()
        enrichment_button_elem = self.browser.find_element_by_css_selector(
	       "#enrichment > a")
        enrichment_button_elem.click()
        time.sleep(3)
        try:
              WebDriverWait(self.browser, 10).until(
                      EC.presence_of_element_located((By.ID, 
                                      "downloadEnrichment"))
			)
        finally:
        	pass
        self.save_enrichment_tests()


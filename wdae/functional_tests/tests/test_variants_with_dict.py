from .base import FunctionalTest
from .base_variants import select_method, select_method_by_value, \
    type_method, radio_button_select

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


class VariantsTest(FunctionalTest):

    location = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
    results_dir = '/results_dir/variants/'
    tests_defs = 'data_dict.txt'

    def get_dictionary(self):
        text_file = open(os.path.join(
            VariantsTest.location, 'data_dict.txt'), 'r')
        data = text_file.readlines()
        text_file.close()
        return data





    def generate_file(self, idx, type_of_data):
        return (VariantsTest.location + VariantsTest.results_dir +
                str(type_of_data) + str(idx) + '.txt')

    def save_content_to_file(self, data, idx, type_of_data):
        filename = self.generate_file(idx, type_of_data)
        f = open(os.path.join(filename), 'w+')
        # f.write(str([str(x) for x in data]))
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
        f = open(VariantsTest.location + VariantsTest.results_dir +
                 '/' + str(type_of_data) + str(idx) + '.txt', 'r')
        data = f.read()
        f.close()
        print ast.literal_eval(data)
        return ast.literal_eval(data)

    def execute(self, idx):

        # self.download_file()
        self.click_the_preview_button()
        preview_content = self.get_preview_content(idx)
        preview_content_from_file = self.read_content_from_file(idx,
                                                                'preview_results_')
        self.assertTrue(preview_content == preview_content_from_file)
        self.click_the_chroms_button()
        chroms_content = self.get_chroms_content(idx)
        chroms_content_from_file = self.read_content_from_file(idx,
                                                               'chroms_results_')
        self.assertTrue(chroms_content == chroms_content_from_file)
        self.click_the_reset_button()

    def save(self, idx):

        self.click_the_preview_button()
        preview_content = self.get_preview_content(idx)
        self.save_content_to_file(preview_content, idx, 'preview_results_')
        self.click_the_chroms_button()
        chroms_content = self.get_chroms_content(idx)
        self.save_content_to_file(chroms_content, idx, 'chroms_results_')
        self.download_file()
        # self.click_the_reset_button()

    def save_variants_results(self, data_defs, idx):

        self.fill_variants_form(data_defs)
        self.save(idx)
        self.execute(idx)

    def make_results_dir(self):
        if not os.path.exists(os.path.dirname(
                VariantsTest.location + VariantsTest.results_dir)):
            print 'dir does not exist'
            os.makedirs(os.path.dirname(
                VariantsTest.location +
                VariantsTest.results_dir))

    def run_variants_tests(self):
        self.make_results_dir()
        data_defs = self.get_dictionary()
        for idx, line in enumerate(data_defs):
            print "idx", idx
            temp_data_defs = ast.literal_eval(line)
            self.save_variants_results(temp_data_defs, idx)

    def test_variants_with_predefined_values(self):

        self.browser.get(self.server_url)
        self.run_variants_tests()

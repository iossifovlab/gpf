from .base import FunctionalTest

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import unittest
import os
import time

class CheckPagesTest(FunctionalTest):


    def test_landing_page(self):

        # Edith has heard about a cool new online to-do app. She goes
        # to check out its homepage
        self.browser.get(self.server_url)

        # She notices the page title and header mention to-do lists
        self.assertIn('Seqpip', self.browser.title)

        title_elem = self.browser.find_element_by_css_selector(
            "#pageContent > div.container.container-form > h1")
        self.assertIn("Get Variants", title_elem.text.decode())

    def test_study_summaries_page(self):
        self.browser.get(self.server_url)
        summaries_button_elem = self.browser.find_element_by_css_selector(
            "#summaries > a")
        summaries_button_elem.click()
        
        try:
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "summariesTable"))
            )
        finally:
            pass

    def test_reports_page(self):
        self.browser.get(self.server_url)
        reports_button_elem = self.browser.find_element_by_css_selector(
            "#reports > a")
        reports_button_elem.click()
        
        try:
            element = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#sammyContainer > div > h1"))
            )
            self.assertIn("Variant report", element.text.decode())
        finally:
            pass

    def test_enrichment_page(self):
        self.browser.get(self.server_url)
        enrichment_button_elem = self.browser.find_element_by_css_selector(
            "#enrichment > a")
        enrichment_button_elem.click()
        
        try:
            element = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                "#pageContent > div > h1"))
            )
            self.assertIn("Enrichment", element.text.decode())
        finally:
            pass
        
        
class VariantsSimpleTest(FunctionalTest):
    def _checkdownload(self, filename):
        savedir = "/tmp"
        max_mtime = 0
        newest_file = ""

        path = os.path.join(savedir, filename)
        try:
            mtime = os.path.getmtime(path)
            if mtime > max_mtime:
                newest_file = path
                max_mtime = mtime
        except OSError:
            pass  # File probably just moved/deleted
        return newest_file        

    def _waitdownload(self, filename):
        self._checkdownload(filename)

    def setUp(self):
        super(VariantsSimpleTest, self).setUp()
        filename = "/tmp/unruly.csv"
        os.path.exists(filename) and os.remove(filename)


    def test_preview_page(self):

        self.browser.get(self.server_url)

        title_elem = self.browser.find_element_by_css_selector(
            "#pageContent > div.container.container-form > h1")
        self.assertIn("Get Variants", title_elem.text.decode())

        preview_button = self.browser.find_element_by_css_selector(
            "#previewBtn")
        preview_button.click()
        
        try:
            element = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                "#previewTable"))
            )
            first_family = self.browser.find_element_by_css_selector(
                "#previewTable > tbody > tr:nth-child(1) > td:nth-child(1)")

            self.assertIn("11268", first_family.text.decode())
        finally:
            pass

    def test_chromes_page(self):

        self.browser.get(self.server_url)

        title_elem = self.browser.find_element_by_css_selector(
            "#pageContent > div.container.container-form > h1")
        self.assertIn("Get Variants", title_elem.text.decode())

        chromes_button = self.browser.find_element_by_css_selector(
            "#chromsBtn")
        chromes_button.click()
        
        try:
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                "#preview > svg"))
            )
            first_chrome = self.browser.find_element_by_css_selector(
                "#preview > svg > svg > g > text:nth-child(2)")

            self.assertIn("1", first_chrome.text.decode())
        finally:
            pass


    def test_download_button(self):

        self.browser.get(self.server_url)

        title_elem = self.browser.find_element_by_css_selector(
            "#pageContent > div.container.container-form > h1")
        self.assertIn("Get Variants", title_elem.text.decode())

        download_button = self.browser.find_element_by_css_selector(
            "#submitBtn")
        download_button.click()
        
        time.sleep(2.0)
        unruly_csv = os.path.join(self.download_dir, "unruly.csv")
        self.assertTrue(os.path.exists(unruly_csv))
        self.assertTrue(os.path.isfile(unruly_csv))
                        

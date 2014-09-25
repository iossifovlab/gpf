from .base import FunctionalTest

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import unittest


class NewVisitorTest(FunctionalTest):

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
            element = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "summariesTable"))
            )
        finally:
            pass
        

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import unittest

class FirstTest(unittest.TestCase): 

    def setUp(self): 
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)
        self.browser.get('http://localhost:8000')

    def tearDown(self): 
        self.browser.quit()

    def test_effect_types(self):
    	
    	# User select the 'frame-shift' effect type
    	effect_type = Select(self.browser.find_element_by_id('effectType'))
    	effect_type.select_by_value('frame-shift')

    	# User clicks on the preview button
        preview_btn = self.browser.find_element_by_id('previewBtn')
        preview_btn.click()

		# User finds the neccessary data
        table = self.browser.find_element_by_id('previewTable')
        rows = table.find_elements_by_tag_name('tr')
        for x in range(1, len(rows) - 200):
        	row = rows[x]
        	columns = row.find_elements_by_tag_name('td')
        	effect = columns[5]
        	if "frame-shift" not in effect.text:
        		self.fail('No frame shift')

    def test_regions_validation(self): 

        # User finds the regions tab and click on it
        regions = self.browser.find_element_by_id('regionsRadio')
        regions.click()

        # User fills in wrong data in the region text area
        gene_region = self.browser.find_element_by_id('geneRegion')
        gene_region.send_keys('wrong info')

        # User clicks on the preview button and no preview is provided
        preview_btn = self.browser.find_element_by_id('previewBtn')
        preview_btn.click()
        table_container = self.browser.find_element_by_id('preview')
        self.assertEquals(table_container.text, '')

        # User deletes the data in the region text area
        gene_region.clear()

        # User clicks on the preview button again
        preview_btn.click()

        # User fills in the right formatted data
        gene_region.send_keys('4:57889615-60000000')

        # User clicks on the preview button again
        preview_btn.click()

        # User finds the neccessary data
        table = self.browser.find_element_by_id('previewTable')
        rows = table.find_elements_by_tag_name('tr')
        self.assertNotEquals(len(rows), 0)

if __name__ == '__main__': 
    unittest.main() 
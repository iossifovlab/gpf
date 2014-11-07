from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


import time

class base_select(object):
	
	def __init__(self,test):
		self.test = test
	
	def select_method(self,select_target,select_name):
		
		time.sleep(1)
		select_target_variable = Select(
			self.test.browser.find_element_by_id(select_target))
		select_target_variable.select_by_visible_text(
			select_name)
		
		print select_target ," : " , select_name
		time.sleep(2)
		
	def select_method_by_value(self,select_target,select_value):
		
		time.sleep(1)
		select_target_variable = Select(
			self.test.browser.find_element_by_id(select_target))
		select_target_variable.select_by_value(
			select_value)
		
		print select_target ," : " , select_value
		time.sleep(2)
		
	def type_method(self,type_target,text):
		
		time.sleep(1)
		try:
			element = WebDriverWait(self.test.browser, 10).until(
				EC.presence_of_element_located(
					(By.ID,type_target)))
		finally: 
			pass
		
		type_target_variable = self.test.browser.find_element_by_id(type_target)
		type_target_variable.clear()
		type_target_variable.send_keys(text)
		
		print type_target, " : " , text
		time.sleep(2)
		
	def radio_button_select(self,radio_button_target):
		
		time.sleep(1)
		self.test.browser.find_element_by_xpath("//div[@class='controls form-inline']/input[@value='"+radio_button_target+"']").click()
		print radio_button_target
		time.sleep(2)
		

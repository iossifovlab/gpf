from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def select_method(browser, select_target,select_name):
    select_target_variable = Select(
        browser.find_element_by_id(select_target))
    select_target_variable.select_by_visible_text(
        select_name)
    
    print select_target ," : " , select_name
    
def select_method_by_value(browser, select_target, select_value):
    print select_target ," : " , select_value

    select_target_variable = Select(
        browser.find_element_by_id(select_target))
    select_target_variable.select_by_value(
        select_value)
    

    
def type_method(browser, type_target,text):
    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located(
                (By.ID,type_target)))
    finally: 
        pass
        
    type_target_variable = browser.find_element_by_id(type_target)
    type_target_variable.clear()
    type_target_variable.send_keys(text)
    
    print type_target, " : " , text


def radio_button_select(browser, radio_button_target):
    print(radio_button_target)
    xpath = "//div[@class='controls form-inline']/input[@value='%s']" % radio_button_target
    browser.find_element_by_xpath(xpath).click()

	
		

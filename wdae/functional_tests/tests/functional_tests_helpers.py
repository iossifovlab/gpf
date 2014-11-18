from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

import time
import ast

from base_variants import select_method, select_method_by_value, \
    type_method, radio_button_select


def select_denovo_gene_set(browser, data):
    select_method_by_value(browser,
        "denovoStudiesInGeneSet", data['geneStudy'])

def select_gene_set_main(browser, data):
    select_method_by_value(browser,
                           "geneSet", data['geneSet'])
    if data['geneSet'] == 'denovo':
        select_denovo_gene_set(browser, data)

def select_gene_set_value(browser, data):

    gene_set_value_option = browser.find_element_by_xpath(
        "//div[@id='preloadedBtn']/button")
    gene_set_value_option.click()
    
    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".ui-autocomplete")))
    finally:
        pass
    selected_element = lambda: browser.find_element_by_xpath(
        "//ul[@class='ui-autocomplete " +
        "ui-front ui-menu ui-widget ui-widget-content " +
        "ui-corner-all']/li/a[contains(text(),'" +
        data['geneTerm'] + "')]"
    )

    print("Random gene set value : %s" % selected_element().text)
    selected_element().click()

def select_denovo_studies(browser, data):
    select_method(browser,
                  "denovoStudies", data['denovoStudies'])

def select_in_child(browser, data):
    select_method(browser, "inChild", data['inChild'])

def select_effect_type(browser, data):
    select_method(browser, "effectType", data['effectTypes'])

def select_variant_type(browser, data):
    select_method(browser,
                  "variants", data['variantTypes'])

def genes_radio_buttons(browser, data):
    print(data['genes'])
    radio_button_select(browser, data['genes'])
    if data['genes'] == 'Gene Sets':
        select_gene_set_main(browser, data)
        select_gene_set_value(browser, data)
    if data['genes'] == 'Gene Symbols':
        select_gene_symbols(browser, data['geneSyms'])

def select_rare_max(browser, data):
    type_method(browser, "max", data['popFrequencyMax'])

def select_rare_interval(browser, data):
    type_method(browser, "min", data['popFrequencyMin'])
    type_method(browser, "max", data['popFrequencyMax'])
    
def select_rarity_radio_buttons(browser, data):
    browser.find_element_by_id(data['rarity']).click()
    if data['rarity'] == "rare":
        select_rare_max(browser, data)
    if data['rarity'] == "interval":
        select_rare_interval(browser, data)

def select_transmitted_studies(browser, data):
    select_method(browser, "transmittedStudies",
                  data['transmittedStudies'])
    rarity_div = browser.find_element_by_id("rarity")
    if rarity_div.is_displayed():
        select_rarity_radio_buttons(browser, data)

def select_gene_symbols(browser, gene_list):
    gene_syms_radio = browser.find_element_by_id(
        "geneSymsRadio")
    gene_syms_radio.click()
    gene_syms_text_area = browser.find_element_by_id(
        "geneSyms")
    gene_syms_text_area.send_keys(gene_list)

def select_family_ids(browser, family_list):
    family_ids_radio = browser.find_element_by_id(
        "familyIdsRadio")
    family_ids_radio.click()
    family_ids_text_area = browser.find_element_by_id(
        "familyIds")
    family_ids_text_area.send_keys(family_list)

def select_race_option(browser, data):
    select_method(browser, "race", data['familyRace'])

def select_verbal_iq_low(browser, data):
    type_method(browser, "verbalIQLow",
                data['familyVerbalIqLo'])

def select_verbal_iq_high(browser, data):
    type_method(browser, "verbalIQHigh",
                data['familyVerbalIqHi'])

def select_quad_trio(browser, data):
    select_method(browser, "quad-trio",
                  data['familyQuadTrio'])

def select_proband_gender(browser, data):
    select_method(browser, "probandGender",
                  data['familyPrbGender'])

def select_sibling_gender(browser, data):
    select_method(browser, "siblingGender",
                  data['familySibGender'])

    
def select_family_advanced_options(browser, data):
    select_race_option(browser, data)
    select_verbal_iq_low(browser, data)
    select_verbal_iq_high(browser, data)
    select_quad_trio(browser, data)
    select_proband_gender(browser, data)
    select_sibling_gender(browser, data)

def select_families(browser, data):
    browser.find_element_by_xpath(
        "//div[@class='controls form-inline']//input[@value='" +
        data['families'] + "']").click()
    if data['families'] == "advanced":
        select_family_advanced_options(browser, data)
    if data['families'] == 'familyIds':
        select_family_ids(browser, data['familyIds'])

def wait_for_table(browser, timeout=300):
    element = None
    try:
        element = WebDriverWait(browser,timeout).until(
            EC.presence_of_element_located((By.ID,
                                            "previewTable"))
        )
    finally:
        pass
    return element
        
def wait_for_chroms(browser, timeout=300):
    element = None
    try:
        element = WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            "div#preview > svg"))
        )
    finally:
        pass
    return element

def click_the_preview_button(browser):
    preview_button = browser.find_element_by_id("previewBtn")
    preview_button.click()
    wait_for_table(browser)

def click_the_chroms_button(browser):
    preview_button = browser.find_element_by_id("chromsBtn")
    preview_button.click()
    wait_for_chroms(browser)


def get_preview_content(browser):
    preview_content = []
    table = browser.find_elements_by_css_selector(
        "table#previewTable > tbody > tr")
    for tr in table:
        tds = tr.find_elements_by_css_selector('td')
        for td in tds:
            preview_content.append(td.text)
    return preview_content

def get_chroms_content(browser):
    chroms_content = []
    chroms = browser.find_element_by_css_selector(
        "div#preview > svg > svg > g")
    temp_rect = chroms.find_elements_by_css_selector("rect")
    temp_path = chroms.find_elements_by_css_selector("path")
    
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


    
def fill_variants_form(browser, data):
    genes_radio_buttons(browser, data)
    select_denovo_studies(browser, data)
    select_transmitted_studies(browser, data)
    select_in_child(browser, data)
    select_variant_type(browser, data)
    select_effect_type(browser, data)
    select_families(browser, data)

def load_dictionary(filename):
    text_file = open(filename, 'r')
    data = text_file.readlines()
    data_dict = []
    for dd in data:
        data_dict.append(ast.literal_eval(dd))
    text_file.close()
    return data_dict


def start_browser():
    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2)
    profile.set_preference('browser.download.manager.showWhenStarting',
                           False)
    profile.set_preference('browser.download.dir', "/tmp")
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk',
                           'text/csv')
    
    browser = webdriver.Firefox(profile)
    browser.implicitly_wait(5)

    return browser

def stop_browser(browser):
    browser.quit()


if __name__ == "__main__":
    data = load_dictionary("data_dict.txt")
    browser = start_browser()
    
    for dd in data:
        print(dd, type(dd))
        browser.get("http://seqpipe-vm.setelis.com/dae")
        fill_variants_form(browser, dd)

    stop_browser(browser)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

import time
import ast
import tempfile
import os
import sys
import shutil
import difflib
import traceback


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
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located(
            (By.ID,type_target)))
        
    type_target_variable = browser.find_element_by_id(type_target)
    type_target_variable.clear()
    type_target_variable.send_keys(text)
    
    print type_target, " : " , text


def radio_button_select(browser, radio_button_target):
    print(radio_button_target)
    xpath = "//div[@class='controls form-inline']/input[@value='%s']" % radio_button_target
    browser.find_element_by_xpath(xpath).click()



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
    
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".ui-autocomplete")))

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
    radio_button_select(browser, data['genes'])
    if data['genes'] == 'Gene Sets':
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID,
                                            "geneSet"))
        )
        
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

def wait_for_preview(browser, timeout=300):
    element = WebDriverWait(browser,timeout).until(
        EC.presence_of_element_located((By.ID,
                                        "previewTable"))
    )
    return element
        
def wait_for_chroms(browser, timeout=300):
    element = WebDriverWait(browser, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,
                                        "div#preview > svg"))
    )
    return element

def wait_for_download(browser, ddir, filename='unruly.csv', timeout=300):
    fullname = os.path.join(ddir, filename)

    while not os.path.exists(fullname):
        print("waiting for %s" % fullname)
        time.sleep(2)
    
    file_size_stored = os.stat(fullname).st_size

    while True:
        try:
            file_size_current = os.stat(fullname).st_size
            if file_size_stored == file_size_current:
                break
            else:
                file_size_stored = file_size_current
                print(fullname, file_size_stored)
                time.sleep(2)
        except: 
            pass

    return fullname

def click_the_preview_button(browser):
    preview_button = browser.find_element_by_id("previewBtn")
    preview_button.click()
    wait_for_preview(browser)
    return get_preview_content(browser)

def click_the_chroms_button(browser):
    preview_button = browser.find_element_by_id("chromsBtn")
    preview_button.click()
    wait_for_chroms(browser)
    return get_chroms_content(browser)


def click_the_download_button(browser, ddir):
    download_button = browser.find_element_by_id(
        "submitBtn")
    download_button.click()
    filename = wait_for_download(browser, ddir)
    print(filename)
    return filename

def save_preview_content(rdir, idx, content):
    fullname = os.path.join(rdir, "preview_result_%03d.out" % idx)
    with open(fullname, "w") as f:
        f.write(content)

def save_request_content(rdir, idx, content):
    fullname = os.path.join(rdir, "request_%03d.out" % idx)
    with open(fullname, "w") as f:
        f.write(str(content))

def save_chroms_content(rdir, idx, content):
    fullname = os.path.join(rdir, "chroms_result_%03d.out" % idx)
    with open(fullname, "w") as f:
        f.write(content)

def save_download_content(rdir, idx, content):
    fullname = os.path.join(rdir, "unruly_result_%03d.out" % idx)
    print("moving %s -> %s" % (content, fullname))
    shutil.move(content, fullname)

def _equal(orig, content):
    if orig != content:
        print("************************************************************")
        ostr = orig.splitlines(1)
        cstr = content.splitlines(1)
        diff = difflib.context_diff(ostr, cstr)
        for line in diff:
            print >>sys.stderr, line
        return False
    return True
    
def assert_request_content(rdir, idx, content):
    fullname = os.path.join(rdir, "request_%03d.out" % idx)
    with open(fullname, "r") as f:
        orig = f.read()
    
    assert _equal(str(content), orig)

def assert_preview_content(rdir, idx, content):
    fullname = os.path.join(rdir, "preview_result_%03d.out" % idx)
    with open(fullname, "r") as f:
        orig = f.read()
    assert _equal(content, orig)

def assert_chroms_content(rdir, idx, content):
    fullname = os.path.join(rdir, "chroms_result_%03d.out" % idx)
    with open(fullname, "r") as f:
        orig = f.read()
    assert _equal(content, orig)

def assert_download_content(rdir, idx, content):
    fullname = os.path.join(rdir, "unruly_result_%03d.out" % idx)
    with open(fullname, 'r') as f:
        orig = f.read()
    with open(content, 'r') as f:
        scont = f.read()
    assert _equal(orig, scont)

def get_preview_content(browser):
    table = browser.find_element_by_id("previewTable")
    return table.get_attribute('innerHTML')
    
def get_chroms_content(browser):
    chroms = browser.find_element_by_css_selector(
        "div#preview > svg")
    return chroms.get_attribute('innerHTML')
    
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
    tmpdir = tempfile.mkdtemp()
    
    profile.set_preference('browser.download.dir', tmpdir)
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk',
                           'text/csv')
    
    browser = webdriver.Firefox(profile)
    browser.implicitly_wait(5)

    return (browser, tmpdir)

def stop_browser(browser):
    browser.quit()

def ensure_directory(dirname):
    try:
        os.makedirs(dirname)
    except Exception:
        pass


def save_results_mode(server_url, frequests, rdir):
    ensure_directory(rdir)

    data = load_dictionary(frequests)
    (browser, ddir) = start_browser()

    for (idx, request) in enumerate(data):
        browser.get(server_url)
        save_request_content(rdir, idx, request)
        fill_variants_form(browser, request)

        preview = click_the_preview_button(browser)
        save_preview_content(rdir, idx, preview)
        
        chroms = click_the_chroms_button(browser)
        save_chroms_content(rdir, idx, chroms)
        
        down = click_the_download_button(browser, ddir)
        save_download_content(rdir, idx, down)

    stop_browser(browser)
    shutil.rmtree(ddir)

def test_results_mode(server_url, frequests, rdir):
    data = load_dictionary(frequests)
    (browser, ddir) = start_browser()

    for (idx, request) in enumerate(data):
        try:
            browser.get(server_url)
            fill_variants_form(browser, request)
        
            assert_request_content(rdir, idx, request)
            
            preview = click_the_preview_button(browser)
            assert_preview_content(rdir, idx, preview)
            
            chroms = click_the_chroms_button(browser)
            assert_chroms_content(rdir, idx, chroms)
            
            down = click_the_download_button(browser, ddir)
            assert_download_content(rdir, idx, down)
        except AssertionError:
            print >>sys.stderr, request
            print >>sys.stderr, traceback.format_exc()
            print >>sys.stderr, sys.exc_info()[0]
        
    stop_browser(browser)
    shutil.rmtree(ddir)
        
if __name__ == "__main__":
    
    rdir = "./results"
    frequests = "data_dict.txt"
    server_url = "http://seqpipe-vm.setelis.com/dae"

    # save_results_mode(server_url, frequests, rdir)
    test_results_mode(server_url, frequests, rdir)
    
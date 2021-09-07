# -*- coding: utf-8 -*-
"""
Created on Thu Nov  5 10:01:23 2020
"""

import pandas as pd
import logging  # Added by Mrityunjay on 19th July
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime  # Added by Kajal on 27th Aug
from PIL import Image, ImageDraw, ImageFont
import os
import re
#from lxml import html
#import requests
#from selenium.common.exceptions import TimeoutException, NoAlertPresentException
#from selenium.webdriver.common.alert import Alert
#import pdb

url='http://10.144.97.109:9004/cwf/login'  # OC URL
#url='http://10.135.34.37:8111/siteforge/jsp/login.jsp'# SF ST URL
#url='http://10.135.26.21:8079/siteforge/jsp/login.jsp'# SF SIT URL
#url='http://10.144.96.183:7532/OPI/'# GI GUI URL
parent_dir = os.getcwd()  # Get current working directory
now = datetime.now()  # Get current date and time
current_time = now.strftime("%d%m%Y_%H%M%S") # Convert current date and time to string

def open_app(url):
    '''To open particular system URL'''
    global driver
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(url)


def enable_log(log_file):
    '''Function definition to set log handler'''
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(filename=os.path.join(parent_dir, 'logs', log_file),
                        format='%(asctime)s %(message)s',
                        filemode='w')  # Added for logging information.
    logger = logging.getLogger()  # Creating logger object
    logger.setLevel(logging.DEBUG)  # Setting the threshold of logger to DEBUG


screenshots_list = [] # Storing list of all screenshot pngs captured
def takeScreenshot(ind):
    '''function used to take screenshots for each event'''  
    logging.info(f"Screenshots captured!")
    filename = "temp/"+scenario_to_run+"_"+str(ind)+".png"
    driver.get_screenshot_as_file(filename)
    global screenshots_list
    image = Image.open(filename)
    image = image.convert("RGB")
    screenshots_list.append(image)


def pass_fail_watermark(result_type, last_image):
    '''Create Pass/Fail Watermark on last_image based on result_type'''
    im = last_image
    width, height = im.size
    draw = ImageDraw.Draw(im)
    text = result_type
    font = ImageFont.truetype('arial.ttf', 36)
    textwidth, textheight = draw.textsize(text, font)
    # calculate the x,y coordinates of the text
    margin = 10
    x = width/2 - margin
    y = height/2 - margin
    # Draw watermark in the centre of the page
    if result_type == 'Pass':
        fill = (0, 128, 0)
    else:
        fill = (255, 0, 0)
    draw.text((x, y), text, font=font, fill=fill)
    # draw watermark in the bottom right corner
    #x = width - textwidth - margin
    #y = height - textheight - margin
    #draw.text((x, y), text, font=font)
    im.save("temp/"+scenario_to_run+"_"+"lastImage"+".png") # Save watermarked image
    return im


def testResultPngToPdf(result_type):
    '''Function call to make pdf for all screen shots taken during execution'''
    logging.info(f"Total Screenshots captured : {len(screenshots_list)}")
    screenshots_list[-1] = pass_fail_watermark(result_type, screenshots_list[-1])
    pdf_filename = ("TestResults/"+scenario_to_run+"_" +current_time+"_"+result_type+".pdf")
    screenshots_list[0].save(pdf_filename, "PDF", resolution=100.0,
                            save_all=True, append_images=screenshots_list[1:])
    screenshots_list.clear()


path_scenario = './data/Scenario.csv'  # Path to fetch Scenario file
scenario = pd.read_csv(path_scenario)  # Read Scenario.csv file
def scenario_file_path():
    '''Function definition to fetch the scenario with value as "Y" from csv'''
    scenario_to_run_list = []
    for i in scenario.index:
        if scenario['Flag'][i] == 'Y':
            scenario_to_run_list.append(scenario['Scenario'][i])
        else:
            logging.info(f"No scenarios found to be run:---")
    return scenario_to_run_list


def construct_xpath(xpath):
    '''Create final xpath to be passed'''
    x_split = xpath.split('("')
    x_split2 = x_split[1].split('"))')
    final_xpath = x_split2[0]
    return final_xpath


logging.info(f'Scenarios under execution : {scenario_file_path()}')

get_text = ''
scenario_to_run = ''

def run_script(current_scenario):
    '''Function definition to execute script of current scenario'''
    global get_text
    global scenario_to_run
    scenario_to_run = current_scenario
    logging.info(f"Current scenario executing::: {scenario_to_run}")
    data_path = ('./data/'+scenario_to_run+'.csv')
    log_path = (scenario_to_run+'_'+current_time+'.log')
    logging.info(f"data_path::: {data_path}")
    logging.info(f"log_path::: {log_path}")
    df = pd.read_csv(data_path)
    log_file = log_path
    logging.info(f"log file::: {log_file}")
    enable_log(log_file)
    # Iterate the csv file for Step by Step execution of Events
    for ind in df.index:
        logging.info(f"*** Executing step {ind+1} ***")
        logging.info(f"Step Executed : {df['Step'][ind]}")
        # Event used to click on elements
        if df['Event'][ind] == "click":
            final_xpath = construct_xpath(df['XPATH'][ind])
            identifier = '"'+final_xpath+'"'
            logging.info(f"identifier:::: {identifier}")
            try:
                # Wait until element or xpath is present on webpage
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, final_xpath)))
                element.click()
            except:
                # Providing time delay until xpath is available on page
                print('im here')
                time.sleep(5)
                WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_xpath(final_xpath)).click()
            takeScreenshot(ind)  # Function call for taking screenshots
        # Event used to send input to elements    
        elif df['Event'][ind] == "send_key":
            if get_text != "":
                if df['Step'][ind] == "Enter Service Order ID":
                    user_input = get_text # SO ID fetched from previous scenario execution
                    final_xpath = construct_xpath(df['XPATH'][ind])
                    logging.info(f"user input:: {user_input}")
                    identifier = '"'+final_xpath+'"'
                    logging.info(f"identifier:::: {identifier}")
                    try:
                        # Wait until element or xpath is present on webpage
                        element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, final_xpath)))
                        element.send_keys(user_input) 
                    except:
                        # Providing time delay until xpath is available on page
                        time.sleep(7)
                        WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_xpath(final_xpath)).send_keys(user_input)
                    takeScreenshot(ind)  # Function call for taking screenshots
                else:
                    final_xpath = construct_xpath(df['XPATH'][ind])
                    user_input = df['Data'][ind]
                    logging.info(f"user input:: {user_input}")
                    identifier = '"'+final_xpath+'"'
                    logging.info(f"identifier:::: {identifier}")
                    try:
                        # Wait until element or xpath is present on webpage
                        element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, final_xpath)))
                        element.send_keys(user_input) 
                    except:
                        # Providing time delay until xpath is available on page
                        time.sleep(7)
                        WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_xpath(final_xpath)).send_keys(user_input)
                    takeScreenshot(ind)  # Function call for taking screenshots
            else:
                final_xpath = construct_xpath(df['XPATH'][ind])
                user_input = df['Data'][ind]
                logging.info(f"user input:: {user_input}")
                identifier = '"'+final_xpath+'"'
                logging.info(f"identifier:::: {identifier}")
                try:
                    # Wait until element or xpath is present on webpage
                    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, final_xpath)))
                    element.send_keys(user_input) 
                except:
                    # Providing time delay until xpath is available on page
                    time.sleep(7)
                    WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_xpath(final_xpath)).send_keys(user_input)
                takeScreenshot(ind)  # Function call for taking screenshots
        # Event used to press Keyboard's key 'ENTER'
        elif df['Event'][ind] == "keypress":
            logging.info(f"inside key press:---")
            time.sleep(5)
            chains = ActionChains(driver)
            chains.send_keys(Keys.ENTER)
            chains.perform()
            time.sleep(5)
            takeScreenshot(ind)  # Function call for taking screenshots
        # Event used to Scroll Down the page    
        elif df['Event'][ind] == "scroll_down":  
            final_xpath = construct_xpath(df['XPATH'][ind])
            logging.info(f"execute scroll function:---")
            try:
                # Wait until element or xpath is present on webpage
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, final_xpath)))
                actions = ActionChains(driver)
                actions.move_to_element(element).click_and_hold().perform()
            except:
                # Providing time delay until xpath is available on page
                time.sleep(10)
                element = driver.find_element_by_xpath(final_xpath)
                actions = ActionChains(driver)
                actions.move_to_element(element).click_and_hold().perform()
        # Event used to search the element
        elif df['Event'][ind] == "search":  
            final_xpath = construct_xpath(df['XPATH'][ind])
            logging.info(f"X-path:::: {final_xpath}")
            try:
                # Wait until element or xpath is present on webpage
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, final_xpath)))
                element.click()
            except:
                # Providing time delay until xpath is available on page
                time.sleep(10)
                WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_xpath(final_xpath)).click()
            takeScreenshot(ind)  # Function call for taking screenshots
        # Event used to take some extra screenshots
        elif df['Event'][ind] == "screenshot":
            time.sleep(10)
            takeScreenshot(ind) # Function call for taking screenshots
        # Event used for refershing the page based on user input
        elif df['Event'][ind] == "refresh":
            user_input = df['Data'][ind]
            time.sleep(int(user_input))
            driver.refresh()
            takeScreenshot(ind)  # Function call for taking screenshots
        # Event used for uploading the files
        elif df['Event'][ind] == "upload":
            final_xpath = construct_xpath(df['XPATH'][ind])
            user_input = df['Data'][ind]
            file_path = os.path.join(parent_dir, 'data_upload', user_input)
            logging.info(f"user input:: {file_path}")
            try:
                # Wait until element or xpath is present on webpage
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, final_xpath)))
                element.send_keys(file_path)
            except:
                # Providing time delay until xpath is available on page
                time.sleep(5)
                WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_xpath(final_xpath)).send_keys(file_path)
            takeScreenshot(ind)  # Function call for taking screenshots
            time.sleep(5) # Extra time delay after uploading file 
        # Event used to Right click on specified path
        elif df['Event'][ind] == "right_click":
            final_xpath = construct_xpath(df['XPATH'][ind])
            logging.info(f"execute Right click:---")
            try:
                # Wait until element or xpath is present on webpage
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, final_xpath)))
                actions = ActionChains(driver)
                actions.context_click(element).perform()
            except:
                # Providing time delay until xpath is available on page
                time.sleep(5)
                element = driver.find_element_by_xpath(final_xpath)
                actions = ActionChains(driver)
                actions.context_click(element).perform()
            takeScreenshot(ind)  # Function call for taking screenshots
        elif df['Event'][ind] == "pixel_position":
            logging.info(f"execute pixel position event:---")
            try:
                # Wait until element or xpath is present on webpage
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                action = ActionChains(driver)
                action.move_to_element_with_offset(element, 790, 290)
                action.click()
                action.perform()
            except:
                # Providing time delay until xpath is available on page
                time.sleep(10)
                actions = ActionChains(driver)
                element = driver.find_element_by_tag_name('body')
                action = ActionChains(driver)
                action.move_to_element_with_offset(element, 790, 290)
                # action.context_click() # for testing purpose using context_click()
                action.click()
                action.perform()
        elif df['Event'][ind] == "SF_pixel_position":
            logging.info(f"execute pixel position event:---")
            try:
                # Wait until element or xpath is present on webpage
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                action = ActionChains(driver)
#                action.move_to_element_with_offset(element, 90, 351)
                action.click()
                action.context_click() # for testing purpose using context_click()
                action.perform()
                
            except:
                # Providing time delay until xpath is available on page
                time.sleep(10)
                actions = ActionChains(driver)
                element = driver.find_element_by_tag_name('body')
                action = ActionChains(driver)
                action.move_to_element_with_offset(element, 90, 351)
#                action.context_click() # for testing purpose using context_click()
                action.click()
                action.perform()
        # Event used to Wait for few seconds according to user input
        elif df['Event'][ind] == "wait":
            user_input = df['Data'][ind]
            time.sleep(int(user_input))
        # Event used to click on date from the datepicker
        elif df['Event'][ind] == "datepick":
            final_xpath = construct_xpath(df['XPATH'][ind])
            identifier = '"'+final_xpath+'"'
            logging.info(f"identifier:::: {identifier}")
            try:
                # Wait until element or xpath is present on webpage
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, final_xpath)))
                element.click()
            except:
                # Providing time delay until xpath is available on page
                time.sleep(5)
                WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_css_selector(final_xpath)).click() # ".dropdown-menu:nth-child(6) > .datepicker-days .active" # example css_selector for active date
            takeScreenshot(ind)  # Function call for taking screenshots
        # Event used to get text present on webpage
        elif df['Event'][ind] == "get_text":
            final_xpath = construct_xpath(df['XPATH'][ind])
            identifier = '"'+final_xpath+'"'
            logging.info(f"identifier:::: {identifier}")
            time.sleep(2)
            get_whole_text = WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_xpath(final_xpath)).text
            logging.info(f"Get text value:::: {get_whole_text}")
            get_SO = re.search("\d{9}", get_whole_text) # Get first SO ID displayed on dialog box
            get_text = get_SO.group()
            logging.info(f"final Get text value:::: {get_text}")
            # logging.info(f"Get text value:::: {get_whole_text}")
            # get_SO = re.findall(r"\b\d{9}\b", get_whole_text)
            # logging.info(f"final Get text value:::: {get_SO[0]}")
            # get_text = get_SO[0]
            # logging.info(f"final Get text value:::: {get_text}")
        
        elif df['Event'][ind] == "clear_field":
            logging.info(f"Inside clear field function")
            final_xpath = construct_xpath(df['XPATH'][ind])
            identifier = '"'+final_xpath+'"'
            logging.info(f"identifier:::: {identifier}")
            try:
                # Wait until element or xpath is present on webpage
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, final_xpath)))
                element.clear()
            except:
                # Providing time delay until xpath is available on page
                print('im here')
                time.sleep(5)
                element=WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_xpath(final_xpath))
                element.clear()
            takeScreenshot(ind)  # Function call for taking screenshots
        elif df['Event'][ind] == "sf_scroll":  
            final_xpath = construct_xpath(df['XPATH'][ind])
            logging.info(f"execute scroll function:---")
            try:
                # Wait until element or xpath is present on webpage
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, final_xpath)))
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", element)
            except:
                # Providing time delay until xpath is available on page
                time.sleep(10)
                element = driver.find_element_by_xpath(final_xpath)
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", element)
        else:
            logging.error(f"No record found:---")
    # Function call to make pdf for all screen shots taken during execution
    testResultPngToPdf(result_type='Pass')


scenariosToBeExecuted = scenario_file_path()
for i in scenariosToBeExecuted:
    open_app(url)
    try:
        run_script(i)  # Function call for execution of script
    except:
        logging.exception(f"Time Out Exception:---")
        testResultPngToPdf(result_type='Fail')
    #driver.close() #commnet for testing

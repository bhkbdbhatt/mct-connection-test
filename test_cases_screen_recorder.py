from collections import namedtuple
import subprocess
import json
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from locators import Locators  # Import the Locators class
import time
import logging
from pyscreenrec import ScreenRecorder  # Import the pyscreenrec library
from ScreenRecordingManager import ScreenRecorderManager, record_test
from datetime import datetime



# Define named tuples for better organization
DriverContext = namedtuple('DriverContext', ['agent_login_url_driver', 'chatbot_url_driver'])
UserContext = namedtuple('UserContext', ['username', 'password', 'country_code','lang_code', 'customer_service_utterance','site_reference'])

# Load country configuration from JSON file
def load_country_config(file_path='country_config_am.json'):
    with open(file_path,  encoding='utf-8') as config_file:
        return json.load(config_file)

# Centralized function to wait for an element to be present and then visible with a timeout
def wait_for_visible(driver, locator, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
        return driver.find_element(*locator)
    except TimeoutException:
        raise
    except Exception as e:
        raise

# Centralized function to click an element with retry logic
def click_with_retry(driver, locator, timeout=10, retries=6):
    for i in range(retries):
        try:
            wait_for_visible(driver, locator, timeout)
            driver.find_element(*locator).click()
            # driver.
            return
        except Exception as error:
            if i == retries - 1:
                pytest.fail(f"Failed to click {locator} after {retries} attempts: {error}")

# Function to wait for the chat response to be visible
def wait_for_chat_response(driver, expected_text, timeout=30):
    start_time = time.time()
    while True:
        try:
            response_element = wait_for_visible(driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]//div[@data-test-id="message-content"]'))
            response_text = response_element.text.strip()
            if expected_text in response_text:
                return response_text  # Return the response text if it matches
        except Exception:
            pass  # Ignore exceptions if the element is not found yet

        # Check if timeout has been reached
        if time.time() - start_time > timeout:
            raise AssertionError(f"Expected response not found within {timeout} seconds.")

        time.sleep(1)  # Wait a bit before trying again

def get_site_url(site_reference, country_code, lang_code, awb_number=None):
    base_url = f'https://ewfsit.dhl.com/{country_code}/{lang_code}'
    if site_reference == "Tracking Page" and awb_number:
        return f'{base_url}/tracking.html#/results?id={awb_number}'
    elif site_reference == "Contact Us":
        return f'{base_url}/help-and-support.html'
    elif site_reference == "HomePage":
        return f'{base_url}/home.html'
    else:
        return f'{base_url}/home.html#/createNewShipmentTab'
def setup_chat_environment(setup_driver):
    """Common setup function for chat environment initialization.
    Args:
        setup_driver: The setup_driver fixture providing driver and user contexts
    Returns:
        tuple: Contains agent_login_url_driver, chatbot_url_driver, and user context information
    """
    drivers, user_context = setup_driver  # Get the contexts
    agent_login_url_driver = drivers.agent_login_url_driver
    chatbot_url_driver = drivers.chatbot_url_driver
    username = user_context.username
    password = user_context.password
    country_code = user_context.country_code
    lang_code = user_context.lang_code
    CUSTOMER_SERVICE_UTTERANCE = user_context.customer_service_utterance

    common_login(agent_login_url_driver, username, password)

    site_url = get_site_url(user_context.site_reference, user_context.country_code, user_context.lang_code)
    chatbot_url_driver.get(site_url)
    click_with_retry(chatbot_url_driver, Locators.ACCEPT_ALL_BUTTON)

    chat_frame = wait_for_visible(chatbot_url_driver, Locators.CHAT_FRAME)
    chatbot_url_driver.switch_to.frame(chat_frame)

    return agent_login_url_driver, chatbot_url_driver, user_context

@pytest.fixture(scope="module")
def setup_driver():
    country_config = load_country_config()
    country_code = 'co'
    credentials = country_config[country_code]
    lang_code = credentials['langCodes'][1]  # Get the first language code


    CUSTOMER_SERVICE_UTTERANCE = country_config['translations']['customer_service'].get(lang_code, country_config['translations']['customer_service']['en'])

    site_reference = country_config[country_code]['site_reference']

    username = credentials.get('username')
    password = credentials.get('password')

    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument("--inprivate")
    edge_options.add_argument('--start-maximized')

    agent_login_url_driver = webdriver.Edge(options=edge_options)
    chatbot_url_driver = webdriver.Edge(options=edge_options)

    # Get the size of the screen
    screen_width = agent_login_url_driver.get_window_rect()['width']
    screen_height = agent_login_url_driver.get_window_rect()['height']

    # Set the size of each window to half of the screen width and full height
    agent_login_url_driver.set_window_size(screen_width // 2, screen_height)
    chatbot_url_driver.set_window_size(screen_width // 2, screen_height)

    # Position the first window on the left
    agent_login_url_driver.set_window_position(0, 0)

    # Position the second window on the right
    chatbot_url_driver.set_window_position(screen_width // 2, 0)

    
    # Create contexts
    drivers = DriverContext(agent_login_url_driver, chatbot_url_driver)
    user_context = UserContext(username, password, country_code,lang_code, CUSTOMER_SERVICE_UTTERANCE, site_reference)


    # Yield both contexts
    yield drivers, user_context

    agent_login_url_driver.quit()
    chatbot_url_driver.quit()
def common_login(agent_login_url_driver, username, password):
    agent_login_url_driver.get('https://verint-mct-test.prg-dc.dhl.com/login-service/login-page?redirect_uri=https%3A%2F%2Fverint-mct-test.prg-dc.dhl.com%3A443%2FGTConnect%2FUnifiedAcceptor%2FFrameworkDesktop.Main%3Fsso%3Dfalse&scope=openid+tags+context_entitlements+content_entitlements+em_api_access&client_id=default&tz=&sWidth=&sHeight=')

    wait_for_visible(agent_login_url_driver, Locators.USERNAME_FIELD).send_keys(username)
    wait_for_visible(agent_login_url_driver, Locators.PASSWORD_FIELD).send_keys(password)
    click_with_retry(agent_login_url_driver, Locators.LOGIN_BUTTON)

    try:
        # Check for the presence of the concurrent login form
        if wait_for_visible(agent_login_url_driver, Locators.CONCURRENT_LOGIN_FORM):
            continue_button = wait_for_visible(agent_login_url_driver, (By.ID, 'f5_btnContinue'))
            if continue_button:
                continue_button.click()
                time.sleep(2)
                wait_for_visible(agent_login_url_driver, Locators.OPT_REQUESTED_STATUS)
            else:
                select = Select(wait_for_visible(agent_login_url_driver, Locators.OPT_REQUESTED_STATUS))
                time.sleep(2)
                select.select_by_visible_text('Available')
    except TimeoutException:
        # If the concurrent login form is not visible, proceed directly to the select dropdown
        select = Select(wait_for_visible(agent_login_url_driver, Locators.OPT_REQUESTED_STATUS))
        time.sleep(2)
        select.select_by_visible_text('Available')

def finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver):
        # wait_for_visible(agent_login_url_driver, Locators.CUSTOMER_VALIDATION_TEXT_AND_BELOW)
        time.sleep(7)
        wait_for_visible(agent_login_url_driver, Locators.CUSTOMER_VALIDATION_TEXT)
        click_with_retry(agent_login_url_driver, Locators.END_CHAT_BUTTON)
        click_with_retry(agent_login_url_driver, Locators.CONFIRM_BUTTON)
        click_with_retry(agent_login_url_driver, Locators.CLOSE_CHAT_BUTTON)

        wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_END_MESSAGE)
        wait_for_visible(chatbot_url_driver, Locators.AGENT_LOGOUT_MESSAGE)

        # click_with_retry(agent_login_url_driver, (By.ID, 'f54_tabButton'))
        # click_with_retry(agent_login_url_driver, (By.XPATH, '//div[@id="innerForm111"]/div[5]')) Need to update as per
        # click_with_retry(agent_login_url_driver, (By.LINK_TEXT, 'LH - HO CHI MINH, VIETNAM (')) Need to be country Specific
        select = Select(wait_for_visible(chatbot_url_driver, Locators.OPT_REQUESTED_STATUS))
        select.select_by_visible_text('Not Available')
        click_with_retry(agent_login_url_driver, Locators.LOGOUT_BUTTON)
        click_with_retry(agent_login_url_driver, Locators.OK_BUTTON)

def finalize_chat(agent_login_url_driver, chatbot_url_driver):
        time.sleep(7)
        click_with_retry(agent_login_url_driver, Locators.END_CHAT_BUTTON)
        click_with_retry(agent_login_url_driver, Locators.CONFIRM_BUTTON)
        # click_with_retry(agent_login_url_driver, Locators.CLOSE_CHAT_BUTTON)
        click_with_retry(agent_login_url_driver, Locators.END_CHAT_SUBMIT_BUTTON)

        wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_END_MESSAGE)
        wait_for_visible(chatbot_url_driver, Locators.AGENT_LOGOUT_MESSAGE)

        # click_with_retry(agent_login_url_driver, (By.ID, 'f54_tabButton'))
        # click_with_retry(agent_login_url_driver, (By.XPATH, '//div[@id="innerForm111"]/div[5]')) Need to update as per
        # click_with_retry(agent_login_url_driver, (By.LINK_TEXT, 'LH - HO CHI MINH, VIETNAM (')) Need to be country Specific
        select = Select(wait_for_visible(chatbot_url_driver, Locators.OPT_REQUESTED_STATUS))
        select.select_by_visible_text('Not Available')
        click_with_retry(agent_login_url_driver, Locators.LOGOUT_BUTTON)
        click_with_retry(agent_login_url_driver, Locators.OK_BUTTON)

@pytest.mark.checkpoint("MCT Drop off with Customer Service Utterance")
@record_test(fps=30)
def test_customer_service_utterance(setup_driver):
    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)
    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    # Continue with other interactions if necessary
    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(5)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("testcustomerservice")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for PL Checkpoint with valid Account Number")
@record_test(fps=30)
def test_dhl_automation_PL_valid_account_number(setup_driver):
    chatbot_url_driver, agent_login_url_driver,user_context  = setup_chat_environment(setup_driver)

    # Enter Air Way Bill for PL
    air_way_bill = "AWB-PL-TEST"
    air_way_bill_number = "1775460934"
    print(f"Entering Air Way Bill: {air_way_bill} with {air_way_bill_number}for checkpoint: PL")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    # Continue with other interactions if necessary
    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    # time.sleep(3)
    # Add any additional steps specific to the PL test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    # time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    
         # Wait for the chat response element to be visible
    response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]'))

    # Extract the response text
    # response_text = response_element.text.strip()

    # response_text = wait_for_chat_response(chatbot_url_driver, response_element)


    expected_response = (
        "This shipment has been processed at a DHL facility.\n"
        "To reorganize your delivery or to redirect it to another place, visit our delivery service on request.\n"
        "Would you like to track another package?"
    )

    # Flag to track if the expected response is found
    # response_found = expected_response in response_text
    time.sleep(4)
    # Log the result
    # if response_found:
    #     print("Expected response found.")
    # else:
    #     print(f"Expected response not found. Got: {response_text}")

    # Debugging output to see what the actual response is
    # print(f"Actual response received: {response_text}")
    time.sleep(3)
    # Assert that the response matches the expected message
    # assert expected_response in response_text, f"Expected response not found. Got: {response_text}"

    time.sleep(2)  # Adjust this as necessary

    # Optional: Interact with quick reply buttons if needed
    quick_replies = wait_for_visible(chatbot_url_driver, (By.CSS_SELECTOR, '[data-test-id="quick-replies"]'))
    quick_reply_buttons = quick_replies.find_elements(By.TAG_NAME, 'button')

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(5)
    expected_customer_name_response = (
        "Before I transfer you, could you provide your name so our advisor can address you?"
    )

    customer_name_response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]//div[@data-test-id="message-content"]'))
    customer_name_response_text = customer_name_response_element.text.strip()

    # assert expected_customer_name_response in customer_name_response_text, f"Expected response not found. Got: {customer_name_response_text}"
    
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("testpl")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    # Now locate the "Account Number" button and click it
    # Now locate the "Account Number" button and click it
    # Correct XPath to find the "Account Number" button
    account_number_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Account Number"]]'))

    # Click the "Account Number" button
    account_number_button.click()
    time.sleep(5)
    # Click the "Account Number" button
    # click_with_retry(chatbot_url_driver, (By.XPATH, account_number_button))
    # time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("813159982")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for PL Checkpoint with valid Telephone Number")
@record_test(fps=30)
def test_dhl_automation_PL_valid_telephone_number(setup_driver):
    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)
    # Enter Air Way Bill for PL
    air_way_bill = "AWB-PL-TEST"
    air_way_bill_number = "1775460934"
    print(f"Entering Air Way Bill: {air_way_bill} with {air_way_bill_number}for checkpoint: PL")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    # Continue with other interactions if necessary
    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(3)
    # Add any additional steps specific to the PL test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    expected_response = (
        "This shipment has been processed at a DHL facility.\n"
        "To reorganize your delivery or to redirect it to another place, visit our delivery service on request.\n"
        "Would you like to track another package?"
    )

     # Wait for the chat response element to be visible
    response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]'))

    # Extract the response text
    response_text = response_element.text.strip()

    # Assert that the response matches the expected message
    # assert expected_response in response_text, f"Expected response not found. Got: {response_text}"

    # Optional: Interact with quick reply buttons if needed
    quick_replies = wait_for_visible(chatbot_url_driver, (By.CSS_SELECTOR, '[data-test-id="quick-replies"]'))
    quick_reply_buttons = quick_replies.find_elements(By.TAG_NAME, 'button')

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(5)
    expected_customer_name_response = (
        "Before I transfer you, could you provide your name so our advisor can address you?"
    )

    customer_name_response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]//div[@data-test-id="message-content"]'))
    customer_name_response_text = customer_name_response_element.text.strip()

    # assert expected_customer_name_response in customer_name_response_text, f"Expected response not found. Got: {customer_name_response_text}"
    
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("testpl")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    # Now locate the "Telephone Number" button and click it
    # Now locate the "Telephone Number" button and click it
    # Correct XPath to find the "Account Number" button
    telephone_number_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Telephone Number"]]'))

    # Click the "Account Number" button
    telephone_number_button.click()
    time.sleep(5)
    # Click the "Account Number" button
    # click_with_retry(chatbot_url_driver, (By.XPATH, telephone_number_button))
    # time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("7875289866")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    time.sleep(6)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for PL Checkpoint with Valid Postal Code")
@record_test(fps=30)
def test_dhl_automation_PL_valid_post_code(setup_driver):
    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)
    # Enter Air Way Bill for PL
    air_way_bill = "AWB-PL-TEST"
    air_way_bill_number = "1775460934"
    print(f"Entering Air Way Bill: {air_way_bill} with {air_way_bill_number}for checkpoint: PL")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    # Continue with other interactions if necessary
    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(3)
    # Add any additional steps specific to the PL test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    expected_response = (
        "This shipment has been processed at a DHL facility.\n"
        "To reorganize your delivery or to redirect it to another place, visit our delivery service on request.\n"
        "Would you like to track another package?"
    )

     # Wait for the chat response element to be visible
    response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]'))

    # Extract the response text
    response_text = response_element.text.strip()

    # Assert that the response matches the expected message
    # assert expected_response in response_text, f"Expected response not found. Got: {response_text}"

    # Optional: Interact with quick reply buttons if needed
    quick_replies = wait_for_visible(chatbot_url_driver, (By.CSS_SELECTOR, '[data-test-id="quick-replies"]'))
    quick_reply_buttons = quick_replies.find_elements(By.TAG_NAME, 'button')

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(5)
    expected_customer_name_response = (
        "Before I transfer you, could you provide your name so our advisor can address you?"
    )

    customer_name_response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]//div[@data-test-id="message-content"]'))
    customer_name_response_text = customer_name_response_element.text.strip()

    # assert expected_customer_name_response in customer_name_response_text, f"Expected response not found. Got: {customer_name_response_text}"
    
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("testpl")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    # Now locate the "Postal Code" button and click it
    # Now locate the "Postal Code" button and click it
    # Correct XPath to find the "Postal Code" button
    post_code_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Post Code"]]'))

    # Click the "Postal Code" button
    post_code_button.click()
    time.sleep(5)
    # Click the "Postal Code" button
    # click_with_retry(chatbot_url_driver, (By.XPATH, post_code_button))
    # time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("00-020")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(2)

    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for PU Checkpoint with Valid Account Number")
@record_test(fps=30)
def test_dhl_automation_PU_valid_account_number(setup_driver):
    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)
    # Enter Air Way Bill for PU
    air_way_bill = "AWB-PU-TEST"
    air_way_bill_number = "1059240464"
    (f"Entering Air Way Bill: {air_way_bill} with  {air_way_bill_number}for checkpoint: PU")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(3)
    # Add any additional steps specific to the PL test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    expected_response = (
        "This shipment has been processed at a DHL facility.\n"
        "To reorganize your delivery or to redirect it to another place, visit our delivery service on request.\n"
        "Would you like to track another package?"
    )

     # Wait for the chat response element to be visible
    response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]'))

    # Extract the response text
    response_text = response_element.text.strip()

    # Assert that the response matches the expected message
    # assert expected_response in response_text, f"Expected response not found. Got: {response_text}"

    # Optional: Interact with quick reply buttons if needed
    # quick_replies = wait_for_visible(chatbot_url_driver, (By.CSS_SELECTOR, '[data-test-id="quick-replies"]'))
    # quick_reply_buttons = quick_replies.find_elements(By.TAG_NAME, 'button')

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(5)
    expected_customer_name_response = (
        "Before I transfer you, could you provide your name so our advisor can address you?"
    )

    customer_name_response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]//div[@data-test-id="message-content"]'))
    customer_name_response_text = customer_name_response_element.text.strip()

    # assert expected_customer_name_response in customer_name_response_text, f"Expected response not found. Got: {customer_name_response_text}"
    
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("testpuwithvalidaccountnumber")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    # Now locate the "Account Number" button and click it
    # Now locate the "Account Number" button and click it
    # Correct XPath to find the "Account Number" button
    account_number_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Account Number"]]'))

    # Click the "Account Number" button
    account_number_button.click()
    time.sleep(5)
    # Click the "Account Number" button
    # click_with_retry(chatbot_url_driver, (By.XPATH, account_number_button))
    # time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("813159982")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for PU Checkpoint with Valid Telephone Number")
@record_test(fps=30)
def test_dhl_automation_PU_valid_telephone_number(setup_driver):
    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)
    # Enter Air Way Bill for PU
    air_way_bill = "AWB-PU-TEST"
    air_way_bill_number = "1059240464"
    (f"Entering Air Way Bill: {air_way_bill} with  {air_way_bill_number}for checkpoint: PU")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(3)
    # Add any additional steps specific to the PL test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    expected_response = (
        "This shipment has been processed at a DHL facility.\n"
        "To reorganize your delivery or to redirect it to another place, visit our delivery service on request.\n"
        "Would you like to track another package?"
    )

     # Wait for the chat response element to be visible
    response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]'))

    # Extract the response text
    response_text = response_element.text.strip()

    # Assert that the response matches the expected message
    # assert expected_response in response_text, f"Expected response not found. Got: {response_text}"

    # Optional: Interact with quick reply buttons if needed
    # quick_replies = wait_for_visible(chatbot_url_driver, (By.CSS_SELECTOR, '[data-test-id="quick-replies"]'))
    # quick_reply_buttons = quick_replies.find_elements(By.TAG_NAME, 'button')

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(5)
    expected_customer_name_response = (
        "Before I transfer you, could you provide your name so our advisor can address you?"
    )

    customer_name_response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]//div[@data-test-id="message-content"]'))
    customer_name_response_text = customer_name_response_element.text.strip()

    # assert expected_customer_name_response in customer_name_response_text, f"Expected response not found. Got: {customer_name_response_text}"
    
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("testpuwithvalidaccountnumber")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    # Now locate the "Telephone Number" button and click it
    # Now locate the "Telephone Number" button and click it
    # Correct XPath to find the "Telephone Number" button
    telephone_number_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Telephone Number"]]'))

    # Click the "Telephone Number" button
    telephone_number_button.click()
    time.sleep(5)
    # Click the "Telephone Number" button
    # click_with_retry(chatbot_url_driver, (By.XPATH, telephone_number_button))
    # time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("7875289866")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for PU Checkpoint with Valid Postal Code")
@record_test(fps=30)
def test_dhl_automation_PU_valid_post_code(setup_driver):
    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)
    # Enter Air Way Bill for PU
    air_way_bill = "AWB-PU-TEST"
    air_way_bill_number = "1059240464"
    (f"Entering Air Way Bill: {air_way_bill} with  {air_way_bill_number}for checkpoint: PU")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(3)
    # Add any additional steps specific to the PL test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    expected_response = (
        "This shipment has been processed at a DHL facility.\n"
        "To reorganize your delivery or to redirect it to another place, visit our delivery service on request.\n"
        "Would you like to track another package?"
    )

     # Wait for the chat response element to be visible
    response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]'))

    # Extract the response text
    response_text = response_element.text.strip()

    # Assert that the response matches the expected message
    # assert expected_response in response_text, f"Expected response not found. Got: {response_text}"

    # Optional: Interact with quick reply buttons if needed
    # quick_replies = wait_for_visible(chatbot_url_driver, (By.CSS_SELECTOR, '[data-test-id="quick-replies"]'))
    # quick_reply_buttons = quick_replies.find_elements(By.TAG_NAME, 'button')

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(5)
    expected_customer_name_response = (
        "Before I transfer you, could you provide your name so our advisor can address you?"
    )

    customer_name_response_element = wait_for_visible(chatbot_url_driver, (By.XPATH, '(//div[@data-test-id="chat-response"])[last()]//div[@data-test-id="message-content"]'))
    customer_name_response_text = customer_name_response_element.text.strip()

    # assert expected_customer_name_response in customer_name_response_text, f"Expected response not found. Got: {customer_name_response_text}"
    
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("testpuwithvalidpostcode")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(3)
    # Now locate the "Postal Code" button and click it
    # Now locate the "Postal Code" button and click it
    # Correct XPath to find the "Account Number" button
    post_code_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Postal Code"]]'))

    # Click the "Postal Code" button
    post_code_button.click()
    time.sleep(5)
    # Click the "Postal Code" button
    # click_with_retry(chatbot_url_driver, (By.XPATH, post_code_button))
    # time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("4017")
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for OK Checkpoint with Valid Account Number")
@record_test(fps=30)
def test_dhl_automation_OK_valid_account_number(setup_driver):
    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)
    # Enter Air Way Bill for OK
    air_way_bill = "AWB-OK-TEST"
    air_way_bill_number = "7593085581"
    print(f"Entering Air Way Bill: {air_way_bill} with {air_way_bill_number} for checkpoint: OK")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    # Continue with other interactions if necessary
    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(4)

    # Correct XPath to find the "Account Number" button
    account_number_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Account Number"]]'))

    # Click the "Account Number" button
    account_number_button.click()
    time.sleep(5)

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("813159982") # type: ignore
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    # Add any additional steps specific to the OK test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys('testokvalidaccountnumber')
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for OK Checkpoint with Valid Telephone Number")
@record_test(fps=30)
def test_dhl_automation_OK_valid_telephone_number(setup_driver):
    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)
    # Enter Air Way Bill for OK
    air_way_bill = "AWB-OK-TEST"
    air_way_bill_number = "7593085581"
    print(f"Entering Air Way Bill: {air_way_bill} with {air_way_bill_number} for checkpoint: OK")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    # Continue with other interactions if necessary
    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(4)

    # Correct XPath to find the "Telephone Number" button
    telephone_number_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Telephone Number"]]'))

    # Click the "Telephone Number" button
    telephone_number_button.click()
    time.sleep(5)

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("7875289866") # type: ignore
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    # Add any additional steps specific to the OK test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys('testokvalidtelephonenumber')
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for OK Checkpoint with Valid Postal Code")
@record_test(fps=30)
def test_dhl_automation_OK_valid_post_code(setup_driver):
    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)

    # Enter Air Way Bill for OK
    air_way_bill = "AWB-OK-TEST"
    air_way_bill_number = "7593085581"
    print(f"Entering Air Way Bill: {air_way_bill} with {air_way_bill_number} for checkpoint: OK")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    # Continue with other interactions if necessary
    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(4)

    # Correct XPath to find the "Postal Code" button
    post_code_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Postal Code"]]'))

    # Click the "Postal Code" button
    post_code_button.click()
    time.sleep(5)

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("1009") # type: ignore
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    # Add any additional steps specific to the OK test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys('testokvalidpostcode')
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for OK Checkpoint with Valid Postal Code")
@record_test(fps=30)
def test_dhl_automation_OK_invalid_post_code(setup_driver):
    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)

    # Enter Air Way Bill for OK
    air_way_bill = "AWB-OK-TEST"
    air_way_bill_number = "7593085581"
    print(f"Entering Air Way Bill: {air_way_bill} with {air_way_bill_number} for checkpoint: OK")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    # Continue with other interactions if necessary
    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(4)

    # Correct XPath to find the "Postal Code" button
    post_code_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Postal Code"]]'))

    # Click the "Postal Code" button
    post_code_button.click()
    time.sleep(5)
    for i in range(3):
        wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("invalid") # type: ignore
        time.sleep(3)
        wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
        time.sleep(2)

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    # Add any additional steps specific to the OK test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys('testokinvalidpostcode')
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for OK Checkpoint with In Valid Account Number")
@record_test(fps=30)
def test_dhl_automation_OK_invalid_account_number(setup_driver):
    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)

    # Enter Air Way Bill for OK
    air_way_bill = "AWB-OK-TEST"
    air_way_bill_number = "7593085581"
    print(f"Entering Air Way Bill: {air_way_bill} with {air_way_bill_number} for checkpoint: OK")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    # Continue with other interactions if necessary
    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(4)

    # Correct XPath to find the "Postal Code" button
    account_number_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Account Number"]]'))

    # Click the "Postal Code" button
    account_number_button.click()
    time.sleep(5)
    for i in range(3):
        wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("invalid") # type: ignore
        time.sleep(3)
        wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
        time.sleep(2)

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    # Add any additional steps specific to the OK test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys('testokinvalidaccountnumber')
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)

@pytest.mark.checkpoint("This test case is for OK Checkpoint with In Valid Account Number")
@record_test(fps=30)
def test_dhl_automation_OK_invalid_telephone_number(setup_driver):

    agent_login_url_driver, chatbot_url_driver, user_context = setup_chat_environment(setup_driver)

    # Enter Air Way Bill for OK
    air_way_bill = "AWB-OK-TEST"
    air_way_bill_number = "7593085581"
    print(f"Entering Air Way Bill: {air_way_bill} with {air_way_bill_number} for checkpoint: OK")

    click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

    # Continue with other interactions if necessary
    wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(air_way_bill_number)
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    time.sleep(4)

    # Correct XPath to find the "Telephone Number" button
    telephone_number_button = wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="quick-replies"]//button[span[text()="Telephone Number"]]'))

    # Click the "Telephone Number" button
    telephone_number_button.click()
    time.sleep(5)
    # attempt = 3
    for i in range(4):
        wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys("invalid") # type: ignore
        time.sleep(3)
        wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
        time.sleep(2)

    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys(user_context.customer_service_utterance) # type: ignore
    time.sleep(2)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    # Add any additional steps specific to the OK test case here
    wait_for_visible(chatbot_url_driver,Locators.CHAT_INPUT).send_keys('testokinvalidaccountnumber')
    time.sleep(3)
    wait_for_visible(chatbot_url_driver,Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
    wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
    wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
    wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)
    finalize_chat_transfer_security(agent_login_url_driver, chatbot_url_driver)


if __name__ == "__main__":
    pytest.main()
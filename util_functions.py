from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from locators import Locators  # Import the Locators class

class UtilityFunctions:

    def record_test(driver, test_actions, max_duration=60, output_filename=None):
        if output_filename is None:
            output_filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

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


    def perform_chat_interaction(agent_login_url_driver, chatbot_url_driver, user_context):
        username = user_context.username
        password = user_context.password
        country_code = user_context.country_code
        lang_code = user_context.lang_code
        CUSTOMER_SERVICE_UTTERANCE = user_context.customer_service_utterance
        site_reference = user_context.site_reference  # Get the site reference

        # Common login to the first driver
        common_login(agent_login_url_driver, username, password)

        # Determine the URL based on the site reference
        if site_reference == "Tracking Page":
            air_way_bill_number = "1775460934"  # Example AWB number
            url = f'https://ewfsit.dhl.com/{country_code}/{lang_code}/tracking.html#/results?id={air_way_bill_number}'
        elif site_reference == "Contact Us":
            url = f'https://ewfsit.dhl.com/{country_code}/{lang_code}/help-and-support.html'
        elif site_reference == "HomePage":
            url = f'https://ewfsit.dhl.com/{country_code}/{lang_code}/home.html'
        else:
            raise ValueError(f"Unknown site reference: {site_reference}")

        # Navigate to the constructed URL
        chatbot_url_driver.get(url)
        click_with_retry(chatbot_url_driver, Locators.ACCEPT_ALL_BUTTON)

        # Switch to the chat frame
        chat_frame = wait_for_visible(chatbot_url_driver, Locators.CHAT_FRAME)
        chatbot_url_driver.switch_to.frame(chat_frame)
        click_with_retry(chatbot_url_driver, Locators.MINIMIZED_BUTTON)

        # Continue with chat interactions
        wait_for_visible(chatbot_url_driver, (By.XPATH, '//div[@data-test-id="session-start"]'))
        time.sleep(2)
        wait_for_visible(chatbot_url_driver, Locators.CHAT_INPUT).send_keys(CUSTOMER_SERVICE_UTTERANCE)  # type: ignore
        time.sleep(2)
        wait_for_visible(chatbot_url_driver, Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
        time.sleep(5)

        # Additional interaction with the chat
        wait_for_visible(chatbot_url_driver, Locators.CHAT_INPUT).send_keys("testcustomerservice")  # Example user input
        wait_for_visible(chatbot_url_driver, Locators.CHAT_SUBMIT).send_keys(Keys.ENTER)
        time.sleep(3)

        # Wait for the takeover start and agent entered
        wait_for_visible(chatbot_url_driver, Locators.TAKEOVER_START)
        wait_for_visible(chatbot_url_driver, Locators.AGENT_ENTERED)
        wait_for_visible(chatbot_url_driver, Locators.CHAT_RESPONSE)

        # Finalize the chat transfer
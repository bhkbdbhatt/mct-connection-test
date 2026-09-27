# locators.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Locators:
    # Login Page
    USERNAME_FIELD = (By.ID, 'userName')
    PASSWORD_FIELD = (By.ID, 'password')
    LOGIN_BUTTON = (By.XPATH, '//button[text()="Login"]')
    CONCURRENT_LOGIN_FORM = (By.ID, 'ConcurrentLoginDetectedForm')
    CONTINUE_BUTTON = (By.ID, 'f5_btnContinue')
    
    # Dropdown
    # OPT_REQUESTED_STATUS = (By.XPATH, "//select[@class='GTOptionMenu top-bar-option-menu floatRight optRequestedStatus' and @title='Availability']")
    # OPT_REQUESTED_STATUS = (By.XPATH, "//select[@class='GTOptionMenu top-bar-option-menu floatRight optRequestedStatus' and @title='Availability' and @name='f47_optRequestedStatus']")
    OPT_REQUESTED_STATUS = (By.XPATH, "//select[contains(@class, 'GTOptionMenu top-bar-option-menu')]")
    
    # Shipment Creation Page
    ONETRUST_FILTER = (By.CLASS_NAME, 'onetrust-pc-dark-filter')
    ACCEPT_ALL_BUTTON = (By.XPATH, '//button[text()="Accept All"]')
    
    # Chatbot
    CHAT_FRAME = (By.XPATH, '//iframe[@title="DHL VA Widget"]')
    MINIMIZED_BUTTON = (By.CSS_SELECTOR, '[data-test-id="minimized-button"]')
    CHAT_INPUT = (By.CSS_SELECTOR, '[data-test-id="chat-input"]')
    CHAT_SUBMIT = (By.CSS_SELECTOR, '[data-test-id="chat-submit"]')
    
    # Wait for agent response
    TAKEOVER_START = (By.XPATH, '//div[@data-test-id="takeover-start"]')
    AGENT_ENTERED = (By.XPATH, '//div[@data-test-id="agent-entered"]')
    CHAT_RESPONSE = (By.XPATH, '//div[@data-test-id="chat-response"]')

    # CUSTOMER_VALIDATION_TEXT_AND_BELOW = (By.XPATH, "//div[contains(@class, 'chatBubble chatBubbleCustomer')][following-sibling::text()[contains(., 'CUSTOMER VALIDATION')]]//text()[following::text()[1]]")
    # CUSTOMER_VALIDATION_TEXT = (By.XPATH, "//div[contains(@class, 'chatBubble chatBubbleCustomer')]//text()[contains(.,'CUSTOMER VALIDATION')]")
    CUSTOMER_VALIDATION_TEXT = (By.XPATH, "//div[contains(@class, 'chatBubble chatBubbleCustomer') and contains(text(), 'CUSTOMER VALIDATION')]")
    # End Chat
    END_CHAT_BUTTON = (By.XPATH, "//button[@title='End chat' and contains(@class, 'GTImageButton')]")
    CONFIRM_BUTTON = (By.XPATH, "//button[@title='Confirm' and contains(@class, 'btnConfirm')]")
    CLOSE_CHAT_BUTTON = (By.XPATH, '//button[@id="f106_btnCloseChat"]')
    END_CHAT_SUBMIT_BUTTON = (By.XPATH, "//button[contains(@class, 'btnQuickWrapup')]") #need customization as per country
    LOGOUT_BUTTON = (By.XPATH, '//button[text()="Log out"]')
    OK_BUTTON = (By.XPATH, '//button[text()="Ok"]')

    AGENT_SIDE_CONVERSATION_ENDED = (By.XPATH, "//td[contains(text(), 'The conversation has been ended.'")
    
    # Conversation Messages
    AGENT_LOGOUT_MESSAGE = (By.XPATH, "//div[@data-test-id='agent-logout' and text()='GVA left the conversation']")
    TAKEOVER_END_MESSAGE = (By.XPATH, "//div[@data-test-id='takeover-end' and text()='You are now chatting with your digital assistant']")
#!/usr/bin/env python3
"""
ANTAM Queue Registration Bot - Standalone Module
Extracted for use with Flask dashboard
"""

import time
import random
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ANTAMQueueBot:
    def __init__(self, headless=False):
        self.setup_driver(headless)
        self.success = False
        self.user_data = {
            "name": "",
            "ktp": "", 
            "phone": ""
        }
        
    def setup_driver(self, headless=False):
        """Setup Chrome WebDriver"""
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
            
            # Hide automation signals
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            raise Exception(f"Failed to initialize Chrome driver. Make sure Chrome is installed. Error: {e}")
            
    def get_csrf_token(self):
        """Extract CSRF token from the form"""
        try:
            token_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "_token"))
            )
            return token_input.get_attribute("value")
        except TimeoutException:
            logging.error("Could not find CSRF token")
            return None
            
    def get_captcha_text(self):
        """Extract current captcha text and clean it properly"""
        try:
            captcha_box = self.wait.until(
                EC.presence_of_element_located((By.ID, "captcha-box"))
            )
            # Get text and strip all whitespace, including letter-spacing gaps
            raw_text = captcha_box.text
            # Remove all whitespace and keep only alphanumeric characters
            clean_text = ''.join(raw_text.split())
            logging.info(f"Raw captcha: '{raw_text}' -> Clean: '{clean_text}'")
            return clean_text
        except TimeoutException:
            logging.error("Could not find captcha")
            return None
            
    def solve_captcha(self, captcha_text):
        """Since captcha is plain text in HTML, just return it cleaned up"""
        return captcha_text
        
    def fill_form(self, site_url):
        """Fill out the registration form"""
        try:
            logging.info(f"Loading site: {site_url}")
            self.driver.get(site_url)
            
            # Wait for form to load
            self.wait.until(EC.presence_of_element_located((By.NAME, "name")))
            
            # Get CSRF token
            csrf_token = self.get_csrf_token()
            if not csrf_token:
                logging.error("Failed to get CSRF token")
                return False
                
            logging.info(f"Got CSRF token: {csrf_token[:10]}...")
            
            # Fill name field
            name_input = self.driver.find_element(By.ID, "name")
            name_input.clear()
            name_input.send_keys(self.user_data["name"])
            time.sleep(random.uniform(0.5, 1.5))
            
            # Fill KTP field
            ktp_input = self.driver.find_element(By.ID, "ktp")
            ktp_input.clear()
            ktp_input.send_keys(self.user_data["ktp"])
            time.sleep(random.uniform(0.5, 1.5))
            
            # Fill phone field
            phone_input = self.driver.find_element(By.ID, "phone_number")
            phone_input.clear()
            phone_input.send_keys(self.user_data["phone"])
            time.sleep(random.uniform(0.5, 1.5))
            
            # Check both checkboxes
            checkbox1 = self.driver.find_element(By.ID, "check")
            if not checkbox1.is_selected():
                checkbox1.click()
                time.sleep(0.5)
                
            checkbox2 = self.driver.find_element(By.ID, "check_2")
            if not checkbox2.is_selected():
                checkbox2.click()
                time.sleep(0.5)
                
            # Handle captcha
            captcha_text = self.get_captcha_text()
            if not captcha_text:
                logging.error("Failed to get captcha text")
                return False
                
            logging.info(f"Captcha text: {captcha_text}")
            
            # Solve captcha (for now, just copy the text)
            captcha_solution = self.solve_captcha(captcha_text)
            
            captcha_input = self.driver.find_element(By.ID, "captcha_input")
            captcha_input.clear()
            captcha_input.send_keys(captcha_solution)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            logging.info("Submitting form...")
            submit_button.click()
            
            # Wait for response
            time.sleep(3)
            
            # Check for success indicators
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            # Look for success indicators
            success_indicators = [
                "berhasil", "success", "antrian", "nomor", 
                "terima kasih", "thank you", "registered"
            ]
            
            if any(indicator in page_source for indicator in success_indicators):
                self.take_screenshot("SUCCESS")
                logging.info("🎉 FORM SUBMITTED SUCCESSFULLY! 🎉")
                return True
            else:
                self.take_screenshot("UNKNOWN_RESULT")
                logging.warning("Form submitted but unclear if successful")
                return False
                
        except Exception as e:
            logging.error(f"Error filling form: {str(e)}")
            self.take_screenshot("ERROR")
            return False
            
    def take_screenshot(self, prefix):
        """Take screenshot for debugging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/{prefix}_{timestamp}.png"
        try:
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logging.error(f"Could not save screenshot: {e}")
            return None
            
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            
    def test_site(self, site_url):
        """Test if a site is accessible and has the expected form"""
        try:
            logging.info(f"Testing site: {site_url}")
            self.driver.get(site_url)
            
            # Check if form elements exist
            required_elements = [
                (By.ID, "name"),
                (By.ID, "ktp"), 
                (By.ID, "phone_number"),
                (By.ID, "check"),
                (By.ID, "check_2"),
                (By.ID, "captcha_input")
            ]
            
            missing_elements = []
            for locator in required_elements:
                try:
                    self.driver.find_element(*locator)
                except NoSuchElementException:
                    missing_elements.append(locator[1])
                    
            if missing_elements:
                logging.warning(f"Missing form elements: {missing_elements}")
                return False, f"Missing elements: {', '.join(missing_elements)}"
            else:
                logging.info("Site test passed - all form elements found")
                return True, "All form elements found"
                
        except Exception as e:
            logging.error(f"Site test failed: {e}")
            return False, str(e)

# For standalone testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot_test.log')
        ]
    )
    
    # Test the bot
    bot = ANTAMQueueBot(headless=False)  # Set to True for headless mode
    
    # Set test data
    bot.user_data = {
        "name": "Test User",
        "ktp": "123456",
        "phone": "08123456789"
    }
    
    try:
        # Test site accessibility
        test_url = "http://127.0.0.1:5500/contoh.html"
        success, message = bot.test_site(test_url)
        print(f"Site test: {'PASS' if success else 'FAIL'} - {message}")
        
        if success:
            # Try to fill the form
            result = bot.fill_form(test_url)
            print(f"Form submission: {'SUCCESS' if result else 'FAILED'}")
            
    except KeyboardInterrupt:
        print("Test interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        bot.cleanup()
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1280,800")

try:
    print("Starting Chrome...")
    driver = webdriver.Chrome(options=options)
    
    # Capture Landing Page
    print("Navigating to landing page...")
    driver.get("http://localhost:8000/landing")
    time.sleep(2)
    driver.save_screenshot("screenshot_landing.png")
    print("Saved screenshot_landing.png")
    
    # Capture Login and Authenticate
    print("Navigating to dashboard...")
    driver.get("http://localhost:8000/")
    time.sleep(1)
    
    print("Logging in...")
    email_input = driver.find_element(By.ID, "a-email")
    email_input.send_keys("demo@test.com")
    
    pass_input = driver.find_element(By.ID, "a-pass")
    pass_input.send_keys("demo123")
    
    submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign In')]")
    submit_btn.click()
    
    time.sleep(2)  # Wait for dashboard to load
    
    # Capture Authenticated Dashboard
    driver.save_screenshot("screenshot_dashboard_auth.png")
    print("Saved screenshot_dashboard_auth.png")
    
    # Navigate to Find Jobs and Capture
    print("Navigating to Find Jobs...")
    jobs_nav = driver.find_element(By.XPATH, "//div[contains(@class, 'nav-item') and contains(text(), 'Find Jobs')]")
    jobs_nav.click()
    
    time.sleep(3)  # Wait for jobs to load
    driver.save_screenshot("screenshot_find_jobs.png")
    print("Saved screenshot_find_jobs.png")
    
    driver.quit()
    print("Done!")
except Exception as e:
    print(f"Error occurred: {e}")


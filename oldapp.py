from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time
import logging
import threading

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger()

# Global variable to store the status data
status_data = {}
driver = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check_status", methods=["POST"])
def check_status():
    global status_data
    global driver

    name = request.form.get("name")

    # Path to the new Chrome profile
    profile_path = '~/chrome-profile'

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument(f'user-data-dir={profile_path}')

    webdriver_service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

    try:
        driver.get("https://web.whatsapp.com/")
        logger.info("WhatsApp Web opened successfully")

        # Wait for QR code to be scanned and page loaded
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div._1VwoK")))

        # Start the status update thread
        threading.Thread(target=update_status, args=(name,)).start()

        return "Status update started"

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if driver:
            driver.quit()
        return "An error occurred: " + str(e), 500

def update_status(name):
    global status_data
    global driver

    try:
        while True:
            # Get the element with the ID "contact-status"
            status_element = driver.find_element(By.ID, "contact-status")

            # Extract the text content
            status_text = status_element.text

            # Determine the online status based on the text
            status = "Online" if status_text == "· ♡" else "Offline"

            # Update the status data
            status_data[name] = {
                "status": status,
                "timestamp": str(datetime.now())
            }

            # Sleep for 5 seconds before checking again
            time.sleep(5)

    except Exception as e:
        logger.error(f"An error occurred in update_status: {e}")
        if driver:
            driver.quit()

@app.route("/stop_checking", methods=["POST"])
def stop_checking():
    global driver

    if driver:
        driver.quit()
        return "Status update stopped"
    else:
        return "No status update in progress", 404

@app.route("/get_status/<name>", methods=["GET"])
def get_status(name):
    global status_data

    if name in status_data:
        return jsonify(status_data[name])
    else:
        return jsonify({"error": "No data for this name"}), 404

if __name__ == "__main__":
    app.run(debug=True)


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
import json

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

# Configure logging
logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Global variable to store the status data
status_data = {}

@app.route("/check_status", methods=["POST"])
def check_status():
    global status_data
    name = request.form["name"]

    # Path to the new Chrome profile
    profile_path = '~/chrome-profile'

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument(f'user-data-dir={profile_path}')

    webdriver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

    try:
        # Open the WhatsApp Web URL
        driver.get("https://web.whatsapp.com/")
        logging.info("WhatsApp Web opened successfully")
    except Exception as e:
        # Handle potential errors during script execution
        logging.error(f"An error occurred: {e}")
        driver.quit()
        return "An error occurred: " + str(e), 500

    try:
        # Wait until the name element is present in the DOM
        wait = WebDriverWait(driver, 10)  # wait for up to 10 seconds
        name_element = wait.until(EC.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{name}')]")))
        name_element.click()

        online_start_time = None
        offline_start_time = None

        while True:
            try:
                online_indicator = driver.find_element(By.XPATH, "//span[contains(text(), 'online')]")
                status = "Online"
                if online_start_time is None:
                    online_start_time = datetime.now()
                online_duration = datetime.now() - online_start_time
                logging.info(f"Online since: {online_start_time}, Duration: {online_duration}")
            except:
                status = "Offline"
                if offline_start_time is None:
                    offline_start_time = datetime.now()
                offline_duration = datetime.now() - offline_start_time
                logging.info(f"Offline since: {offline_start_time}, Duration: {offline_duration}")

            # Update the status data
            status_data[name] = {
                "status": status,
                "online_duration": str(online_duration) if online_start_time else None,
                "offline_duration": str(offline_duration) if offline_start_time else None
            }

            # Save the status data to a JSON file
            with open('status_data.json', 'w') as f:
                json.dump(status_data, f)

            time.sleep(5)  # wait for 5 seconds before checking the status again

            try:
                auth_button = driver.find_element(By.XPATH, "//button[contains(text(), 'I am authenticated')]")
                break  # exit the loop if the authentication button is found
            except:
                pass

        # Script execution successful, close the driver
        driver.quit()
        return render_template("result.html", name=name, status=status, online_duration=online_duration if online_start_time else None, offline_duration=offline_duration if offline_start_time else None)

    except Exception as e:
        # Handle potential errors during script execution
        logging.error(f"An error occurred: {e}")
        driver.quit()
        return "An error occurred: " + str(e), 500  # Return an error message and a 500 status code

@app.route("/get_status/<name>", methods=["GET"])
def get_status(name):
    global status_data
    if name in status_data:
        return jsonify(status_data[name])
    else:
        return jsonify({"error": "No data for this name"}), 404

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time
import logging
import json
import threading

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

@app.route("/check_status", methods=["POST"])
def check_status():
    name = request.form["name"]

    # Path to the new Chrome profile
    # For auto login and extensions
    profile_path = '~/chrome-profile'

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument(f'user-data-dir={profile_path}')

    webdriver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

    try:
        driver.get("https://web.whatsapp.com/")
        logging.info("WhatsApp Web opened successfully")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        driver.quit()
        return "An error occurred: " + str(e), 500

    def update_status():
        global status_data
        online_start_time = None
        online_duration = None
        offline_start_time = None

        while True:
            try:
                # Execute JavaScript to get the online status
                online_status = driver.execute_script("return window.Store.Chat.models[0].__x_presence.attributes.isOnline")
                status = "Online" if online_status else "Offline"

    ### Online is what is searchedin the DOM. You could also extract the last seen time and use that to determine the status of the user for example


                if status == "Online":
                    if online_start_time is None:
                        online_start_time = datetime.now()
                    online_duration = datetime.now() - online_start_time
                    logging.info(f"Online since: {online_start_time}, Duration: {online_duration}")
                    print(f"Status: {status}, Online since: {online_start_time}, Duration: {online_duration}")
                else:
                    if offline_start_time is None:
                        offline_start_time = datetime.now()
                    offline_duration = datetime.now() - offline_start_time
                    logging.info(f"Offline since: {offline_start_time}, Duration: {offline_duration}")
                    print(f"Status: {status}, Offline since: {offline_start_time}, Duration: {offline_duration}")

                # Update the status data
                status_data[name] = {
                    "status": status,
                    "online_start_time": str(online_start_time) if online_start_time else "",
                    "online_duration": str(online_duration) if online_start_time else None,
                    "offline_duration": str(offline_duration) if offline_start_time else None
                }

                time.sleep(5)  # wait for 5 seconds before checking the status again

            except Exception as e:
                logging.error(f"An error occurred: {e}")
                break

        driver.quit()

    # Start the status update thread
    threading.Thread(target=update_status).start()

    return "Status update started"

@app.route("/get_status/<name>", methods=["GET"])
def get_status(name):
    if name in status_data:
        return jsonify(status_data[name])
    else:
        return jsonify({"error": "No data for this name"}), 404

if __name__ == "__main__":
    # Global variable to store the status data
    status_data = {}

    app.run(debug=True)

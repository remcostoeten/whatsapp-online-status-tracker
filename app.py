from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check_status", methods=["POST"])
def check_status():
    name = request.form["name"]

    # Move driver initialization inside the function for better scope control
    webdriver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=webdriver_service)

    try:
        # Search for the name element using user input
        lianne_element = driver.find_element(By.XPATH, f"//span[contains(text(), '{name}')]")
        lianne_element.click()

        online_start_time = None
        offline_start_time = None

        while True:
            try:
                online_indicator = driver.find_element(By.XPATH, "//span[contains(text(), 'online')]")
                status = "Online"
                if online_start_time is None:
                    online_start_time = datetime.now()
                online_duration = datetime.now() - online_start_time
                print(f"Online since: {online_start_time}, Duration: {online_duration}")
            except:
                status = "Offline"
                if offline_start_time is None:
                    offline_start_time = datetime.now()
                offline_duration = datetime.now() - offline_start_time
                print(f"Offline since: {offline_start_time}, Duration: {offline_duration}")

            time.sleep(5)  # wait for 5 seconds before checking the status again

        # Script execution successful, close the driver
        driver.quit()
        return render_template("result.html", name=name, status=status, online_duration=online_duration if online_start_time else None, offline_duration=offline_duration if offline_start_time else None)

    except Exception as e:
        # Handle potential errors during script execution
        print(f"Error occurred: {e}")
        driver.quit()  # Close the driver even on error
        return render_template("error.html", error_message=str(e))

if __name__ == "__main__":
    app.run(debug=True)

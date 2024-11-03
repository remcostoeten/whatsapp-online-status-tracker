from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import time
import logging
import threading
import os
import json
from pathlib import Path
from pythonjsonlogger import jsonlogger

app = Flask(__name__)

# Configure logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Global variables
status_data = {}
driver = None
data_file = "status_history.json"

# Load previous data if exists
def load_saved_data():
    global status_data
    try:
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                status_data = json.load(f)
            logger.info("Loaded saved status data")
    except Exception as e:
        logger.error(f"Error loading saved data: {e}")

# Save data periodically
def save_data():
    global status_data
    try:
        with open(data_file, 'w') as f:
            json.dump(status_data, f)
        logger.info("Status data saved")
    except Exception as e:
        logger.error(f"Error saving data: {e}")

def initialize_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--headless")  # Uncomment for headless mode
        
        # Try to use system ChromeDriver first
        driver_path = "/usr/local/bin/chromedriver"
        if not os.path.exists(driver_path):
            driver_path = "/usr/bin/chromedriver"
        
        service = Service(executable_path=driver_path)
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        logger.error(f"Error initializing driver: {str(e)}")
        raise

def select_contact(driver, contact_name):
    try:
        # Wait for the search box
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
        )
        
        # Clear and type contact name
        search_box.clear()
        search_box.send_keys(contact_name)
        time.sleep(2)
        
        # Try different contact selectors
        contact_xpath_options = [
            f"//span[@title='{contact_name}']",
            f"//span[contains(@title, '{contact_name}')]",
            f"//div[contains(@class, 'zoWT4')]//span[contains(text(), '{contact_name}')]"
        ]
        
        contact = None
        for xpath in contact_xpath_options:
            try:
                contact = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                if contact:
                    break
            except:
                continue
        
        if not contact:
            raise Exception(f"Contact {contact_name} not found")
        
        contact.click()
        time.sleep(2)
        logger.info(f"Selected contact: {contact_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error selecting contact: {str(e)}")
        raise

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check_status", methods=["POST"])
def check_status():
    global status_data
    global driver

    try:
        name = request.form.get("name")
        if not name:
            return jsonify({"error": "Name is required"}), 400

        # Initialize driver and WhatsApp
        driver = initialize_driver()
        driver.get("https://web.whatsapp.com/")
        logger.info("WhatsApp Web opened")

        # Wait for QR code scan and load
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
        )
        
        # Select contact
        select_contact(driver, name)
        
        # Initialize status data structure
        if name not in status_data:
            status_data[name] = {
                'history': [],
                'statistics': {
                    'total_time': 0,
                    'online_time': 0,
                    'status_changes': 0
                },
                'current': {
                    'status': 'Unknown',
                    'timestamp': datetime.now().isoformat()
                }
            }

        # Start monitoring thread
        threading.Thread(
            target=update_status,
            args=(name,),
            daemon=True
        ).start()

        return jsonify({"message": "Status tracking started"})

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if driver:
            driver.quit()
        return jsonify({"error": str(e)}), 500

def update_status(name):
    global status_data
    global driver
    
    save_interval = 0
    try:
        while driver:
            try:
                # Check online status
                online_indicators = [
                    "//span[contains(text(), 'online')]",
                    "//span[contains(text(), 'typing')]",
                    "//span[contains(@title, 'online')]"
                ]
                
                is_online = False
                for indicator in online_indicators:
                    try:
                        elements = driver.find_elements(By.XPATH, indicator)
                        if elements:
                            is_online = True
                            break
                    except:
                        continue
                
                current_time = datetime.now()
                status = "Online" if is_online else "Offline"
                
                # Update current status
                status_data[name]['current'] = {
                    'status': status,
                    'timestamp': current_time.isoformat()
                }
                
                # Add to history if status changed or 5 minutes passed
                if (not status_data[name]['history'] or 
                    status_data[name]['history'][-1]['status'] != status or 
                    (current_time - datetime.fromisoformat(status_data[name]['history'][-1]['timestamp'].replace('Z', '+00:00'))).total_seconds() > 300):
                    
                    status_data[name]['history'].append({
                        'status': status,
                        'timestamp': current_time.isoformat()
                    })
                    
                    # Keep last 1000 entries
                    if len(status_data[name]['history']) > 1000:
                        status_data[name]['history'] = status_data[name]['history'][-1000:]
                    
                    # Update statistics
                    status_data[name]['statistics'] = calculate_statistics(status_data[name]['history'])
                
                # Save data every 5 minutes
                save_interval += 1
                if save_interval >= 60:  # 60 * 5 seconds = 5 minutes
                    save_data()
                    save_interval = 0
                
            except Exception as e:
                logger.error(f"Error updating status: {str(e)}")
                status_data[name]['current'] = {
                    'status': 'Error',
                    'timestamp': datetime.now().isoformat()
                }
            
            time.sleep(5)
            
    except Exception as e:
        logger.error(f"Fatal error in update_status: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def calculate_statistics(history):
    if not history:
        return {
            'total_time': 0,
            'online_time': 0,
            'status_changes': 0,
            'online_percentage': 0,
            'hourly_pattern': [0] * 24,
            'daily_summary': {
                'most_active_hour': None,
                'least_active_hour': None,
                'average_session_duration': 0
            }
        }
    
    total_time = 0
    online_time = 0
    status_changes = 0
    hourly_counts = [[0, 0] for _ in range(24)]
    online_sessions = []
    current_session_start = None
    
    for i in range(1, len(history)):
        current = datetime.fromisoformat(history[i]['timestamp'].replace('Z', '+00:00'))
        previous = datetime.fromisoformat(history[i-1]['timestamp'].replace('Z', '+00:00'))
        duration = (current - previous).total_seconds()
        
        # Track status changes
        if history[i]['status'] != history[i-1]['status']:
            status_changes += 1
            if history[i-1]['status'] == 'Online':
                if current_session_start:
                    session_duration = (current - current_session_start).total_seconds()
                    online_sessions.append(session_duration)
                    current_session_start = None
            elif history[i]['status'] == 'Online':
                current_session_start = current
        
        # Calculate times
        if history[i-1]['status'] == 'Online':
            online_time += duration
        total_time += duration
        
        # Update hourly pattern
        hour = previous.hour
        hourly_counts[hour][0] += duration
        if history[i-1]['status'] == 'Online':
            hourly_counts[hour][1] += duration
    
    # Calculate hourly percentages
    hourly_pattern = [
        (online / total * 100 if total > 0 else 0)
        for online, total in hourly_counts
    ]
    
    # Find most/least active hours
    max_hour = hourly_pattern.index(max(hourly_pattern))
    min_hour = hourly_pattern.index(min(hourly_pattern))
    
    # Calculate average session duration
    avg_session = sum(online_sessions) / len(online_sessions) if online_sessions else 0
    
    return {
        'total_time': total_time,
        'online_time': online_time,
        'status_changes': status_changes,
        'online_percentage': (online_time / total_time * 100) if total_time > 0 else 0,
        'hourly_pattern': hourly_pattern,
        'daily_summary': {
            'most_active_hour': max_hour,
            'least_active_hour': min_hour,
            'average_session_duration': avg_session
        }
    }

@app.route("/stop_checking", methods=["POST"])
def stop_checking():
    global driver
    
    if driver:
        try:
            driver.quit()
            driver = None
            save_data()
            return jsonify({"message": "Status tracking stopped"})
        except Exception as e:
            logger.error(f"Error stopping driver: {str(e)}")
            return jsonify({"error": "Error stopping tracking"}), 500
    else:
        return jsonify({"error": "No tracking in progress"}), 404

@app.route("/get_status/<name>", methods=["GET"])
def get_status(name):
    if name in status_data:
        return jsonify(status_data[name])
    return jsonify({"error": "No data for this name"}), 404

@app.route("/get_history/<name>", methods=["GET"])
def get_history(name):
    if name not in status_data:
        return jsonify({"error": "No data for this name"}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    history = status_data[name].get('history', [])
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    return jsonify({
        'history': history[start_idx:end_idx],
        'total': len(history),
        'has_more': end_idx < len(history)
    })

@app.route("/clear_data/<name>", methods=["POST"])
def clear_data(name):
    global status_data
    if name in status_data:
        del status_data[name]
        save_data()
        return jsonify({"message": f"Data cleared for {name}"})
    return jsonify({"error": "No data found for this name"}), 404

if __name__ == "__main__":
    load_saved_data()
    app.run(debug=True)
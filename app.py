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
import sys
import traceback
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('severity'):
            log_record['severity'] = record.levelname
        if not log_record.get('message') and record.msg:
            log_record['message'] = record.msg

# Configure logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()

# Custom formatter that will ignore Flask's werkzeug logs
formatter = CustomJsonFormatter(
    '%(severity)s %(message)s',
    json_ensure_ascii=False
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Add this to suppress Flask's default logging
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.disabled = True

# Modify Flask's logging
cli = sys.modules.get('flask.cli')
if cli is not None:
    cli.show_server_banner = lambda *args: None

app = Flask(__name__)
app.logger.handlers = []
app.logger.propagate = False

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
            logger.info("Status data loaded successfully")
    except Exception as e:
        logger.error(f"Error loading saved data: {str(e)}")

# Save data periodically
def save_data():
    global status_data
    try:
        with open(data_file, 'w') as f:
            json.dump(status_data, f)
        logger.info("Status data saved")
    except Exception as e:
        logger.error(f"Error saving data: {e}")

def create_driver():
    try:
        chrome_profile_dir = os.path.join(os.path.expanduser("~"), "ChromeProfile")
        
        # Check if Chrome profile directory exists
        if not os.path.exists(chrome_profile_dir):
            os.makedirs(chrome_profile_dir)
            logger.info(f"Created Chrome profile directory at {chrome_profile_dir}")
            
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={chrome_profile_dir}")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        # Add these options to help prevent crashes
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Use webdriver_manager to handle driver installation
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set window size and position
        driver.set_window_rect(0, 0, 800, 600)
        
        return driver
        
    except Exception as e:
        logger.error(f"Error creating Chrome driver: {str(e)}")
        raise Exception(f"Failed to create Chrome driver: {str(e)}")

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
        driver = create_driver()
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
                # Periodically refresh the visibility override
                driver.execute_script("""
                document.dispatchEvent(new Event('visibilitychange'));
                document.dispatchEvent(new Event('focus'));
                """)
                
                # Updated online status indicators with more specific selectors
                online_indicators = [
                    "//span[contains(@title, 'online')]",
                    "//span[contains(@title, 'typing...')]",
                    "//span[text()='online']",
                    "//span[text()='typing...']",
                    "//div[contains(@class, '_3vPI2')]//span[contains(text(), 'online')]",
                    "//div[contains(@class, 'zzgSd')]//span[contains(text(), 'online')]",
                    "//div[contains(@class, 'YmixP')]//span[contains(text(), 'online')]"
                ]
                
                is_online = False
                for indicator in online_indicators:
                    try:
                        elements = driver.find_elements(By.XPATH, indicator)
                        if elements:
                            is_online = True
                            logger.info(f"Online status detected via selector: {indicator}")
                            break
                    except Exception as e:
                        logger.error(f"Error checking indicator {indicator}: {str(e)}")
                        continue
                
                # Force focus on the chat window
                driver.execute_script("""
                // Force focus on chat window
                document.querySelector('div[tabindex="-1"]')?.focus();
                // Ensure chat is visible
                document.querySelector('div[data-tab="1"]')?.scrollIntoView();
                """)
                
                current_time = datetime.now()
                status = "Online" if is_online else "Offline"
                
                # Debug logging
                logger.info(f"Current status for {name}: {status}")
                
                # Update current status
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
                            'timestamp': current_time.isoformat()
                        }
                    }
                
                status_data[name]['current'] = {
                    'status': status,
                    'timestamp': current_time.isoformat()
                }
                
                # Fixed parentheses in the condition check
                should_update = (
                    not status_data[name]['history'] or 
                    status_data[name]['history'][-1]['status'] != status or 
                    (current_time - datetime.fromisoformat(status_data[name]['history'][-1]['timestamp'].replace('Z', '+00:00'))).total_seconds() > 300
                )
                
                if should_update:
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
                logger.error(f"Error in update_status: {str(e)}")
            
            time.sleep(2)
            
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
    try:
        # Configure logging first
        logging.basicConfig(level=logging.ERROR)
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.disabled = True
        app.logger.disabled = True
        
        # Load data
        load_saved_data()
        
        startup_message = f"""
\033[38;5;196mW\033[38;5;202mh\033[38;5;208ma\033[38;5;214mt\033[38;5;220ms\033[38;5;226mA\033[38;5;190mp\033[38;5;154mp\033[38;5;118m Status \033[38;5;82mTracker \033[38;5;196m⚠️  Not supported anymore

\033[38;5;51mAuthor: \033[38;5;227m@remcostoeten
\033[38;5;51mGitHub: \033[38;5;227mhttps://github.com/remcostoeten

\033[38;5;213mTech Stack:
\033[38;5;159m• Backend:  Python + Flask
\033[38;5;159m• Frontend: HTML + Tailwind + Chart.js

\033[38;5;213mApplication running at: \033[38;5;159mhttp://localhost:5000\033[0m
"""
        print(startup_message)
        
        # Start the Flask app with minimal logging
        app.run(debug=False, host="127.0.0.1", port=5000)
        
    except Exception as e:
        print("\033[91mError starting server:\033[0m")
        print(f"\033[91m{str(e)}\033[0m")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)

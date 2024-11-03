# WhatsApp Online Status Tracker

> [!WARNING]
> Do not use this for stalking purposes. Trust me, you're better off moving on. Time will heal all wounds.

### This tool is intended for educational and personal use only. It should not be used for stalking, harassment, or any other activities that violate the privacy rights of individuals. Please respect the privacy of others and use this tool responsibly.

---

This tool starts up a Chrome (driver) instance and goes to WhatsApp Web. You don't want to authenticate every time, and since each chromedriver reboot resets the browser, you need to create a Chrome profile. Do so by running `google-chrome --user-data-dir=/path/to/your/new/profile` in the root of the project. Navigate to WhatsApp, authenticate, and optionally install extensions like WhatsApp Plus to hide blue checkmarks.

> [!NOTE]
> This project is no longer actively maintained. Feel free to fork and adapt for your needs.
<small>Works on my machine which is PopOS (ubuntu) with these versions.</small>

```bash
pop-os% chromedriver --v ; python3 --version ; pip --version
ChromeDriver 130.0.6723.0 (ed44bc873f9ef776a2ef1ccb90252a6de5666cd6-refs/branch-heads/6723@{#1})
Python 3.10.12
pip 22.0.2 from /usr/lib/python3/dist-packages/pip (python 3.10)
```
glhf

## Running the app
```bash
pip install -r requirements.txt
# or pip3. If having issues, look into app.py, copy the imports into chatgpt and ask for pip installs
```
Then you should be able to run the app with `python app.py` or `./start.sh` which then serves a server on `localhost:5000`.

## 📋 Features

- Real-time online/offline status tracking
- Visual timeline of activity
- Daily pattern analysis
- Detailed statistics
- Historical data tracking
- Data export functionality
- Responsive web interface

## 🔧 Detailed Prerequisites

### Chrome and ChromeDriver Setup

The application requires specific versions of Chrome and ChromeDriver that match. Here's how to set them up correctly:

#### Windows

1. Check your Chrome version:
   - Open Chrome
   - Click the three dots (⋮) in the top-right corner
   - Go to Help > About Google Chrome
   - Note down the version number (e.g., 130.0.6723.91)

2. Install ChromeDriver:
```shell
# Method 1: Using ChromeDriver Manager (Recommended)
pip install webdriver-manager

# Method 2: Manual Installation
# 1. Go to https://googlechromelabs.github.io/chrome-for-testing/
# 2. Download the ChromeDriver version matching your Chrome version
# 3. Extract the zip file
# 4. Add the ChromeDriver location to your PATH:
#    - Right-click 'This PC' > Properties > Advanced system settings
#    - Click 'Environment Variables'
#    - Under 'System variables', find and select 'Path'
#    - Click 'Edit' > 'New'
#    - Add the path to your ChromeDriver folder
#    - Click 'OK' on all windows
```

3. Verify ChromeDriver installation:
```shell
chromedriver --version
# Should output something like: ChromeDriver 130.0.6723.0
```

#### macOS

1. Check Chrome version:
```shell
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

2. Install ChromeDriver:
```shell
# Method 1: Using Homebrew (Recommended)
brew install --cask chromedriver

# Method 2: Using ChromeDriver Manager
pip install webdriver-manager

# Method 3: Manual Installation
# 1. Visit https://googlechromelabs.github.io/chrome-for-testing/
# 2. Download matching ChromeDriver version
# 3. Extract the zip file
# 4. Move ChromeDriver to /usr/local/bin:
sudo mv chromedriver /usr/local/bin/
sudo xattr -d com.apple.quarantine /usr/local/bin/chromedriver
```

3. Verify installation:
```shell
chromedriver --version
```

### Troubleshooting Chrome/ChromeDriver Issues

#### Common Error 1: Version Mismatch
```
SessionNotCreatedException: Message: session not created: This version of ChromeDriver only supports Chrome version XX
```

Solution:
```shell
# 1. Uninstall existing ChromeDriver
pip uninstall webdriver-manager
rm -f /usr/local/bin/chromedriver  # macOS
del chromedriver.exe               # Windows

# 2. Update Chrome to latest version

# 3. Reinstall ChromeDriver
pip install webdriver-manager
```

#### Common Error 2: Executable Path Error
```
WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

Solution:
```shell
# Windows - Add to PATH manually:
setx PATH "%PATH%;C:\path\to\chromedriver"

# macOS - Create symlink:
sudo ln -s /path/to/chromedriver /usr/local/bin/chromedriver
```

#### Common Error 3: Permission Issues (macOS)
```
OSError: [Errno 13] Permission denied: 'chromedriver'
```

Solution:
```shell
# Fix permissions
sudo chmod +x /usr/local/bin/chromedriver
sudo xattr -d com.apple.quarantine /usr/local/bin/chromedriver
```

#### Common Error 4: THIRD_PARTY_NOTICES Error
```
OSError: [Errno 8] Exec format error: '.../THIRD_PARTY_NOTICES.chromedriver'
```

Solution:
```shell
# 1. Remove the webdriver-manager cache:
rm -rf ~/.wdm/drivers/chromedriver/  # macOS/Linux
rd /s /q %USERPROFILE%\.wdm\drivers\chromedriver  # Windows

# 2. Manually download ChromeDriver and specify path in app.py:
driver_path = "/absolute/path/to/chromedriver"  # Update in app.py
```

## 💻 Installation

### Windows

1. Install Python from the official website:
```shell
# Download Python from https://www.python.org/downloads/windows/
# During installation, check "Add Python to PATH"
```

2. Clone or download the repository:
```shell
git clone https://github.com/remcostoeten/whatsapp-online-status-tracker.git whatsapp-tracker
cd whatsapp-tracker
```

3. Install dependencies:
```shell
pip install -r requirements.txt
# or pip3. If having issues, look into app.py, copy the imports into chatgpt and ask for pip installs
```

4. Create and activate virtual environment:
```shell
python -m venv venv
.\venv\Scripts\activate
```

5. Install dependencies:
```shell
pip install -r requirements.txt
```

### macOS

1. Install Homebrew (if not installed):
```shell
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Install Python and Chrome:
```shell
brew install python
brew install --cask google-chrome
```

3. Clone or download the repository:
```shell
git clone https://github.com/remcostoeten/whatsapp-online-status-tracker.git
cd whatsapp-online-status-tracker
```

4. Create and activate virtual environment:
```shell
python3 -m venv venv
source venv/bin/activate
```

5. Install dependencies:
```shell
pip install -r requirements.txt
```

## 🚀 Usage

1. Start the application:
```shell
python app.py
## or
./start.sh
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. Steps to track a contact:
   - Open WhatsApp Web and scan the QR code
   - Enter the exact contact name as it appears in WhatsApp
   - Click "Start Tracking"
   - The application will begin monitoring the contact's online status

## 📁 Project Structure

```
whatsapp-tracker/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── README.md             # Documentation
└── templates/            # HTML templates
    ├── error.html        # Error page template
    ├── index.html        # Main application interface
    └── result.html       # Results display template
```

## ⚙️ Advanced Configuration

### Custom ChromeDriver Options

You can modify the ChromeDriver options in `app.py`:

```python
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")  # Needed for some Windows setups
chrome_options.add_argument("--remote-debugging-port=9222")  # For debugging

# For headless mode (no GUI):
# chrome_options.add_argument("--headless")
```

### Environment Variables

Create a `.env` file in your project root:
```shell
CHROME_DRIVER_PATH=/path/to/chromedriver
FLASK_ENV=development
DEBUG_MODE=True
```

### Data Storage Configuration

The application stores data in:
- Windows: `%APPDATA%/whatsapp-tracker/`
- macOS: `~/Library/Application Support/whatsapp-tracker/`

You can modify this in `app.py`:
```python
data_dir = os.path.expanduser("~/whatsapp-tracker-data")
os.makedirs(data_dir, exist_ok=True)
```

## 🤝 Contributing

Contributions were welcome, but as this project is no longer maintained, consider forking the repository for your own modifications.

## 🙏 Acknowledgments

- Flask framework
- Selenium WebDriver
- Chart.js
- Tailwind CSS

## 📧 Contact

For historical reference only - no active support is provided.

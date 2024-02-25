## WhatsApp online status tracker

> [!WARNING]
> Do not use this for stalking purposes. Trust me, you're better off moving on. Time will heal all wounds.

### This tool is intended for educational and personal use only. It should not be used for stalking, harassment, or any other activities that violate the privacy rights of individuals. Please respect the privacy of others and use this tool responsibly.

---

This tool starts up a Chrome (driver) instance and goes to WhatsApp Web. You don't want to authenticate every time, and since each chromedriver reboot resets the browser, you need to create a Chrome profile. Do so by running `google-chrome --user-data-dir=/path/to/your/new/profile` in the root of the project. Navigate to WhatsApp, authenticate, and optionally install extensions like WhatsApp Plus to hide blue checkmarks.

## Requirements

> Download chromedriver from [here](https://chromedriver.chromium.org/downloads).

> Have Python 3 installed.

## Run Locally

btw,runs fine on my machine. Linux, PopOS.

1. Clone the project:

```bash
git clone https://github.com/remcostoeten/whatsapp-online-status-tracker.git
cd whatsapp-online-status-tracker
```

2. Create a new Chrome profile:

```bash
google-chrome --user-data-dir=~/chrome-profile                                                                                                                                                                                                          ```

Navigate to WhatsApp Web in the new Chrome instance, authenticate, and optionally install extensions like WhatsApp Plus to hide blue checkmarks.

3. Install the Python dependencies:
```bash
pip install -r requirements.txt
```

4. Start the server:

```bash
python app.py
### or python3 app.py. Have struggled with that in the past if you're new. 🙃
```

Now, you can navigate to `http://localhost:5000` in your web browser to use the application.

### Roadmap

I have a React/NextJS API route working which I might make available someday. Also displaying data, e.g. logging, doesn't do anything on the front-end. Logs are filled in JSON format so you can API yourself in the root.

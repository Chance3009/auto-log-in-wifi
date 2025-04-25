import subprocess
import time
import platform
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from plyer import notification

MAX_ATTEMPTS = 3
TARGET_WIFI = "PutraNet"
CREDENTIALS_PATH = r"credentials.json" # 
CHROME_DRIVER_PATH = r"C:\Program Files\chromedriver-win64\chromedriver.exe"

# ----------------------------- Utils -----------------------------


def log_step(msg):
    now = time.strftime("%H:%M:%S")
    print(f"[{now}] {msg}")


def notify(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=3
    )

# -----------------------------------------------------------------


def get_connected_wifi():
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True
        )
        for line in result.stdout.split("\n"):
            if "SSID" in line and "BSSID" not in line:
                return line.split(":")[1].strip()
    except Exception as e:
        log_step(f"⚠️ Error checking Wi-Fi: {e}")
    return None


def has_internet():
    command = ["ping", "-c", "1", "google.com"] if platform.system(
    ) != "Windows" else ["ping", "google.com", "-n", "1"]
    try:
        subprocess.check_call(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def read_credentials(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def auto_login():
    credentials = read_credentials(CREDENTIALS_PATH)
    username = credentials.get("username")
    password = credentials.get("password")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")

    service = Service(executable_path=CHROME_DRIVER_PATH, log_output="NUL")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    attempts = 0

    while attempts < MAX_ATTEMPTS:
        try:
            log_step(f"[{attempts+1}] Navigating to login page...")
            driver.get("http://neverssl.com")

            log_step(f"[{attempts+1}] Page title: {driver.title}")
            log_step(f"[{attempts+1}] Current URL: {driver.current_url}")

            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                log_step(f"[{attempts+1}] ✅ Login form detected.")
            except Exception as wait_error:
                log_step(f"[{attempts+1}] ⏱️ Timeout: Login form not found.")
                raise wait_error

            log_step(f"[{attempts+1}] Submitting credentials...")
            username_field = driver.find_element(By.ID, "username")
            password_field = driver.find_element(By.ID, "password")
            login_button = driver.find_element(By.ID, "loginBtn")

            username_field.send_keys(username)
            password_field.send_keys(password)
            login_button.click()

            log_step(
                f"[{attempts+1}] 🧠 Clicked login button. Waiting for redirect...")
            time.sleep(3)

            final_url = driver.current_url
            log_step(f"[{attempts+1}] 🔁 Final URL after login: {final_url}")

            if driver.find_elements(By.ID, "loginBtn"):
                log_step(
                    f"[{attempts+1}] ⚠️ Still on login page. Login may have failed.")
            else:
                log_step(
                    f"[{attempts+1}] ✅ Redirected. Login might have succeeded.")

            notify(f"{TARGET_WIFI} AutoLogin", "Logged in successfully!")
            log_step("✅ Logged in successfully!")
            break

        except Exception as e:
            attempts += 1
            log_step(f"❌ Login attempt {attempts} failed: {e}")

            try:
                driver.save_screenshot(f"login_fail_attempt{attempts}.png")
                with open(f"login_fail_attempt{attempts}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                log_step(
                    f"📸 Screenshot and HTML saved for attempt {attempts}.")
            except:
                log_step("⚠️ Could not save snapshot.")

            if attempts >= MAX_ATTEMPTS:
                log_step("🚫 Max login attempts reached. Exiting.")
                notify(f"{TARGET_WIFI} AutoLogin", "Max login attempts reached.")
                break

        time.sleep(2)

    driver.quit()


def should_stop():
    wifi = get_connected_wifi()
    if not wifi:
        log_step("No Wi-Fi connection detected. Exiting.")
        return True
    return False


# ------------------------ Main Execution -------------------------


def main():
    start_time = time.time()

    while True:
        current_wifi = get_connected_wifi()
        log_step(f"Detected Wi-Fi: {current_wifi}")

        if current_wifi and TARGET_WIFI.lower() in current_wifi.lower():
            if not has_internet():
                log_step(
                    f"Connected to {current_wifi} but no internet. Attempting login...")
                notify(f"{TARGET_WIFI} AutoLogin",
                       f"Connected to {current_wifi}. Logging in...")
                auto_login()
            else:
                log_step(
                    f"Already connected to the internet via {current_wifi}.")
                notify(f"{TARGET_WIFI} AutoLogin",
                       f"Already online via {current_wifi}.")
            break

        if should_stop():
            break

        time.sleep(10)

    end_time = time.time()
    duration = end_time - start_time
    minutes, seconds = divmod(duration, 60)
    summary = f"Script run duration: {int(minutes)} minutes and {int(seconds)} seconds."
    log_step(summary)
    notify(f"{TARGET_WIFI} AutoLogin", summary)


if __name__ == "__main__":
    main()

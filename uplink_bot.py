#!/usr/bin/env python3
import requests, time, json, random, string, csv, logging
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import names

# === CONFIGURATION (edit these before running) ===
MAILSLURP_API_KEY = "YOUR_MAILSLURP_API_KEY"
CAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY"
REFERRAL_CODE    = "cCgXtH"  # Use your referral code

# ISP options for simulated routers
ISP_LIST = ["Globe", "PLDT", "Converge", "Sky", "DITO", "Bayantel"]

ua = UserAgent()
logging.basicConfig(filename="uplink_log.txt",
                    format="%(asctime)s %(levelname)s: %(message)s",
                    level=logging.INFO)
logger = logging.getLogger()

# Random router name
def gen_router_name():
    return "Router_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# Random PH lat/lon
def rand_location():
    return round(random.uniform(13.0, 15.0), 6), round(random.uniform(120.0, 122.0), 6)

# Create email using MailSlurp
def create_email():
    for attempt in range(3):
        try:
            resp = requests.post(
                "https://api.mailslurp.com/inboxes",
                headers={"x-api-key": MAILSLURP_API_KEY},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            return data["id"], data["emailAddress"]
        except Exception as e:
            logger.warning("MailSlurp inbox creation failed, retrying… (%s)", e)
            time.sleep(5)
    raise Exception("MailSlurp failed after retries")

# Poll for verification email
def wait_email(inbox_id, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"https://api.mailslurp.com/inboxes/{inbox_id}/emails?unreadOnly=true",
            headers={"x-api-key": MAILSLURP_API_KEY}, timeout=5
        )
        email_list = resp.json()
        if email_list:
            email_id = email_list[0]["id"]
            body = requests.get(
                f"https://api.mailslurp.com/emails/{email_id}", headers={"x-api-key": MAILSLURP_API_KEY}
            ).json()["body"]
            
            soup = BeautifulSoup(body, "html.parser")
            for a in soup.find_all("a", href=True):
                if "confirm" in a["href"]:
                    return a["href"]
        time.sleep(5)
    raise Exception("Timed out waiting for verification email")

# Solve hCaptcha with 2Captcha
def solve_captcha(sitekey, pageurl):
    s = requests.post("http://2captcha.com/in.php", data={
        "key": CAPTCHA_API_KEY,
        "method": "hcaptcha",
        "sitekey": sitekey,
        "pageurl": pageurl,
        "json": 1
    }, timeout=10).json()
    
    if s["status"] != 1:
        raise Exception("2Captcha API error: " + str(s))
    captcha_id = s["request"]
    for _ in range(20):
        time.sleep(5)
        r = requests.get(
            "http://2captcha.com/res.php",
            params={"key": CAPTCHA_API_KEY, "action": "get", "id": captcha_id, "json": 1},
            timeout=10
        ).json()
        if r["status"] == 1:
            return r["request"]
    raise Exception("Captcha solve timeout")

# Register account + router
def register_account():
    inbox_id, email = create_email()
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    logger.info("Registering %s", email)

    sitekey = "3f21c7a4-07d7-4c14-9c51-8db14ba38f07"
    token = solve_captcha(sitekey, "https://portal.uplink.xyz/register")

    payload = {
        "email": email,
        "password": password,
        "referralCode": REFERRAL_CODE,
        "hcaptchaToken": token
    }
    headers = {
        "User-Agent": ua.random,
        "Content-Type": "application/json"
    }
    resp = requests.post(
        "https://portal.uplink.xyz/api/auth/register",
        json=payload, headers=headers, timeout=10
    )
    resp.raise_for_status()
    logger.info("Registered: %s, status=%s", email, resp.status_code)

    link = wait_email(inbox_id)
    requests.get(link, headers={"User-Agent": ua.random}, timeout=10)
    logger.info("Verified email for %s", email)

    lat, lon = rand_location()
    router = gen_router_name()
    isp = random.choice(ISP_LIST)
    logger.info("Registering router '%s', ISP=%s, lat=%.6f lon=%.6f", router, isp, lat, lon)

    # Placeholder for router registration. Uplink backend might not support web registration.
    # You can expand this by reverse-engineering the explorer API.
    # For now, we log the intent only.
    
    return {
        "email": email,
        "password": password,
        "router": router,
        "lat": lat,
        "lon": lon,
        "isp": isp
    }

def main():
    count = int(input("How many accounts/routers to create (1‑1000)? ").strip())
    accounts = []
    for i in range(count):
        try:
            acc = register_account()
            accounts.append(acc)
            print(f"[{i+1}/{count}] {acc['email']} | {acc['router']} OK")
        except Exception as e:
            logger.error("Error creating account #%d: %s", i+1, e)
            print(f"[!] Failed account #{i+1}: {e}")

    with open("uplink_accounts.json", "w") as j:
        json.dump(accounts, j, indent=2)
    with open("uplink_accounts.csv", "w", newline="") as c:
        writer = csv.DictWriter(c, fieldnames=accounts[0].keys())
        writer.writeheader()
        writer.writerows(accounts)

    print("✔ Done! Check uplink_accounts.json, .csv, uplink_log.txt")

if __name__ == "__main__":
    main()

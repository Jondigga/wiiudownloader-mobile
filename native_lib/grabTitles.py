#!/usr/bin/env python3
import os
import ssl
import sys
import time
import urllib.request

URL = os.environ.get("WIIU_DB_URL", "https://napi.v10lator.de/db?t=go")
DEST_PATH = os.path.join(os.path.dirname(__file__), "db.go")
USER_AGENT = "NUSspliBuilder/2.1"
MAX_ATTEMPTS = 3
REQUEST_TIMEOUT = 30


def check_and_delete_file(path):
    if os.path.exists(path):
        print(f"Deleting {path}")
        os.remove(path)


def write_fallback_db():
    content = (
        'package main\n\n'
        'import wiiudownloader "github.com/Xpl0itU/WiiUDownloader"\n\n'
        'var titleEntry = []wiiudownloader.TitleEntry{}\n'
    )
    with open(DEST_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created fallback {DEST_PATH}; build will continue without an online title database.")


def fetch_title_database():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
    opener.addheaders = [("User-agent", USER_AGENT)]
    urllib.request.install_opener(opener)

    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"Downloading db.go (attempt {attempt}/{MAX_ATTEMPTS}) from {URL}...")
            req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content_bytes = response.read()

            if not content_bytes:
                raise ValueError("Downloaded response was empty")

            content = content_bytes.decode("utf-8")
            if "var titleEntry" not in content:
                raise ValueError("Downloaded payload did not contain the expected titleEntry section")

            before, sep, after = content.partition("var titleEntry")
            generated = "package main\nimport wiiudownloader \"github.com/Xpl0itU/WiiUDownloader\"\n" + sep + after
            generated = generated.replace("[]TitleEntry{", "[]wiiudownloader.TitleEntry{")

            with open(DEST_PATH, "w", encoding="utf-8") as f:
                f.write(generated)

            print(f"Database saved to {DEST_PATH}")
            return True
        except Exception as exc:  # pragma: no cover - keeps CI resilient
            last_error = exc
            print(f"Fetch attempt {attempt} failed: {exc}", file=sys.stderr)
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 ** attempt)

    print(f"Unable to download title database from {URL}: {last_error}", file=sys.stderr)
    if os.path.exists(DEST_PATH):
        print(f"Using existing database file at {DEST_PATH}")
        return False

    write_fallback_db()
    return False


def main():
    if os.path.exists(DEST_PATH):
        print(f"Using existing {DEST_PATH}")
        return 0

    fetch_title_database()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

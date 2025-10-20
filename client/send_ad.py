import argparse
import os
import sys
from typing import List
import http.server
import threading
import webbrowser
import socket
import functools

import requests

# Support running both as a package (python -m client.send_ad) and as a script from the client/ directory
try:
    from client.config import SERVER_URL, API_KEY  # when executed from project root
except ModuleNotFoundError:
    from config import SERVER_URL, API_KEY  # when executed directly inside the client/ folder


def send_ad(
    model: str,
    manufacture_year: str,
    price: str,
    location: str,
    price_type: str,
    phone: str,
    condition: str,
    image_paths: List[str],
):
    url = f"{SERVER_URL}/api/ads"
    files = []
    for p in image_paths:
        if not os.path.isfile(p):
            print(f"Skipping missing image: {p}", file=sys.stderr)
            continue
        files.append(("images", (os.path.basename(p), open(p, "rb"), "image/jpeg")))

    data = {
        "model": model,
        "manufacture_year": manufacture_year,
        "price": price,
        "location": location,
        "price_type": price_type,
        "phone": phone,
        "condition": condition,
    }

    headers = {}
    if API_KEY:
        headers["x-api-key"] = API_KEY

    resp = requests.post(url, data=data, files=files, headers=headers, timeout=120)
    resp.raise_for_status()
    print(resp.json())


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_ui():
    # Serve the client directory and open index.html in the default browser
    client_dir = os.path.dirname(os.path.abspath(__file__))
    port = _find_free_port()

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=client_dir)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}/index.html"
    print(f"Opening UI at {url}")
    webbrowser.open(url)

    try:
        # Keep the main thread alive to serve until user stops with Ctrl+C
        print("Press Ctrl+C to stop the UI server.")
        while True:
            thread.join(1)
    except KeyboardInterrupt:
        print("\nShutting down UI server...")
        server.shutdown()
        server.server_close()


def main():
    # Launch the local UI instead of using CLI arguments
    run_ui()


if __name__ == "__main__":
    main()
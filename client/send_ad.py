import argparse
import os
import sys
from typing import List

import requests

from client.config import SERVER_URL, API_KEY


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


def main():
    parser = argparse.ArgumentParser(description="Upload vehicle ad details and images to Ganudenu.store API server.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--manufacture_year", required=True)
    parser.add_argument("--price", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--price_type", required=True, choices=["Negotiable", "Fixed"])
    parser.add_argument("--phone", required=True)
    parser.add_argument("--condition", required=True)
    parser.add_argument("--images", nargs="+", required=True, help="Paths to 3-9 image files")

    args = parser.parse_args()
    if len(args.images) < 3:
        parser.error("Please provide at least 3 images")

    send_ad(
        model=args.model,
        manufacture_year=args.manufacture_year,
        price=args.price,
        location=args.location,
        price_type=args.price_type,
        phone=args.phone,
        condition=args.condition,
        image_paths=args.images,
    )


if __name__ == "__main__":
    main()
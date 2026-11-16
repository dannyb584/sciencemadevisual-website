#!/usr/bin/env python3
"""Add a Lunchbox Designs product to the shop feed in one command.

The feed is shop/products.json. The website's Shop grid and the SMV Pharmacology
app both read it from https://www.sciencemadevisual.co.uk/shop/products.json, so
adding a product here updates both once it is pushed to main.

    python3 scripts/add_shop_product.py \\
        --title "Tablet Transporter: Giant Tablet 7-Day Trinket Box" \\
        --price "£19.99" \\
        --url "https://www.etsy.com/uk/listing/4618693468" \\
        --photo "/path/to/real/photo.jpg"

Options:
    --id slug       the product id and image name (made from the title if left out)
    --date Y-M-D    the "added" date (today if left out)
    --dry-run       show what would happen without writing anything
    --push          commit on main and push, so it goes live

What it does: makes the slug, turns the photo into a square 800 px sRGB JPEG with
no EXIF or GPS (images/shop/<id>.jpg, under about 150 KB), puts the product at the
top of shop/products.json with today's "added" date, sets "updated", and refuses a
listing that is already in the feed. Needs only Python 3 and macOS's sips.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

SITE = "https://www.sciencemadevisual.co.uk"
REPO = Path(__file__).resolve().parent.parent
FEED = REPO / "shop" / "products.json"
IMAGE_DIR = REPO / "images" / "shop"
SIZE = 800                      # px, square
MAX_BYTES = 150 * 1024          # keep each product photo under about 150 KB
QUALITIES = (82, 76, 70, 64, 58, 52)
SRGB = Path("/System/Library/ColorSync/Profiles/sRGB Profile.icc")
KEYS = ("id", "title", "price", "url", "image", "added")


def fail(message: str) -> None:
    print(f"Stopped: {message}", file=sys.stderr)
    sys.exit(1)


# ── Text and URL clean-up ─────────────────────────────────────────────────────

def slugify(title: str) -> str:
    """'Tablet Transporter: Giant Tablet 7-Day Trinket Box' -> 'tablet-transporter'.

    Uses the product name before the first ':', '|' or spaced dash, so ids stay short.
    """
    name = re.split(r"\s*(?::|\||\s[\u2014\u2013-]\s)\s*", title.strip(), maxsplit=1)[0]
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return slug


def clean_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme != "https" or parts.netloc not in ("www.etsy.com", "etsy.com"):
        fail(f"the url should be an https Etsy listing link, not {url!r}")
    if not listing_id(parts.path):
        fail(f"the url has no /listing/<number> in it: {url!r}")
    # Drop tracking (?ref=..., #...) so the same listing always looks the same
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


def listing_id(url_or_path: str) -> str | None:
    match = re.search(r"/listing/(\d+)", url_or_path)
    return match.group(1) if match else None


def clean_price(price: str) -> str:
    raw = price.strip().replace(",", "")
    if raw.startswith("£"):
        raw = raw[1:]
    try:
        value = Decimal(raw)
    except InvalidOperation:
        fail(f"the price should look like £19.99, not {price!r}")
    if value <= 0:
        fail(f"the price should be more than £0, not {price!r}")
    return f"£{value:.2f}"


def check_date(text: str) -> str:
    try:
        return dt.date.fromisoformat(text).isoformat()
    except ValueError:
        fail(f"the date should be YYYY-MM-DD, not {text!r}")


# ── Feed ──────────────────────────────────────────────────────────────────────

def load_feed() -> dict:
    if not FEED.exists():
        return {"updated": dt.date.today().isoformat(), "products": []}
    try:
        feed = json.loads(FEED.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        fail(f"{FEED} is not valid JSON ({err}); fix it before adding more")
    if not isinstance(feed, dict) or not isinstance(feed.get("products"), list):
        fail(f'{FEED} should be {{"updated": ..., "products": [...]}}')
    for i, product in enumerate(feed["products"]):
        missing = [k for k in KEYS if not product.get(k)]
        if missing:
            fail(f"product {i + 1} in {FEED.name} is missing {', '.join(missing)}")
    return feed


def write_feed(feed: dict) -> None:
    FEED.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(feed, ensure_ascii=False, indent=2) + "\n"
    tmp = FEED.with_suffix(".json.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, FEED)


def refuse_duplicates(feed: dict, product_id: str, url: str) -> None:
    new_listing = listing_id(url)
    for p in feed["products"]:
        if p["url"].rstrip("/") == url or listing_id(p["url"]) == new_listing:
            fail(f"that Etsy listing is already in the feed as {p['id']!r} ({p['title']})")
        if p["id"] == product_id:
            fail(f"the id {product_id!r} is taken by {p['title']!r}; pass a different --id")


# ── Photo ─────────────────────────────────────────────────────────────────────

def sips(*args: str) -> str:
    if not shutil.which("sips"):
        fail("sips was not found; this script needs macOS to resize the photo")
    result = subprocess.run(["sips", *args], capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"sips could not process the photo:\n{result.stderr.strip()}")
    return result.stdout


def photo_info(path: Path) -> dict:
    out = sips("-g", "pixelWidth", "-g", "pixelHeight", str(path))
    info = dict(re.findall(r"^\s+(\w+): (.+)$", out, flags=re.M))
    return {"w": int(info["pixelWidth"]), "h": int(info["pixelHeight"])}


def tiff_orientation(path: Path) -> int:
    """The EXIF orientation (1 to 8) in the TIFF that sips wrote.

    sips keeps a phone photo's rotation tag but does not turn the pixels, and the tag
    is stripped at the end, so the pixels have to be turned upright here first.
    """
    data = path.read_bytes()
    order = {b"II": "<", b"MM": ">"}.get(data[:2])
    if not order:
        return 1
    try:
        ifd = struct.unpack(order + "I", data[4:8])[0]
        count = struct.unpack(order + "H", data[ifd:ifd + 2])[0]
        for k in range(count):
            entry = ifd + 2 + 12 * k
            tag = struct.unpack(order + "H", data[entry:entry + 2])[0]
            if tag == 0x0112:
                value = struct.unpack(order + "H", data[entry + 8:entry + 10])[0]
                return value if 1 <= value <= 8 else 1
    except struct.error:
        pass
    return 1


def pick_photo(photo: Path) -> Path:
    """Prefer the matching square crop (Photos/square/<name>_1x1.jpg) when there is one."""
    info = photo_info(photo)
    if info["w"] == info["h"]:
        return photo
    for ext in (photo.suffix, ".jpg", ".jpeg", ".png"):
        square = photo.parent / "square" / f"{photo.stem}_1x1{ext}"
        if square.exists():
            print(f"Using the square crop beside it: {square}")
            return square
    print("No square crop found beside the photo, so it will be cropped to a centred square.")
    return photo


# EXIF orientation -> sips steps that turn the pixels upright
ORIENT_STEPS = {
    2: [("-f", "horizontal")],
    3: [("-r", "180")],
    4: [("-f", "vertical")],
    5: [("-r", "90"), ("-f", "horizontal")],
    6: [("-r", "90")],
    7: [("-r", "270"), ("-f", "horizontal")],
    8: [("-r", "270")],
}


def strip_jpeg_metadata(data: bytes) -> bytes:
    """Keep only what a browser needs to draw the JPEG.

    Drops EXIF and GPS (APP1), XMP, IPTC, comments and any extra image stuck on the
    end (such as an iPhone gain map), and keeps the JFIF header and the ICC colour profile.
    """
    if data[:2] != b"\xff\xd8":
        fail("the processed photo is not a JPEG")
    out = bytearray(b"\xff\xd8")
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            fail("the processed photo has a damaged JPEG header")
        marker = data[i + 1]
        if marker == 0xFF:                      # padding byte
            i += 1
            continue
        if marker == 0xDA:                      # start of scan: copy the image data up to the end marker
            end = find_eoi(data, i)
            out += data[i:end]
            return bytes(out)
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        segment = data[i:i + 2 + length]
        body = segment[4:]
        keep = True
        if 0xE1 <= marker <= 0xEF or marker == 0xFE:
            keep = marker == 0xE2 and body.startswith(b"ICC_PROFILE\x00")
        if keep:
            out += segment
        i += 2 + length
    fail("the processed photo has no image data")


def find_eoi(data: bytes, start: int) -> int:
    """Index just past the first end-of-image marker (scan data never holds a bare FFD9)."""
    j = data.find(b"\xff\xd9", start + 2)
    return len(data) if j == -1 else j + 2


def make_image(photo: Path, dest: Path) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "work.tiff"            # lossless between steps
        args = ["-s", "format", "tiff"]
        if SRGB.exists():
            args += ["-m", str(SRGB)]
        sips(*args, str(photo), "--out", str(work))

        for step in ORIENT_STEPS.get(tiff_orientation(work), []):
            sips(*step, str(work))

        info = photo_info(work)
        side = min(info["w"], info["h"])
        if info["w"] != info["h"]:
            sips("-c", str(side), str(side), str(work))   # centred square
        if side > SIZE:
            sips("-z", str(SIZE), str(SIZE), str(work))
        elif side < 400:
            print(f"Note: the photo is only {side} px wide, so it may look soft on the site.")

        jpeg = Path(tmp) / "out.jpg"
        for quality in QUALITIES:
            sips("-s", "format", "jpeg", "-s", "formatOptions", str(quality), str(work), "--out", str(jpeg))
            data = strip_jpeg_metadata(jpeg.read_bytes())
            if len(data) <= MAX_BYTES:
                break
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    final = photo_info(dest)
    shown = dest.relative_to(REPO) if REPO in dest.parents else dest.name
    print(f"Photo: {shown} ({final['w']}x{final['h']} px, {len(data) // 1024} KB, quality {quality}, no EXIF)")
    return len(data)


# ── Git ───────────────────────────────────────────────────────────────────────

def git(*args: str, capture: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(REPO), *args], capture_output=capture, text=True)
    if result.returncode != 0:
        fail(f"git {' '.join(args)} failed:\n{(result.stderr or '').strip()}")
    return (result.stdout or "").strip()


def ready_to_push() -> None:
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch != "main":
        fail(f"--push commits on main, but this repo is on {branch!r}. Switch with: git checkout main")
    busy = git("status", "--porcelain", "--", "shop", "images/shop")
    if busy:
        fail(f"shop/ or images/shop/ already has uncommitted changes; commit or undo them first:\n{busy}")
    print("Bringing main up to date before adding...")
    git("pull", "--ff-only", "origin", "main")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Add a product to the SMV shop feed (shop/products.json).")
    parser.add_argument("--title", required=True, help="product title as it should appear on the site and app")
    parser.add_argument("--price", required=True, help='price, e.g. "£19.99"')
    parser.add_argument("--url", required=True, help="the Etsy listing link")
    parser.add_argument("--photo", required=True, help="a real photo of the product (jpg, png or heic)")
    parser.add_argument("--id", help="short id and image name, e.g. tablet-transporter (made from the title if left out)")
    parser.add_argument("--date", help="the added date, YYYY-MM-DD (today if left out)")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen without writing anything")
    parser.add_argument("--push", action="store_true", help="commit on main and push so it goes live")
    args = parser.parse_args()

    title = " ".join(args.title.split())
    if not title:
        fail("the title is empty")
    price = clean_price(args.price)
    url = clean_url(args.url)
    product_id = slugify(args.id) if args.id else slugify(title)
    if not product_id:
        fail("could not make an id from the title; pass --id")
    added = check_date(args.date) if args.date else dt.date.today().isoformat()
    photo = Path(args.photo).expanduser()
    if not photo.is_file():
        fail(f"no photo at {photo}")

    if args.push and not args.dry_run:
        ready_to_push()

    feed = load_feed()
    refuse_duplicates(feed, product_id, url)

    image_path = IMAGE_DIR / f"{product_id}.jpg"
    entry = {
        "id": product_id,
        "title": title,
        "price": price,
        "url": url,
        "image": f"{SITE}/images/shop/{product_id}.jpg",
        "added": added,
    }

    photo = pick_photo(photo)
    if args.dry_run:
        with tempfile.TemporaryDirectory() as tmp:
            make_image(photo, Path(tmp) / image_path.name)
        print("\nDry run, nothing written. This entry would go at the top of shop/products.json:")
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return

    if image_path.exists():
        print(f"Replacing an old image file that no product was using: {image_path.relative_to(REPO)}")
    make_image(photo, image_path)

    feed["products"].insert(0, entry)
    feed["updated"] = dt.date.today().isoformat()
    write_feed({"updated": feed["updated"], "products": feed["products"]})
    print(f"Feed: added {product_id!r} at the top of shop/products.json ({len(feed['products'])} products)")

    files = ["shop/products.json", f"images/shop/{product_id}.jpg"]
    message = f"Shop: add {title}"
    if args.push:
        git("add", "--", *files)
        git("commit", "-m", message, "--", *files)
        print("Pushing to main...")
        git("push", "origin", "main", capture=False)
        print(f"\nPushed. Live in a minute or two at {SITE}/#shop and in the app via {SITE}/shop/products.json")
        return

    print("\nTo publish (site and app), run:")
    print(f"  cd {shlex.quote(str(REPO))}")
    print(f"  git add {' '.join(files)}")
    print(f"  git commit -m {shlex.quote(message)}")
    print("  git push origin main")
    print(f"\nOr next time add --push to do this for you. The app reads {SITE}/shop/products.json")


if __name__ == "__main__":
    main()

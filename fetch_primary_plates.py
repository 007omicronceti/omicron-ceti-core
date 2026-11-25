#!/usr/bin/env python3
"""
Fetch and verify primary NASA/JPL, ESA/Hubble, Chandra, and 1603 Uranometria plates
into content/assets/ with magic-byte validation and SHA-256 provenance logging.
"""
import hashlib
import os
import urllib.request
from datetime import datetime, timezone

ASSETS_DIR = os.path.join("content", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "OmicronCetiCoreArchive/1.0 (https://github.com/007omicronceti/omicron-ceti-core)"
}

PLATES = [
    {
        "filename": "pia09958-galex-mira-tail.jpg",
        "title": "NASA/JPL GALEX Far-UV Mosaic: Mira's 13-Light-Year Bow Shock & Tail (PIA09958)",
        "credit": "NASA/JPL-Caltech/C. Martin (Caltech)/M. Seibert (OCIW)",
        "archive_page": "https://science.nasa.gov/photojournal/mira-soars-through-the-sky/",
        "urls": [
            "https://photojournal.jpl.nasa.gov/jpeg/PIA09958.jpg",
            "https://photojournal.jpl.nasa.gov/jpegMod/PIA09958_modest.jpg",
        ],
    },
    {
        "filename": "opo9726a-hubble-mira-ab.jpg",
        "title": "NASA/ESA Hubble FOC Ultraviolet/Optical Image Separating Mira A & Mira B (opo9726a)",
        "credit": "NASA, ESA, and M. Karovska (Harvard-Smithsonian Center for Astrophysics)",
        "archive_page": "https://esahubble.org/images/opo9726a/",
        "urls": [
            "https://cdn.esahubble.org/archives/images/screen/opo9726a.jpg",
            "https://cdn.esahubble.org/archives/images/large/opo9726a.jpg",
            "https://esahubble.org/media/archives/images/screen/opo9726a.jpg",
        ],
    },
    {
        "filename": "chandra-2005-mira-xray.jpg",
        "title": "NASA Chandra X-Ray Observatory ACIS-S Image of Mira AB Outburst (CXC 05-06)",
        "credit": "NASA/CXC/SAO/M. Karovska et al.",
        "archive_page": "https://chandra.harvard.edu/photo/2005/mira/",
        "urls": [
            "https://chandra.harvard.edu/photo/2005/mira/mira.jpg",
            "https://chandra.harvard.edu/photo/2005/mira/mira_lg.jpg",
            "https://chandra.harvard.edu/photo/2005/mira/mira_xray.jpg",
        ],
    },
    {
        "filename": "bayer-1603-uranometria-cetus-fol34v.jpg",
        "title": "Johannes Bayer, Uranometria (Augsburg, 1603), fol. 34v: Cetus (Cataloging Omicron Ceti)",
        "credit": "Linda Hall Library of Science, Engineering & Technology / Wikimedia Commons (Public Domain)",
        "archive_page": "https://commons.wikimedia.org/wiki/File:Uranometria_%E2%80%94_fol._34_v,_Cetus_%E2%80%94_1603.jpg",
        "urls": [
            "https://commons.wikimedia.org/wiki/Special:FilePath/Uranometria_%E2%80%94_fol._34_v,_Cetus_%E2%80%94_1603.jpg?width=1600",
            "https://commons.wikimedia.org/wiki/Special:FilePath/Uranometria_%E2%80%94_fol._34_v,_Cetus_%E2%80%94_1603.jpg",
        ],
    },
]

def is_valid_image(data: bytes) -> bool:
    if len(data) < 2048:
        return False
    return data.startswith(b"\xff\xd8\xff") or data.startswith(b"\x89PNG")

def fetch_plate(plate: dict) -> tuple[str, str, int]:
    dest = os.path.join(ASSETS_DIR, plate["filename"])
    last_err = "unknown error"
    for url in plate["urls"]:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            if is_valid_image(data):
                with open(dest, "wb") as f:
                    f.write(data)
                sha256 = hashlib.sha256(data).hexdigest()
                return url, sha256, len(data)
            last_err = f"Non-image or truncated payload ({len(data)} bytes) from {url}"
        except Exception as exc:
            last_err = f"{url} -> {exc}"
    raise RuntimeError(f"Failed to download {plate['filename']}: {last_err}")

def main():
    records = []
    for plate in PLATES:
        print(f"Downloading {plate['filename']}...")
        src_url, sha256, size = fetch_plate(plate)
        print(f"  OK: {size:,} bytes | SHA-256: {sha256[:16]}...")
        records.append((plate, src_url, sha256, size))

    provenance_path = os.path.join(ASSETS_DIR, "PROVENANCE.md")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(provenance_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write('title: "Primary Visual Assets Provenance & SHA-256 Manifest"\n')
        f.write("tags: [assets, provenance, nasa, esa, chandra, bayer, primary-sources]\n")
        f.write("---\n\n")
        f.write("# Primary Visual Assets Provenance & SHA-256 Manifest\n\n")
        f.write(f"All visual plates mirrored into `content/assets/` were retrieved directly from official institutional repositories on **{now}** and verified by binary header and SHA-256 checksum.\n\n")
        for plate, src_url, sha256, size in records:
            f.write(f"## `{plate['filename']}`\n")
            f.write(f"* **Description:** {plate['title']}\n")
            f.write(f"* **Credit / Rights:** {plate['credit']}\n")
            f.write(f"* **Archival Record Page:** [{plate['archive_page']}]({plate['archive_page']})\n")
            f.write(f"* **Direct Mirror Source:** `{src_url}`\n")
            f.write(f"* **File Size:** {size:,} bytes\n")
            f.write(f"* **SHA-256:** `{sha256}`\n\n")
    print(f"Wrote {provenance_path}")

if __name__ == "__main__":
    main()

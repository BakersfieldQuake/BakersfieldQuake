"""extract_refs.py — Unpacks all 371 embedded reference images, captions, GPS metadata,
and text descriptions from g:/Downloads/nana-plaza-gallery-self-contained.html into
ref_images/ + manifest.json + high-resolution contact sheets for 100% visual review.
"""
import base64
import html as html_mod
import io
import json
import math
import os
import re
from PIL import Image, ImageDraw, ImageFont

HTML_PATH = r"G:\Downloads\nana-plaza-gallery-self-contained.html"
HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "ref_images")
SHEET_DIR = os.path.join(HERE, "contact_sheets")
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(SHEET_DIR, exist_ok=True)

with open(HTML_PATH, "r", encoding="utf-8") as f:
    raw = f.read()

# Parse sequentially through h2, h3, p, figure
token_re = re.compile(
    r"<(h2|h3|p|pre|div|ul|figure)\b[^>]*>(.*?)</\1>",
    re.DOTALL | re.IGNORECASE,
)
img_re = re.compile(
    r'<img\s+src="data:image/([a-zA-Z0-9.+-]+);base64,([^"]+)"(?:\s+alt="([^"]*)")?',
    re.DOTALL | re.IGNORECASE,
)
cap_re = re.compile(r"<figcaption>(.*?)</figcaption>", re.DOTALL | re.IGNORECASE)
tag_strip = re.compile(r"<[^>]+>")
pano_re = re.compile(r"Pano\s+(\S+)\s+[—-]\s+([^—-]+?)\s+[—-]\s+([0-9.]+),\s*([0-9.]+)")


def clean_text(s):
    return html_mod.unescape(tag_strip.sub("", s)).strip()


cur_h2 = "INTRO"
cur_h3 = ""
cur_p = ""
manifest = []
text_sections = []
idx = 0

for m in token_re.finditer(raw):
    tag = m.group(1).lower()
    body = m.group(2)
    if tag == "h2":
        cur_h2 = clean_text(body)
        cur_h3 = ""
        cur_p = ""
        text_sections.append({"tag": "h2", "text": cur_h2})
    elif tag == "h3":
        cur_h3 = clean_text(body)
        cur_p = ""
        text_sections.append({"tag": "h3", "h2": cur_h2, "text": cur_h3})
    elif tag in ("p", "pre", "div", "ul"):
        txt = clean_text(body)
        if tag == "p":
            cur_p = txt
        text_sections.append({"tag": tag, "h2": cur_h2, "h3": cur_h3, "text": txt})
    elif tag == "figure":
        im_m = img_re.search(body)
        if not im_m:
            continue
        idx += 1
        fmt_raw, b64, alt = im_m.group(1).lower(), im_m.group(2), html_mod.unescape(im_m.group(3) or "")
        cap_m = cap_re.search(body)
        cap = clean_text(cap_m.group(1)) if cap_m else alt
        raw_bytes = base64.b64decode(b64)
        im = Image.open(io.BytesIO(raw_bytes))
        w, h = im.size
        ext = "png" if "png" in fmt_raw else ("webp" if "webp" in fmt_raw else "jpg")
        # Save as PNG or high-quality JPG; let's save original bytes directly to preserve 100% quality!
        fname = f"ref_{idx:03d}.{ext}"
        fpath = os.path.join(IMG_DIR, fname)
        with open(fpath, "wb") as out:
            out.write(raw_bytes)

        lat, lon, pano_id, pano_date = None, None, None, None
        pm = pano_re.search(cur_p)
        if pm:
            pano_id = pm.group(1)
            pano_date = pm.group(2).strip()
            lat = float(pm.group(3).rstrip("."))
            lon = float(pm.group(4).rstrip("."))
        yaw = None
        ym = re.search(r"yaw\s+(\d+)", cap)
        if ym:
            yaw = int(ym.group(1))

        manifest.append({
            "id": idx,
            "file": fname,
            "width": w,
            "height": h,
            "bytes": len(raw_bytes),
            "h2": cur_h2,
            "h3": cur_h3,
            "context": cur_p,
            "caption": cap,
            "pano_id": pano_id,
            "pano_date": pano_date,
            "lat": lat,
            "lon": lon,
            "yaw": yaw,
        })

with open(os.path.join(HERE, "manifest.json"), "w", encoding="utf-8") as mf:
    json.dump({"images": manifest, "text_sections": text_sections}, mf, indent=2, ensure_ascii=False)

print(f"Extracted {len(manifest)} images and {len(text_sections)} text blocks.")

# Build contact sheets (16 images per sheet = 4x4 grid, 480x360 cell + caption bar -> 1920x1600)
try:
    fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 15)
    fnt_sm = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
except OSError:
    fnt = ImageFont.load_default()
    fnt_sm = fnt

PER_SHEET = 16
COLS, ROWS = 4, 4
CW, CH, CAP_H = 460, 320, 56
SW, SH = COLS * CW, ROWS * (CH + CAP_H)

num_sheets = math.ceil(len(manifest) / PER_SHEET)
for s_i in range(num_sheets):
    batch = manifest[s_i * PER_SHEET : (s_i + 1) * PER_SHEET]
    sheet = Image.new("RGB", (SW, SH), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    for j, item in enumerate(batch):
        col = j % COLS
        row = j // COLS
        x0 = col * CW
        y0 = row * (CH + CAP_H)
        im = Image.open(os.path.join(IMG_DIR, item["file"])).convert("RGB")
        im.thumbnail((CW - 8, CH - 8), Image.LANCZOS)
        ix = x0 + (CW - im.width) // 2
        iy = y0 + (CH - im.height) // 2
        sheet.paste(im, (ix, iy))
        d.rectangle([x0, y0, x0 + CW - 1, y0 + CH + CAP_H - 1], outline=(75, 75, 85), width=1)
        hdr = f"#{item['id']:03d} ({item['width']}x{item['height']}) [{item['h3'] or item['h2'][:22]}]"
        cap = item["caption"]
        if len(cap) > 62:
            cap = cap[:59] + "..."
        d.text((x0 + 6, y0 + CH + 4), hdr[:58], fill=(255, 220, 110), font=fnt)
        d.text((x0 + 6, y0 + CH + 24), cap, fill=(225, 225, 230), font=fnt_sm)
    sname = f"sheet_{s_i + 1:02d}_({batch[0]['id']:03d}-{batch[-1]['id']:03d}).jpg"
    sheet.save(os.path.join(SHEET_DIR, sname), quality=88)

print(f"Built {num_sheets} contact sheets in {SHEET_DIR}")

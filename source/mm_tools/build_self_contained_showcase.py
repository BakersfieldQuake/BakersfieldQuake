"""Builds the single-file self-contained HTML version of the streamlined Bakersfield Quake site:
  g:\\Quake\\Combat\\BakersfieldQuake\\fanpage\\bakersfield_geocities_showcase.html

Inlines all CSS, UI textures, 6 interactive 3D/sprite models, 3 GIFs, and 4 map screenshots
into one standalone HTML file with zero external local dependencies and zero fake content.
"""
import base64
import io
import os
import re
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FANPAGE = os.path.join(MOD_ROOT, "fanpage")
OUT_HTML = os.path.join(FANPAGE, "bakersfield_geocities_showcase.html")


def file_to_data_uri(path, max_w=None, webp_q=82):
    ext = os.path.splitext(path)[1].lower()
    if max_w and ext in (".png", ".jpg", ".jpeg"):
        im = Image.open(path)
        im.load()
        if im.width > max_w:
            h = max(1, round(im.height * (max_w / float(im.width))))
            im = im.resize((max_w, h), Image.Resampling.LANCZOS)
        bio = io.BytesIO()
        im.convert("RGB").save(bio, "WEBP", quality=webp_q, method=4)
        return "data:image/webp;base64," + base64.b64encode(bio.getvalue()).decode("ascii")

    raw = open(path, "rb").read()
    mime = {
        ".gif": "image/gif",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def main():
    index_html = open(os.path.join(FANPAGE, "index.html"), "r", encoding="utf-8").read()
    css = open(os.path.join(FANPAGE, "styles.css"), "r", encoding="utf-8").read()
    models_js = open(os.path.join(FANPAGE, "assets", "models_data.js"), "r", encoding="utf-8").read()
    viewer_js = open(os.path.join(FANPAGE, "viewer.js"), "r", encoding="utf-8").read()

    # Inline CSS background assets
    for rel in ("media/ui/bg_tile.png", "media/gifs/fire_divider.gif"):
        p = os.path.join(FANPAGE, rel.replace("/", os.sep))
        css = css.replace(rel, file_to_data_uri(p))

    # Inline all local src/href image references in index.html
    def repl_attr(m):
        attr, rel = m.group(1), m.group(2)
        if rel.startswith(("http://", "https://", "data:", "#")) or rel.endswith((".css", ".js")):
            return m.group(0)
        p = os.path.join(FANPAGE, rel.replace("/", os.sep))
        max_w = 800 if rel.startswith("media/shots/") else None
        return f'{attr}="{file_to_data_uri(p, max_w=max_w)}"'

    html = re.sub(r'(src|href)="([^"]+)"', repl_attr, index_html)
    html = html.replace('<link rel="stylesheet" href="styles.css">', f"<style>\n{css}\n</style>")
    html = html.replace('<script src="assets/models_data.js"></script>', f"<script>\n{models_js}\n</script>")
    html = html.replace('<script src="viewer.js"></script>', f"<script>\n{viewer_js}\n</script>")

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    ext_refs = [
        r for r in re.findall(r'(?:src|href)="([^"]+)"', html)
        if r and not r.startswith(("data:", "https://", "http://", "#"))
    ]
    assert not ext_refs, f"External refs leaked into self-contained HTML: {ext_refs}"

    non_b64 = re.sub(r"data:[^\"']+base64,[A-Za-z0-9+/=]+", "DATA_URI", html)
    non_b64 = re.sub(r'"binGz":"[A-Za-z0-9+/=]+"', '"binGz":"GZ"', non_b64)
    forbidden = ["TimesSquare", "Guestbook", "WebRing", "006610", "PaintShop", "Camper661", "WheelmanVictim", "LOL.BAT"]
    leaked = [pat for pat in forbidden if pat in non_b64]
    assert not leaked, f"Forbidden fake text leaked into self-contained HTML: {leaked}"

    print(f"[SELF-CONTAINED OK] Wrote {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB) | External refs: {ext_refs} | Leaked: {leaked}")


if __name__ == "__main__":
    main()

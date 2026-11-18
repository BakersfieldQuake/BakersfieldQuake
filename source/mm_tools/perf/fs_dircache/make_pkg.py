"""Build a scratch BAKOQUAKE package for release-layout load tests.
File list = the release zip. pk3/pak/bsp/lit (never written by the engine) are hard-linked from the install;
everything else is a real copy, so config.cfg written on quit cannot reach the install."""
import os, shutil, sys, zipfile
ZIP = r"G:\Quake\Combat\dist\BAKOQUAKE_v1.11.zip"
INST = r"G:\Quake\Combat"
OUT = sys.argv[1]
LINK = (".pk3", ".pak", ".bsp", ".lit")
FROM_INSTALL = {"BakersfieldQuake/default.cfg", "BakersfieldQuake/quake.rc", "BakersfieldQuake/server.cfg"}  # today's audit changes
if os.path.exists(OUT):
    sys.exit("exists: " + OUT)
z = zipfile.ZipFile(ZIP)
nl = nc = 0
for i in z.infolist():
    if i.is_dir():
        continue
    rel = i.filename.split("/", 1)[1]
    if rel.startswith("engine/"):
        continue
    dst = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    src = os.path.join(INST, rel)
    if rel.lower().endswith(LINK) and os.path.exists(src) and os.path.getsize(src) == i.file_size:
        os.link(src, dst); nl += 1
    elif rel in FROM_INSTALL:
        shutil.copyfile(src, dst); nc += 1
    else:
        with z.open(i) as f, open(dst, "wb") as g:
            shutil.copyfileobj(f, g)
        nc += 1
for p in ("pak0.pak", "pak1.pak"):
    os.link(os.path.join(INST, "id1", p), os.path.join(OUT, "id1", p)); nl += 1
print("linked %d, copied %d" % (nl, nc))

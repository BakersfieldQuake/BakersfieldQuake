import os, shutil, subprocess, sys
ROOT = r"G:\Quake\Combat"
SRC = os.path.join(ROOT, "qc_src", "quakec")
TST = os.path.join(ROOT, "mm_tools", "qc_vmtest_vanilla")
FTEQCC = r"D:\vibe\quake1opensource\engines\win64\fteqcc64.exe"
def rd(p): return open(p, encoding="utf-8", errors="surrogateescape", newline="").read().replace("\r\n", "\n")
def wr(p, s): open(p, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s)
if os.path.exists(TST): shutil.rmtree(TST)
os.makedirs(TST)
shutil.copytree(SRC, os.path.join(TST, "quakec"))
q = os.path.join(TST, "quakec")
shutil.copy(os.path.join(ROOT, "mm_tools", "zz_vmtest.qc"), os.path.join(q, "zz_vmtest.qc"))
w = rd(os.path.join(q, "weapons.qc"))
w = "void() VMTest_Start;\n" + w
w = w.replace("void() W_Precache =\n{\n", "void() W_Precache =\n{\n\tVMTest_Start();\n", 1)
wr(os.path.join(q, "weapons.qc"), w)
src = rd(os.path.join(q, "progs.src"))
wr(os.path.join(q, "progs.src"), src.rstrip("\n") + "\nzz_vmtest.qc\n")
out = os.path.join(TST, "progs.dat")
p = subprocess.run([FTEQCC, "-srcfile", "progs.src"], cwd=q, capture_output=True, text=True, errors="replace")
for l in (p.stdout + p.stderr).splitlines():
    if ": error" in l or "Compile finished" in l or "Error in" in l: print(l)
if not os.path.exists(out): print("COMPILE FAILED"); sys.exit(1)
dest = os.path.join(ROOT, "BakersfieldMemesTest"); os.makedirs(dest, exist_ok=True)
shutil.copy(out, os.path.join(dest, "progs.dat")); print("installed")

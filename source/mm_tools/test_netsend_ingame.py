"""Isolated DarkPlaces in-game verification harness for the "WHERE'S THE DISK?" 3D models & shaders.

Follows CLAUDE.md strictly:
  - Compiles a temporary stacked test mod `G:\\Quake\\Combat\\BakersfieldQuakeNetsendTest\\progs.dat`
    (NEVER modifies `BakersfieldQuake\\progs.dat` or existing QC files).
  - Checks `darkplaces` processes before launching.
  - Launches directly on the right monitor (`-window -width 1280 -height 720`) on `+map start` (NEVER `dm6`),
    logs via `-condebug +log_file zz_netsend.log`, captures 13 verification screenshots, and exits via `quit`.
  - Copies screenshots & log into `source/mm_tools/out/netsend_renders/ingame/` and removes the temporary test dir.
"""
import glob
import os
import shutil
import subprocess
import sys
import time

COMBAT_ROOT = r"G:\Quake\Combat"
MOD_DIR = os.path.join(COMBAT_ROOT, "BakersfieldQuake")
QC_SRC = os.path.join(MOD_DIR, "source", "qc_combat_decomp")
HERE = os.path.dirname(os.path.abspath(__file__))
TMP_QC = os.path.join(HERE, "out", "qc_netsend_test")
TEST_GAME_DIR = os.path.join(COMBAT_ROOT, "BakersfieldQuakeNetsendTest")
OUT_INGAME = os.path.join(HERE, "out", "netsend_renders", "ingame")
FTEQCC = r"D:\vibe\quake1opensource\engines\win64\fteqcc64.exe"
DP_EXE = os.path.join(COMBAT_ROOT, "darkplaces.exe")


ZZ_NETSEND_QC = r"""
// TEMPORARY ISOLATED MODEL-VERIFICATION HARNESS (BakersfieldQuakeNetsendTest ONLY)

entity ns_pc;
entity ns_arc;
entity ns_dsk;
float  ns_vm_active;
float  ns_vm_frame;
float  ns_vm_hide;
float  ns_fx_zap;
float  ns_fx_pop;
vector ns_lock_ang;
float  ns_lock_on;

.float ns_t0;
.float ns_step;
.float ns_yaw;
.vector ns_anchor;
.vector ns_fwd;

void() NSTest_Think;

void(entity vm) NSTest_VModelThink =
{
	if (!ns_vm_active)
		return;
	if (ns_vm_hide)
	{
		vm.alpha = -1;
		return;
	}
	setmodel(vm, "progs/v_netsend.md3");
	vm.origin = '0 0 0';
	vm.angles = '0 0 0';
	vm.frame = ns_vm_frame;
	vm.skin = 0;
	vm.alpha = 1;
};

void() NSTest_Precache =
{
	local entity ctl;

	precache_model("progs/v_netsend.md3");
	precache_model("progs/netsend_pc.md3");
	precache_model("progs/netsend_arc.md3");
	precache_model("progs/netsend_disk.md3");
	precache_model("progs/netsend_arc.spr");

	ns_fx_zap = particleeffectnum("netsend_zap");
	ns_fx_pop = particleeffectnum("netsend_pop");
	dprint("NSTest_Precache OK: zap=", ftos(ns_fx_zap), " pop=", ftos(ns_fx_pop), "\n");

	ctl = spawn();
	ctl.classname = "ns_test_ctl";
	ctl.think = NSTest_Think;
	ctl.nextthink = time + 0.2;
};

float() NSTest_WeaponFrame =
{
	if (!ns_vm_active)
		return FALSE;
	self.impulse = 0;
	if (ns_lock_on)
	{
		self.angles = ns_lock_ang;
		self.v_angle = ns_lock_ang;
		self.fixangle = TRUE;
		self.velocity = '0 0 0';
	}
	if (ns_vm_hide)
	{
		self.weaponmodel = "";
		self.weaponframe = 0;
	}
	else
	{
		self.weaponmodel = "progs/v_netsend.md3";
		self.weaponframe = ns_vm_frame;
	}
	return TRUE;
};

void(entity p, string nm) NS_Shot =
{
	dprint("NS_Shot: ", nm, "\n");
	stuffcmd(p, strcat("screenshot ", strcat(nm, "\n")));
};

vector(vector org, vector dir, float dist, entity ign) NS_FloorAt =
{
	local vector p_try;
	traceline(org, org + dir * (dist + 16), TRUE, ign);
	p_try = org + dir * dist;
	if (trace_fraction < 1.0)
		p_try = trace_endpos - dir * 18;
	traceline(p_try + '0 0 36', p_try - '0 0 160', TRUE, ign);
	return trace_endpos;
};

void(entity ctl, entity p) NS_InitHallway =
{
	local float best_score, score, cand_y, i, open_d, dz1, dz2;
	local vector v_ang, f1, f2;

	best_score = -9999;
	ctl.ns_yaw = p.angles_y;
	i = 0;
	while (i < 8)
	{
		// Prefer cardinal angles (90, 0, 180, 270) first on ties
		cand_y = i * 45;
		v_ang_x = 0; v_ang_y = cand_y; v_ang_z = 0;
		makevectors(v_ang);
		traceline(p.origin + '0 0 16', p.origin + '0 0 16' + v_forward * 260, TRUE, p);
		open_d = trace_fraction * 260;
		f1 = NS_FloorAt(p.origin, v_forward, 48.35, p);
		f2 = NS_FloorAt(p.origin, v_forward, 82.0, p);
		dz1 = fabs(f1_z - (p.origin_z - 24));
		dz2 = fabs(f2_z - (p.origin_z - 24));
		score = open_d - (dz1 + dz2) * 8;
		if (cand_y == 90 || cand_y == 0 || cand_y == 180 || cand_y == 270)
			score = score + 10;
		if (open_d > 110 && score > best_score)
		{
			best_score = score;
			ctl.ns_yaw = cand_y;
			ctl.ns_fwd = v_forward;
		}
		i = i + 1;
	}
	ctl.ns_anchor = p.origin;
	dprint("NS_InitHallway: anchor=", vtos(ctl.ns_anchor), " yaw=", ftos(ctl.ns_yaw), " score=", ftos(best_score), "\n");

	ns_dsk = spawn();
	ns_dsk.movetype = MOVETYPE_NONE;
	ns_dsk.solid = SOLID_NOT;
	setmodel(ns_dsk, "progs/netsend_disk.md3");
	ns_dsk.effects = ns_dsk.effects | EF_NODRAW;

	ns_pc = spawn();
	ns_pc.movetype = MOVETYPE_NONE;
	ns_pc.solid = SOLID_NOT;
	setmodel(ns_pc, "progs/netsend_pc.md3");
	ns_pc.effects = ns_pc.effects | EF_NODRAW;

	ns_arc = spawn();
	ns_arc.movetype = MOVETYPE_NONE;
	ns_arc.solid = SOLID_NOT;
	setmodel(ns_arc, "progs/netsend_arc.md3");
	ns_arc.effects = ns_arc.effects | EF_NODRAW;
};

void(entity p, float pitch_deg, float yaw_deg) NS_AimPlayer =
{
	ns_lock_ang_x = pitch_deg;
	ns_lock_ang_y = yaw_deg;
	ns_lock_ang_z = 0;
	ns_lock_on = TRUE;
	p.angles = ns_lock_ang;
	p.v_angle = ns_lock_ang;
	p.fixangle = TRUE;
	p.velocity = '0 0 0';
};

void() NSTest_Think =
{
	local entity p;
	local float t, anim16, anim4;
	local vector fpos;

	self.nextthink = time + 0.04;
	p = find(world, classname, "player");
	if (!p)
		return;

	if (!self.ns_t0)
	{
		self.ns_t0 = time;
		ns_vm_active = TRUE;
		ns_vm_hide = FALSE;
		ns_vm_frame = 0;
		NS_InitHallway(self, p);
		NS_AimPlayer(p, 0, self.ns_yaw);
		stuffcmd(p, "crosshair 1; cl_bob 0; cl_rollangle 0; r_drawviewmodel 1; viewsize 100; scr_centertime 0; v_kickpitch 0; v_kickroll 0\n");
		return;
	}

	t = time - self.ns_t0;
	setorigin(p, self.ns_anchor);
	p.angles = ns_lock_ang;
	p.v_angle = ns_lock_ang;
	p.fixangle = TRUE;
	p.velocity = '0 0 0';

	// Continuously animate electric arcs & ~7Hz spark bursts when ns_arc is visible
	if (!(ns_arc.effects & EF_NODRAW))
	{
		ns_arc.frame = floor(time * 20) - floor(floor(time * 20) / 8) * 8;
		if (ns_fx_zap >= 0 && (floor(t * 25) - floor(floor(t * 25) / 4) * 4) == 0)
			pointparticles(ns_fx_zap, ns_pc.origin + '0 0 54', '0 0 8', 1);
	}

	// Step 0 -> 1 (t = 1.0s): Viewmodel Frame 0 Idle Hold (LOL.BAT legible, crosshair clear)
	if (t >= 1.0 && self.ns_step == 0)
	{
		ns_vm_hide = FALSE;
		ns_vm_frame = 0;
		NS_AimPlayer(p, 0, self.ns_yaw);
		self.ns_step = 1;
	}
	if (t >= 1.25 && self.ns_step == 1) { NS_Shot(p, "ns_ig_01_vm_idle.png"); self.ns_step = 2; }

	// Step 2 -> 3 (t = 1.5s): Viewmodel Frame 15 Flipped 180 deg (Back Metal Shutter & Hub)
	if (t >= 1.50 && self.ns_step == 2) { ns_vm_frame = 15; self.ns_step = 3; }
	if (t >= 1.70 && self.ns_step == 3) { NS_Shot(p, "ns_ig_02_vm_flip.png"); self.ns_step = 4; }

	// Step 4 -> 5 (t = 1.95s): Viewmodel Frame 42 Wind-Up
	if (t >= 1.95 && self.ns_step == 4) { ns_vm_frame = 42; self.ns_step = 5; }
	if (t >= 2.15 && self.ns_step == 5) { NS_Shot(p, "ns_ig_03_vm_windup.png"); self.ns_step = 6; }

	// Step 6 -> 7 (t = 2.40s): Viewmodel Frame 44 Release (Empty Hand!) + netsend_disk.md3 stuck in floor!
	if (t >= 2.40 && self.ns_step == 6)
	{
		ns_vm_frame = 44;
		fpos = NS_FloorAt(self.ns_anchor, self.ns_fwd, 56, p);
		setorigin(ns_dsk, fpos);
		ns_dsk.angles_y = self.ns_yaw + 180;
		ns_dsk.frame = 1;
		ns_dsk.effects = ns_dsk.effects - (ns_dsk.effects & EF_NODRAW);
		NS_AimPlayer(p, 22, self.ns_yaw);
		self.ns_step = 7;
	}
	if (t >= 2.60 && self.ns_step == 7) { NS_Shot(p, "ns_ig_04_vm_throw_disk.png"); self.ns_step = 8; }

	// Step 8 -> 9 (t = 2.85s): Deployable PC Materialize Overshoot (Frame 5, Skin 1 off) + Viewmodel Frame 57 reload!
	if (t >= 2.85 && self.ns_step == 8)
	{
		ns_dsk.effects = ns_dsk.effects | EF_NODRAW;
		ns_vm_frame = 57;
		fpos = NS_FloorAt(self.ns_anchor, self.ns_fwd, 82, p);
		setorigin(ns_pc, fpos);
		ns_pc.angles_y = self.ns_yaw + 180;
		ns_pc.frame = 5;
		ns_pc.skin = 1;
		ns_pc.effects = ns_pc.effects - (ns_pc.effects & EF_NODRAW);
		if (ns_fx_pop >= 0)
			pointparticles(ns_fx_pop, fpos + '0 0 8', '0 0 24', 1);
		NS_AimPlayer(p, 6, self.ns_yaw);
		self.ns_step = 9;
	}
	if (t >= 3.05 && self.ns_step == 9) { NS_Shot(p, "ns_ig_05_pc_materialize.png"); self.ns_step = 10; }

	// Step 10 -> 17: 40-UNIT CLOSE-UP CRT SCREEN SEQUENCE!
	// PC origin at 48.35 units -> CRT glass (+8.35 front) is EXACTLY 40.0 Quake units from player's eyes!
	if (t >= 3.30 && self.ns_step == 10)
	{
		fpos = NS_FloorAt(self.ns_anchor, self.ns_fwd, 48.35, p);
		setorigin(ns_pc, fpos);
		setorigin(ns_arc, fpos);
		ns_pc.angles_y = self.ns_yaw + 180;
		ns_arc.angles_y = self.ns_yaw + 180;
		ns_pc.frame = 13;
		ns_pc.skin = 3; // INITIALIZING BATCH FILE...
		ns_vm_frame = 0;
		NS_AimPlayer(p, 3, self.ns_yaw);
		self.ns_step = 11;
	}
	if (t >= 3.50 && self.ns_step == 11) { NS_Shot(p, "ns_ig_06_scr40u_init.png"); self.ns_step = 12; }

	if (t >= 3.75 && self.ns_step == 12) { ns_pc.frame = 15; ns_pc.skin = 4; self.ns_step = 13; } // C:\> LOL.BAT
	if (t >= 3.95 && self.ns_step == 13) { NS_Shot(p, "ns_ig_07_scr40u_lolbat.png"); self.ns_step = 14; }

	if (t >= 4.20 && self.ns_step == 14) { ns_pc.frame = 18; ns_pc.skin = 5; self.ns_step = 15; } // NET SEND * LOL
	if (t >= 4.40 && self.ns_step == 15) { NS_Shot(p, "ns_ig_08_scr40u_netsend.png"); self.ns_step = 16; }

	// Active Live-Typing Hacking Screen ("NET SEND * WHERE'S THE DISK?") at 40 units + Electric Arcs + Viewmodel!
	if (t >= 4.65 && self.ns_step == 16)
	{
		ns_pc.frame = 24;
		ns_pc.skin = 0; // Active 16-frame live-typing loop (animmap 8 -> 2.0s cycle, frames 13..15 show full prompt)!
		ns_arc.effects = ns_arc.effects - (ns_arc.effects & EF_NODRAW);
		self.ns_step = 17;
	}
	anim16 = (time * 6) - floor((time * 6) / 16) * 16;
	if (t >= 4.85 && self.ns_step == 17 && ((anim16 >= 10.0 && anim16 <= 11.9) || t >= 7.60))
	{
		NS_Shot(p, "ns_ig_09_scr40u_wheresthedisk.png");
		self.ns_t0 = time - 5.40; // normalize remaining timeline after animmap sync
		self.ns_step = 18;
		return;
	}

	// Step 18 -> 23: Full Standing Deployable PC + Arcs + Base-Origin Yaw Spin Check (0, 90, 180 deg) at 82 units!
	if (t >= 5.65 && self.ns_step == 18)
	{
		ns_vm_hide = TRUE;
		fpos = NS_FloorAt(self.ns_anchor, self.ns_fwd, 82, p);
		setorigin(ns_pc, fpos);
		setorigin(ns_arc, fpos);
		ns_pc.angles_y = self.ns_yaw + 180;
		ns_arc.angles_y = self.ns_yaw + 180;
		ns_pc.frame = 26;
		ns_pc.skin = 0;
		NS_AimPlayer(p, 10, self.ns_yaw);
		self.ns_step = 19;
	}
	if (t >= 5.90 && self.ns_step == 19) { NS_Shot(p, "ns_ig_10_spin_front.png"); self.ns_step = 20; }

	if (t >= 6.15 && self.ns_step == 20)
	{
		ns_pc.angles_y = self.ns_yaw + 270; // 90 deg side profile
		ns_arc.angles_y = self.ns_yaw + 270;
		ns_pc.frame = 31;
		self.ns_step = 21;
	}
	if (t >= 6.35 && self.ns_step == 21) { NS_Shot(p, "ns_ig_11_spin_side90.png"); self.ns_step = 22; }

	if (t >= 6.60 && self.ns_step == 22)
	{
		ns_pc.angles_y = self.ns_yaw; // 180 deg rear profile
		ns_arc.angles_y = self.ns_yaw;
		ns_pc.frame = 36;
		self.ns_step = 23;
	}
	if (t >= 6.80 && self.ns_step == 23) { NS_Shot(p, "ns_ig_12_spin_rear180.png"); self.ns_step = 24; }

	// Step 24 -> 26: Shutdown Slump & CRT White Collapse Dot (Frame 49, Skin 6)
	if (t >= 7.05 && self.ns_step == 24)
	{
		ns_arc.effects = ns_arc.effects | EF_NODRAW;
		ns_pc.angles_y = self.ns_yaw + 180;
		ns_pc.frame = 49;
		ns_pc.skin = 6;
		self.ns_step = 25;
	}
	anim4 = (time * 4) - floor((time * 4) / 4) * 4;
	if (t >= 7.25 && self.ns_step == 25 && (anim4 < 1.8 || t >= 8.25))
	{
		NS_Shot(p, "ns_ig_13_shutdown.png");
		self.ns_t0 = time - 7.30;
		self.ns_step = 26;
		return;
	}

	if (t >= 7.70 && self.ns_step == 26)
	{
		dprint("NSTest_Think ALL SCREENSHOTS COMPLETE - QUITTING CLEANLY\n");
		stuffcmd(p, "quit\n");
		self.ns_step = 27;
	}
};
"""


def rd(p):
    return open(p, encoding="utf-8", errors="surrogateescape", newline="").read().replace("\r\n", "\n")


def wr(p, s):
    open(p, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s)


def build_temp_test_mod():
    if os.path.exists(TMP_QC):
        shutil.rmtree(TMP_QC)
    shutil.copytree(QC_SRC, TMP_QC)
    wr(os.path.join(TMP_QC, "zz_netsend_test.qc"), ZZ_NETSEND_QC)

    w_path = os.path.join(TMP_QC, "weapons.qc")
    w = rd(w_path)
    w = "void() NSTest_Precache;\nfloat() NSTest_WeaponFrame;\n" + w
    assert "void() W_Precache =\n{\n" in w, "Could not find W_Precache in weapons.qc"
    assert "void() W_WeaponFrame =\n{\n" in w, "Could not find W_WeaponFrame in weapons.qc"
    w = w.replace("void() W_Precache =\n{\n", "void() W_Precache =\n{\n\tNSTest_Precache();\n", 1)
    w = w.replace("void() W_WeaponFrame =\n{\n", "void() W_WeaponFrame =\n{\n\tif (NSTest_WeaponFrame()) return;\n", 1)
    wr(w_path, w)

    ce_path = os.path.join(TMP_QC, "custom_effects.qc")
    ce = rd(ce_path)
    ce = "void(entity vm) NSTest_VModelThink;\n" + ce
    ce_needle = "\tself.nextthink = time;\n\tself.owner.gunof = self.origin;"
    assert ce_needle in ce, "Could not find v_weapon_position_think tail in custom_effects.qc"
    ce = ce.replace(ce_needle, "\tNSTest_VModelThink(self);\n" + ce_needle, 1)
    wr(ce_path, ce)

    ps_path = os.path.join(TMP_QC, "progs.src")
    wr(ps_path, rd(ps_path).rstrip("\n") + "\nzz_netsend_test.qc\n")

    res = subprocess.run([FTEQCC, "-srcfile", "progs.src"], cwd=TMP_QC, capture_output=True, text=True, errors="replace")
    out_dat = os.path.join(TMP_QC, "progs.dat")
    if res.returncode != 0 or not os.path.exists(out_dat):
        print(res.stdout)
        print(res.stderr)
        sys.exit("fteqcc64 compile failed!")

    os.makedirs(TEST_GAME_DIR, exist_ok=True)
    shutil.copy2(out_dat, os.path.join(TEST_GAME_DIR, "progs.dat"))
    print(f"  [OK] Compiled isolated test progs.dat -> {TEST_GAME_DIR}")


def run_darkplaces_start_map():
    # Per CLAUDE.md: check running darkplaces processes first!
    chk = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Process darkplaces* -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
        capture_output=True, text=True,
    )
    running_pids = [ln.strip() for ln in chk.stdout.splitlines() if ln.strip()]
    if running_pids:
        sys.exit(f"ABORT: Another darkplaces process is currently running (PIDs: {running_pids}). Waiting per CLAUDE.md.")

    os.makedirs(OUT_INGAME, exist_ok=True)
    for old_png in glob.glob(os.path.join(OUT_INGAME, "ns_ig_*.png")):
        os.remove(old_png)

    cmd = [
        DP_EXE,
        "-nomouse",
        "-window", "-width", "1280", "-height", "720",
        "-game", "quake15",
        "-game", "BakersfieldQuake",
        "-game", "BakersfieldQuakeNetsendTest",
        "-condebug",
        "+log_file", "zz_netsend.log",
        "+maxplayers", "1",
        "+deathmatch", "0",
        "+map", "start",
    ]
    print("  [RUN] Launching DarkPlaces on +map start (unattended ~10s)...")
    proc = subprocess.Popen(cmd, cwd=COMBAT_ROOT)
    try:
        proc.wait(timeout=32)
        print(f"  [OK] DarkPlaces exited cleanly (code {proc.returncode}, PID {proc.pid}).")
    except subprocess.TimeoutExpired:
        print(f"  [WARN] DarkPlaces timed out after 32s; terminating ONLY our PID {proc.pid}")
        proc.terminate()
        proc.wait(timeout=5)

    # Collect screenshots & zz_netsend.log from TEST_GAME_DIR (and check screenshots/ subfolder if DP uses it)
    for pat in (
        os.path.join(TEST_GAME_DIR, "ns_ig_*.png"),
        os.path.join(TEST_GAME_DIR, "screenshots", "ns_ig_*.png"),
        os.path.join(TEST_GAME_DIR, "*.tga"),
        os.path.join(TEST_GAME_DIR, "zz_netsend.log"),
        os.path.join(TEST_GAME_DIR, "qconsole.log"),
    ):
        for fp in glob.glob(pat):
            shutil.copy2(fp, os.path.join(OUT_INGAME, os.path.basename(fp)))
            print(f"  [CAPTURED] {os.path.basename(fp)}")


def cleanup_temp():
    if os.path.exists(TEST_GAME_DIR):
        shutil.rmtree(TEST_GAME_DIR, ignore_errors=True)
    if os.path.exists(TMP_QC):
        shutil.rmtree(TMP_QC, ignore_errors=True)
    print("  [CLEAN] Removed temporary BakersfieldQuakeNetsendTest & scratch QC.")


if __name__ == "__main__":
    try:
        build_temp_test_mod()
        run_darkplaces_start_map()
    finally:
        cleanup_temp()

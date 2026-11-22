/*
================
robhead_xray.qc — Kali / Red Hat Linux Hacker Terminal + X-Ray Scanner HUD for Rob Head Drone
Called from CSQC_UpdateView when BMST_FD_MODE (stat 81) > 0.
Receives live map-wide enemy targets from SSQC via ENT_RD_TARGET (SendEntity).
================
*/

float	ENT_RD_TARGET		= 7;
float	BMST_FD_MODE		= 81;		// 0=off, 1=cruise, 2=dash, 3=post-blast fade
float	BMST_FD_TIMER		= 82;		// tenths of a second remaining (999=unlimited)
float	BMST_FD_SPEED		= 83;		// drone velocity u/s
float	BMST_FD_ARM			= 84;		// 1=dash armed, 0=arming
float	BMST_FD_SEQ			= 85;		// 1..14 randomized terminal sequence per launch

.entity	rh_next;
.entity	rh_sil;
.float	rh_hp;
.float	rh_flags;						// bit 1 = monster, bit 2 = ally
.float	rh_frame;
.float	rh_skin;
.float	rh_yaw;
.float	rh_scale;
.float	rh_last_t;
.string	rh_mdlname;
.vector	colormod;

entity	rh_xray_head;
float	rh_prev_mode;
float	rh_launch_t;
float	rh_active_seq;
float	rh_term_font;
float	rh_font_checked;

float	RH_DEG2RAD			= 0.01745329;
float	RH_RAD2DEG			= 57.2957795;

float(float x) RH_Sin =
{
	local float r;
	r = sin (x);
	return r;
};

float(float x) RH_Cos =
{
	local float r;
	r = cos (x);
	return r;
};

// Zircon drawline only renders segments where p1_y <= p0_y; normalize endpoint order here.
void(float wline, vector p0, vector p1, vector col, float a) RH_Line =
{
	if (p1_y > p0_y)
		drawline (wline, p1, p0, col, a, 0);
	else
		drawline (wline, p0, p1, col, a, 0);
};

// Angle wrap to [-180, 180]
float(float ang) RH_Wrap180 =
{
	return ang - 360 * rint (ang / 360);
};

// Approximate atan2(y, x) in degrees [-180, 180] using vectoangles
float(float dy, float dx) RH_Atan2Deg =
{
	local vector v, ang;

	v_x = dx;
	v_y = dy;
	v_z = 0;
	ang = vectoangles (v);
	return RH_Wrap180 (ang_y);
};

void(float isnew) RH_XRay_EntUpdate =
{
	local float flags;
	local vector org;
	local string mdl, nm;

	self.drawmask = 0;
	flags = ReadByte ();
	if (flags & 1)
	{
		org_x = ReadCoord ();
		org_y = ReadCoord ();
		org_z = ReadCoord ();
		self.origin = org;
		self.rh_hp = ReadCoord ();
		self.rh_flags = ReadCoord ();
		self.rh_frame = ReadCoord ();
		self.rh_skin = ReadCoord ();
		self.rh_yaw = ReadCoord ();
		self.rh_scale = ReadCoord ();
		mdl = ReadString ();
		if (self.rh_mdlname != "")
			strunzone (self.rh_mdlname);
		self.rh_mdlname = strzone (mdl);
		nm = ReadString ();
		if (self.netname != "")
			strunzone (self.netname);
		self.netname = strzone (nm);
		self.rh_last_t = time;
	}
	if (isnew)
	{
		self.rh_next = rh_xray_head;
		rh_xray_head = self;
	}
};

void() RH_XRay_EntRemove =
{
	local entity cur, prev;

	prev = world;
	cur = rh_xray_head;
	while (cur)
	{
		if (cur == self)
		{
			if (prev)
				prev.rh_next = cur.rh_next;
			else
				rh_xray_head = cur.rh_next;
			break;
		}
		prev = cur;
		cur = cur.rh_next;
	}
	if (self.rh_sil)
	{
		if (self.rh_sil.rh_mdlname != "")
		{
			strunzone (self.rh_sil.rh_mdlname);
			self.rh_sil.rh_mdlname = "";
		}
		remove (self.rh_sil);
		self.rh_sil = world;
	}
	if (self.rh_mdlname != "")
	{
		strunzone (self.rh_mdlname);
		self.rh_mdlname = "";
	}
	if (self.netname != "")
	{
		strunzone (self.netname);
		self.netname = "";
	}
	remove (self);
};

void() RH_AddXRayEntities =
{
	local entity t, s;
	local vector cam_org, cam_ang, delta;
	local float dist, a, sweep_deg, bear_deg, diff, ping;

	cam_org = getpropertyvec (VF_ORIGIN);
	cam_ang = getpropertyvec (VF_ANGLES);
	makevectors (cam_ang);
	sweep_deg = RH_Wrap180 (time * 165);

	t = rh_xray_head;
	while (t)
	{
		if (time - t.rh_last_t <= 0.6 && !(t.rh_flags & 2) && t.rh_mdlname != "")
		{
			dist = vlen (t.origin - cam_org);
			if (dist <= 3600)
			{
				// Skip targets already in direct line-of-sight so we don't double-render a glow over visible enemies
				traceline (cam_org, t.origin + '0 0 24', TRUE, world);
				if (trace_fraction < 0.995)
				{
					delta = t.origin - cam_org;
					delta_z = 0;
					bear_deg = RH_Atan2Deg (delta * v_right, delta * v_forward);
					diff = fabs (RH_Wrap180 (sweep_deg - bear_deg));
					ping = max (0, 1 - diff / 42);

					a = (0.38 + 0.24 * ping) * (1 - bound (0, (dist - 1800) / 1800, 0.72));
					if (a > 0.03)
					{
						if (!t.rh_sil)
							t.rh_sil = spawn ();
						s = t.rh_sil;
						if (s.rh_mdlname != t.rh_mdlname)
						{
							if (s.rh_mdlname != "")
								strunzone (s.rh_mdlname);
							precache_model (t.rh_mdlname);
							setmodel (s, t.rh_mdlname);
							s.rh_mdlname = strzone (t.rh_mdlname);
						}
						s.frame = t.rh_frame;
						s.skin = t.rh_skin;
						s.angles = t.rh_yaw * '0 1 0';
						if (t.rh_scale > 0)
							s.scale = t.rh_scale;
						else
							s.scale = 1;
						setorigin (s, t.origin);
						s.effects = 8192 | 512 | 32;		// EF_NODEPTHTEST | EF_FULLBRIGHT | EF_ADDITIVE
						if (dist < 460)
							s.colormod = '1.80 0.28 0.28' * (0.75 + 0.35 * ping);
						else
							s.colormod = '0.10 1.45 1.85' * (0.75 + 0.40 * ping);
						s.alpha = a;
						addentity (s);
					}
				}
			}
		}
		t = t.rh_next;
	}
};

float() JBH_TopLeftY;		// john_bird_hud.qc: top-left start that clears the con_notify lines

// drop-shadowed plain text in an exact colour (crisp shadow for high legibility over transparent panels)
void(vector pos, string s, vector sc, vector rgb, float a, float fl) RH_ShadowStr =
{
	drawstring (pos + '0.8 0.8 0', s, sc, '0 0 0', 0.95 * a, fl);
	drawstring (pos, s, sc, rgb, a, fl);
};

// ...right-aligned so it ends at rx
void(float rx, float y, string s, vector sc, vector rgb, float a) RH_ShadowStrRight =
{
	local float wd;

	wd = stringwidth (s, FALSE, sc);
	RH_ShadowStr ((rx - wd) * '1 0 0' + y * '0 1 0', s, sc, rgb, a, 0);
};

void(float cx, float cy, float rad, float segs, float rot_deg, float wline, vector col, float a) RH_Circle =
{
	local float i, step, a0, a1, c0, s0, c1, s1;
	local vector p0, p1;

	step = 360 / segs;
	i = 0;
	while (i < segs)
	{
		a0 = (rot_deg + i * step) * RH_DEG2RAD;
		a1 = (rot_deg + (i + 1) * step) * RH_DEG2RAD;
		c0 = RH_Cos (a0);
		s0 = RH_Sin (a0);
		c1 = RH_Cos (a1);
		s1 = RH_Sin (a1);
		p0 = (cx + c0 * rad) * '1 0 0' + (cy + s0 * rad) * '0 1 0';
		p1 = (cx + c1 * rad) * '1 0 0' + (cy + s1 * rad) * '0 1 0';
		RH_Line (wline, p0, p1, col, a);
		i = i + 1;
	}
};

// Translucent corner-anchored window panel with crisp 1px border + bright corner accents
void(float x, float y, float pw, float ph, vector bg, float bg_a, vector bd, float bd_a, vector corner_col) RH_WindowBox =
{
	local float c;

	if (pw < 8 || ph < 8)
		return;
	c = 5;
	drawfill (x * '1 0 0' + y * '0 1 0', pw * '1 0 0' + ph * '0 1 0', bg, bg_a, 0);
	drawfill (x * '1 0 0' + y * '0 1 0', pw * '1 0 0' + '0 1 0', bd, bd_a, 0);
	drawfill (x * '1 0 0' + (y + ph - 1) * '0 1 0', pw * '1 0 0' + '0 1 0', bd, bd_a, 0);
	drawfill (x * '1 0 0' + y * '0 1 0', '1 0 0' + ph * '0 1 0', bd, bd_a, 0);
	drawfill ((x + pw - 1) * '1 0 0' + y * '0 1 0', '1 0 0' + ph * '0 1 0', bd, bd_a, 0);

	// Bright tech corner ticks
	drawfill (x * '1 0 0' + y * '0 1 0', c * '1 0 0' + '0 1 0', corner_col, 0.95, 0);
	drawfill (x * '1 0 0' + y * '0 1 0', '1 0 0' + c * '0 1 0', corner_col, 0.95, 0);
	drawfill ((x + pw - c) * '1 0 0' + y * '0 1 0', c * '1 0 0' + '0 1 0', corner_col, 0.95, 0);
	drawfill ((x + pw - 1) * '1 0 0' + y * '0 1 0', '1 0 0' + c * '0 1 0', corner_col, 0.95, 0);
	drawfill (x * '1 0 0' + (y + ph - 1) * '0 1 0', c * '1 0 0' + '0 1 0', corner_col, 0.95, 0);
	drawfill (x * '1 0 0' + (y + ph - c) * '0 1 0', '1 0 0' + c * '0 1 0', corner_col, 0.95, 0);
	drawfill ((x + pw - c) * '1 0 0' + (y + ph - 1) * '0 1 0', c * '1 0 0' + '0 1 0', corner_col, 0.95, 0);
	drawfill ((x + pw - 1) * '1 0 0' + (y + ph - c) * '0 1 0', '1 0 0' + c * '0 1 0', corner_col, 0.95, 0);
};

void(float cx, float cy, float rad, float a, vector col, float locked) RH_DrawTargetBracket =
{
	local float arm, sy;
	local vector hx, vy;

	arm = bound (3, floor (rad * 0.42), 7);
	hx = arm * '1 0 0' + '0 1 0';
	vy = '1 0 0' + arm * '0 1 0';

	drawfill ((cx - rad) * '1 0 0' + (cy - rad) * '0 1 0', hx, col, a, 0);
	drawfill ((cx - rad) * '1 0 0' + (cy - rad) * '0 1 0', vy, col, a, 0);
	drawfill ((cx + rad - arm) * '1 0 0' + (cy - rad) * '0 1 0', hx, col, a, 0);
	drawfill ((cx + rad - 1) * '1 0 0' + (cy - rad) * '0 1 0', vy, col, a, 0);
	drawfill ((cx - rad) * '1 0 0' + (cy + rad - 1) * '0 1 0', hx, col, a, 0);
	drawfill ((cx - rad) * '1 0 0' + (cy + rad - arm) * '0 1 0', vy, col, a, 0);
	drawfill ((cx + rad - arm) * '1 0 0' + (cy + rad - 1) * '0 1 0', hx, col, a, 0);
	drawfill ((cx + rad - 1) * '1 0 0' + (cy + rad - arm) * '0 1 0', vy, col, a, 0);

	// Active horizontal laser scanline sweeping inside the target bracket
	sy = cy + RH_Sin (time * 6.5 + cx * 0.05) * (rad * 0.72);
	drawfill ((cx - rad + 2) * '1 0 0' + sy * '0 1 0', max (2, (rad * 2 - 4)) * '1 0 0' + '0 1 0', col, a * 0.45, 0);

	if (locked)
		RH_Circle (cx, cy, rad * 1.28, 8, time * 75, 1.0, '1.0 0.22 0.22', a * 0.90);
};

void(entity t, vector cam_org, float w, float h, float top_h, float bot_h, float sz, vector col_red, vector col_cyan) RH_DrawEdgePip =
{
	local vector delta, tip, lwing, rwing;
	local float dist, dirx, diry, dlen, px, py, nx, ny, a;

	if (!t)
		return;
	delta = (t.origin + '0 0 24') - cam_org;
	dist = vlen (delta);
	a = 0.75 * (1 - bound (0, (dist - 900) / 1600, 0.55));
	dirx = delta * v_right;
	diry = 0 - (delta * v_up);
	dlen = sqrt (dirx * dirx + diry * diry);
	if (dlen < 0.001)
	{
		dirx = 0;
		diry = 1;
	}
	else
	{
		dirx = dirx / dlen;
		diry = diry / dlen;
	}
	px = bound (14, w * 0.5 + dirx * (w * 0.5 - 18), w - 14);
	py = bound (top_h + 12, h * 0.5 + diry * (h * 0.5 - top_h - 16), h - bot_h - 12);

	tip = (px + dirx * 6) * '1 0 0' + (py + diry * 6) * '0 1 0';
	nx = -diry;
	ny = dirx;
	lwing = (px - dirx * 4.5 + nx * 5) * '1 0 0' + (py - diry * 4.5 + ny * 5) * '0 1 0';
	rwing = (px - dirx * 4.5 - nx * 5) * '1 0 0' + (py - diry * 4.5 - ny * 5) * '0 1 0';
	RH_Line (1.6, tip, lwing, col_red, a);
	RH_Line (1.6, tip, rwing, col_red, a);
	RH_Line (1.0, lwing, rwing, col_cyan, a * 0.75);
	BM_ShadowCentered (px - dirx * 16, py - diry * 10 - sz * 0.4, strcat (ftos (floor (dist)), "u"), sz * 0.85, col_cyan, a);
};

// 14 unique Kali / Red Hat Linux hacking sequences (real Linux commands, funny Quake/wallhack payloads)
// slot: 0=cmd1, 1=out1, 2=cmd2, 3=banner, 4=scan_msg, 5=result_msg
string(float seq, float slot, float n_en) RH_SeqLine =
{
	local string nstr;

	nstr = ftos (n_en);
	if (seq == 1)
	{
		if (slot == 0) return "sudo apt install -y quakeahh.exe";
		if (slot == 1) return "Unpacking quakeahh.exe (420 KB)...";
		if (slot == 2) return "exec WallHacks.cfg --no-walls";
		if (slot == 3) return "[!] EXECUTING WALLHACKS.CFG";
		if (slot == 4) return "[*] DOWNLOADING MORE WALLHACK RAM..";
		return strcat ("[+] FOUND ", nstr, " NOOBS THRU WALLS!");
	}
	if (seq == 2)
	{
		if (slot == 0) return "sudo dnf install -y rhel-wallhacks";
		if (slot == 1) return "Installed: rhel-wallhacks-9.4.x86_64";
		if (slot == 2) return "systemctl start wallhackd.service";
		if (slot == 3) return "[!] RED HAT WALLHACKS ONLINE";
		if (slot == 4) return "[*] BYPASSING PVS LIKE A MENACE...";
		return strcat ("[+] EXPOSED ", nstr, " CAMPERS IN X-RAY!");
	}
	if (seq == 3)
	{
		if (slot == 0) return "nmap -sS -p 26000 --open 10.0.0/24";
		if (slot == 1) return "26000/udp open  quake-noobs";
		if (slot == 2) return "LD_PRELOAD=/lib/xray.so ./hax.sh";
		if (slot == 3) return "[!] LD_PRELOAD WALLHACKS INJECTED";
		if (slot == 4) return "[*] SNIFFING ENEMY SOCKS COORDS...";
		return strcat ("[+] TRACED ", nstr, " VICTIMS BEHIND BRICK!");
	}
	if (seq == 4)
	{
		if (slot == 0) return "sudo rm -rf /var/log/skill_issue";
		if (slot == 1) return "removed '/var/log/skill_issue'";
		if (slot == 2) return "python3 -m wallhack --bozo-scan";
		if (slot == 3) return "[!] ZERO SKILL ISSUE DETECTED";
		if (slot == 4) return "[*] ENHANCE. ENHANCE. ENHANCE...";
		return strcat ("[+] LOCKED ON ", nstr, " FREE FRAGS!");
	}
	if (seq == 5)
	{
		if (slot == 0) return "curl -sL hax.bako.lan/xray.sh | sh";
		if (slot == 1) return "[+] Piped 100% safe shell script";
		if (slot == 2) return "exec /usr/local/bin/WallHacks.cfg";
		if (slot == 3) return "[!] CURL | SH WALLHACKS ACTIVE";
		if (slot == 4) return "[*] PEEKING THRU EVERY BRICK WALL..";
		return strcat ("[+] GOT ", nstr, " CHUMPS IN 4K X-RAY!");
	}
	if (seq == 6)
	{
		if (slot == 0) return "sudo insmod /lib/see_thru_walls.ko";
		if (slot == 1) return "insmod: tainted kernel (2 much hax)";
		if (slot == 2) return "cat /proc/enemy_locations | head";
		if (slot == 3) return "[!] KERNEL WALLHACK MODULE LOADED";
		if (slot == 4) return "[*] DUMPING CAMPER COORDS FROM RAM.";
		return strcat ("[+] ", nstr, " NOOBS CANNOT HIDE NOW!");
	}
	if (seq == 7)
	{
		if (slot == 0) return "chmod +x ~/Desktop/totally_legit.sh";
		if (slot == 1) return "mode of 'totally_legit.sh' -> 0755";
		if (slot == 2) return "sudo ~/Desktop/totally_legit.sh";
		if (slot == 3) return "[!] 100% LEGIT LINUX WALLHACKS";
		if (slot == 4) return "[*] AUDITING ALL COWARD SPOTS...";
		return strcat ("[+] CAUGHT ", nstr, " FOES RED-HANDED!");
	}
	if (seq == 8)
	{
		if (slot == 0) return "tar -xzf rob_wallhacks_v69.tar.gz";
		if (slot == 1) return "extracted: WallHacks.cfg, xray.bin";
		if (slot == 2) return "nohup ./xray.bin --wallhack &";
		if (slot == 3) return "[!] BACKGROUND WALLHACK DAEMON";
		if (slot == 4) return "[*] TRIANGULATING ROCKET JUMPERS..";
		return strcat ("[+] FLAGGED ", nstr, " TARGETS 4 BIG KISS!");
	}
	if (seq == 9)
	{
		if (slot == 0) return "sudo gdb -q -p $(pidof zircon)";
		if (slot == 1) return "Attached to process :: glDepthFunc";
		if (slot == 2) return "kill -SIGUSR1 $(pgrep quake)";
		if (slot == 3) return "[!] MEMORY PATCH: WALLS = OFF";
		if (slot == 4) return "[*] READING MAP LEAF PVS TABLE...";
		return strcat ("[+] DOXXED ", nstr, " PLAYERS ON MAP!");
	}
	if (seq == 10)
	{
		if (slot == 0) return "sudo pacman -S --noconfirm aim-xray";
		if (slot == 1) return "warning: aim-xray is unfair lol";
		if (slot == 2) return "exec WallHacks.cfg --fedora";
		if (slot == 3) return "[!] EXECUTING WALLHACKS.CFG";
		if (slot == 4) return "[*] PINGING 127.0.0.1 FOR NOOBS..";
		return strcat ("[+] FOUND ", nstr, " NOOBS IN HD X-RAY!");
	}
	if (seq == 11)
	{
		if (slot == 0) return "docker run --rm kali/quake-wallhack";
		if (slot == 1) return "Container up :: PVS bypass ready";
		if (slot == 2) return "sudo ./wallhack_daemon --cyan";
		if (slot == 3) return "[!] DOCKERIZED WALLHACKS LIVE";
		if (slot == 4) return "[*] RENDERING THRU CONCRETE WALLS.";
		return strcat ("[+] ", nstr, " TARGETS TOTALLY EXPOSED!");
	}
	if (seq == 12)
	{
		if (slot == 0) return "ssh -i ~/.ssh/hax root@bako-lan";
		if (slot == 1) return "Welcome to Red Hat Linux (Wallhack)";
		if (slot == 2) return "sudo sysctl -w quake.walls=0";
		if (slot == 3) return "[!] SSH TUNNEL WALLHACKS ARMED";
		if (slot == 4) return "[*] CALCULATING POCKET COORDS...";
		return strcat ("[+] TRACKING ", nstr, " POOR VICTIMS!");
	}
	if (seq == 13)
	{
		if (slot == 0) return "tcpdump -ni wlan0 udp port 26000";
		if (slot == 1) return "listening on wlan0, link-type EN10MB";
		if (slot == 2) return "grep -a \"camp\" /dev/shm/quake.mem";
		if (slot == 3) return "[!] PACKET SNIFFER WALLHACK ON";
		if (slot == 4) return "[*] INTERCEPTING ENEMY FOOTSTEPS.";
		return strcat ("[+] ", nstr, " CAMPERS SPOTTED IN X-RAY!");
	}
	if (slot == 0) return "gcc -O3 wallhack.c -o /tmp/hax";
	if (slot == 1) return "0 errors, 69 warnings (ignored)";
	if (slot == 2) return "exec /tmp/hax --no-mercy --xray";
	if (slot == 3) return "[!] COMPILED WALLHACKS RUNNING";
	if (slot == 4) return "[*] TELLING ROB ALL ENEMY COORDS..";
	return strcat ("[+] ", nstr, " VICTIMS READY 4 DETONATION!");
};

string(float idx) RH_LiveCmd =
{
	local float k;

	k = idx - 14 * floor (idx / 14);
	if (k == 0) return "sudo apt upgrade -y quakeahh.exe";
	if (k == 1) return "exec WallHacks.cfg --verbose";
	if (k == 2) return "cat /proc/noobs_behind_walls";
	if (k == 3) return "ss -uapn | grep 26000";
	if (k == 4) return "tail -n1 /var/log/wallhack.log";
	if (k == 5) return "sudo chmod 777 /etc/enemy_spawns";
	if (k == 6) return "grep -i \"camper\" /proc/quake_map";
	if (k == 7) return "watch -n0 cat /dev/fedora_hax";
	if (k == 8) return "sudo systemctl status xrayd";
	if (k == 9) return "ping -c1 -W1 10.13.37.69";
	if (k == 10) return "ps aux | grep -i wallhack";
	if (k == 11) return "uname -a && whoami";
	if (k == 12) return "sudo journalctl -u wallhack -n1";
	return "dmesg | tail -n1";
};

string(float idx, float n_en) RH_LiveOut =
{
	local float k;
	local string nstr;

	nstr = ftos (n_en);
	k = idx - 14 * floor (idx / 14);
	if (k == 0) return "[APT] quakeahh.exe upgraded to v4.20";
	if (k == 1) return "[CFG] WALLHACKS.CFG APPLIED OK";
	if (k == 2) return strcat ("[SYS] ", nstr, " NOOBS EXPOSED IN REALTIME");
	if (k == 3) return "[NET] UDP:26000 ESTAB rtt=1.2ms";
	if (k == 4) return strcat ("[LOG] PVS_BYPASS=1 | ", nstr, " LOCKED");
	if (k == 5) return "[FS] WORLD-READABLE SPAWN COORDS";
	if (k == 6) return strcat ("[SCAN] ", nstr, " CAMPERS TRACKED ON RADAR");
	if (k == 7) return "[DEV] EF_NODEPTHTEST=ACTIVE";
	if (k == 8) return "[SVC] xrayd.service: active (hacking)";
	if (k == 9) return "[ICMP] 64 bytes from noob: ttl=64";
	if (k == 10) return "[PID] root 1337 WallHacks.cfg";
	if (k == 11) return "[ID] Linux kali-rhel9 :: root (hax)";
	if (k == 12) return "[JRN] GL_DEPTH_TEST=FALSE SYNCED";
	return "[KRN] rob_drone0: XRAY LINK UP";
};

// Draws Red Hat Linux neofetch ASCII art + system spec row 0..6
void(float bx, float y, float row, float tfont, vector tsv, vector col_red, vector col_cyan, vector col_white, vector col_green) RH_DrawNeofetchRow =
{
	local float hat_w, art_cx, col2_x, aw, lw, rw;
	local string art, lbl, val;

	hat_w = stringwidth ("[== RED HAT ==]", FALSE, tsv);
	art_cx = bx + hat_w * 0.5 + 2;
	col2_x = bx + hat_w + tfont * 1.4;
	if (row == 0)
	{
		art = ".#####.";
		lbl = "root@kali-rhel9";
		val = "";
	}
	else if (row == 1)
	{
		art = "./#######\\.";
		lbl = "-------------------";
		val = "";
	}
	else if (row == 2)
	{
		art = "/##/     \\##\\";
		lbl = "OS: ";
		val = "Red Hat Linux 9";
	}
	else if (row == 3)
	{
		art = "/##/       \\##\\";
		lbl = "Kernel: ";
		val = "6.8-kali-x64";
	}
	else if (row == 4)
	{
		art = "/#############\\";
		lbl = "Shell: ";
		val = "zsh 5.9 tty0";
	}
	else if (row == 5)
	{
		art = "[== RED HAT ==]";
		lbl = "Bypass: ";
		val = "PVS + GL_DEPTH";
	}
	else
	{
		art = "'---------'";
		lbl = "Mode: ";
		val = "WALLHACK X-RAY";
	}

	if (row == 2)
	{
		lw = stringwidth ("/##/", FALSE, tsv);
		RH_ShadowStr ((art_cx - tfont * 1.4 - lw) * '1 0 0' + y * '0 1 0', "/##/", tsv, col_red, 1.0, 0);
		RH_ShadowStr ((art_cx + tfont * 1.4) * '1 0 0' + y * '0 1 0', "\\##\\", tsv, col_red, 1.0, 0);
	}
	else if (row == 3)
	{
		lw = stringwidth ("/##/", FALSE, tsv);
		RH_ShadowStr ((art_cx - tfont * 2.0 - lw) * '1 0 0' + y * '0 1 0', "/##/", tsv, col_red, 1.0, 0);
		RH_ShadowStr ((art_cx + tfont * 2.0) * '1 0 0' + y * '0 1 0', "\\##\\", tsv, col_red, 1.0, 0);
	}
	else
	{
		aw = stringwidth (art, FALSE, tsv);
		RH_ShadowStr ((art_cx - aw * 0.5) * '1 0 0' + y * '0 1 0', art, tsv, col_red, 1.0, 0);
	}

	if (row == 0)
		RH_ShadowStr (col2_x * '1 0 0' + y * '0 1 0', lbl, tsv, col_cyan, 1.0, 0);
	else if (row == 1)
		RH_ShadowStr (col2_x * '1 0 0' + y * '0 1 0', lbl, tsv, '0.62 0.84 0.96', 0.95, 0);
	else
	{
		RH_ShadowStr (col2_x * '1 0 0' + y * '0 1 0', lbl, tsv, col_red, 1.0, 0);
		rw = stringwidth (lbl, FALSE, tsv);
		RH_ShadowStr ((col2_x + rw) * '1 0 0' + y * '0 1 0', val, tsv, (row == 6) ? col_green : col_white, 1.0, 0);
	}
};

// Draws one virtual scrollback line 0..total_lines-1 inside the terminal body
void(float idx, float bx, float y, float tfont, vector tsv, float seq, float n_en, float pulse, float cur_t0, float cur_t1, string c0, string c1, string live_cur, float live_done, float live_idx, entity en1, entity en2, entity en3, vector cam_org, float mode, vector col_red, vector col_cyan, vector col_white, vector col_green, vector col_amber) RH_DrawTermRow =
{
	local string s, pfx, spin, bar;
	local float pw, dist, pct, k;
	local entity targ;

	// 0: neofetch command
	if (idx == 0)
	{
		pfx = "# ";
		RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', pfx, tsv, col_red, 1.0, 0);
		pw = stringwidth (pfx, FALSE, tsv);
		RH_ShadowStr ((bx + pw) * '1 0 0' + y * '0 1 0', "neofetch --distro rhel", tsv, col_green, 1.0, 0);
		return;
	}
	// 1..7: Red Hat neofetch ASCII art + specs
	if (idx >= 1 && idx <= 7)
	{
		RH_DrawNeofetchRow (bx, y, idx - 1, tfont, tsv, col_red, col_cyan, col_white, col_green);
		return;
	}
	// 8: Command 1
	if (idx == 8)
	{
		pfx = "kali# ";
		RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', pfx, tsv, col_red, 1.0, 0);
		pw = stringwidth (pfx, FALSE, tsv);
		s = cur_t0 ? strcat (c0, "_") : c0;
		RH_ShadowStr ((bx + pw) * '1 0 0' + y * '0 1 0', s, tsv, col_green, 1.0, 0);
		return;
	}
	// 9: Output 1
	if (idx == 9)
	{
		RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', RH_SeqLine (seq, 1, n_en), tsv, col_cyan, 1.0, 0);
		return;
	}
	// 10: Command 2
	if (idx == 10)
	{
		pfx = "kali# ";
		RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', pfx, tsv, col_red, 1.0, 0);
		pw = stringwidth (pfx, FALSE, tsv);
		s = cur_t1 ? strcat (c1, "_") : c1;
		RH_ShadowStr ((bx + pw) * '1 0 0' + y * '0 1 0', s, tsv, col_white, 1.0, 0);
		return;
	}
	// 11: Banner
	if (idx == 11)
	{
		RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', RH_SeqLine (seq, 3, n_en), tsv, col_red, 1.0, 0);
		return;
	}
	// 12: Scan line + progress bar
	if (idx == 12)
	{
		RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', RH_SeqLine (seq, 4, n_en), tsv, col_amber, 1.0, 0);
		return;
	}
	// 13: Result count
	if (idx == 13)
	{
		RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', RH_SeqLine (seq, 5, n_en), tsv, col_green, 1.0, 0);
		return;
	}
	// 14..16: Live target coordinate dumps from rh_xray_head
	if (idx >= 14 && idx <= 16)
	{
		targ = world;
		if (idx == 14) targ = en1;
		else if (idx == 15) targ = en2;
		else if (idx == 16) targ = en3;
		if (targ)
		{
			s = targ.netname;
			if (s == "") s = "HOSTILE";
			if (strlen (s) > 10) s = substring (s, 0, 10);
			dist = floor (vlen (targ.origin - cam_org));
			s = strcat ("> [", ftos (idx - 13), "] ", s, " ", ftos (targ.rh_hp), "HP ");
			s = strcat (s, ftos (dist), "u");
			RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', s, tsv, (dist < 460) ? col_red : col_cyan, 1.0, 0);
		}
		else if (idx == 14)
		{
			k = floor (time * 8) - 4 * floor (floor (time * 8) / 4);
			if (k == 0) spin = "|";
			else if (k == 1) spin = "/";
			else if (k == 2) spin = "-";
			else spin = "\\";
			pct = floor (50 + 50 * RH_Sin (time * 3));
			bar = (pct > 66) ? "[########--]" : ((pct > 33) ? "[#####-----]" : "[###-------]");
			RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', strcat (spin, " SWEEPING SECTOR ", bar), tsv, col_cyan, 1.0, 0);
		}
		else
		{
			RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', "[SCAN] NO CLOSE CONTACTS IN PVS", tsv, '0.72 0.90 0.98', 0.96, 0);
		}
		return;
	}
	// 17+: Continuous live Linux commands + output pairs (2 rows per live command)
	local float rel, pair, is_out, active_pair;
	rel = idx - 17;
	pair = floor (rel / 2);
	is_out = rel - pair * 2;
	active_pair = (pair == live_idx);

	if (mode == 3 && active_pair && is_out)
	{
		RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', "[!] SIGKILL: DRONE DETONATED!", tsv, col_red, 1.0, 0);
		return;
	}

	if (!is_out)
	{
		pfx = "kali# ";
		RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', pfx, tsv, col_red, 1.0, 0);
		pw = stringwidth (pfx, FALSE, tsv);
		if (active_pair)
			s = live_done ? strcat (live_cur, (pulse > 0) ? "_" : "") : strcat (live_cur, "_");
		else
			s = RH_LiveCmd (pair);
		RH_ShadowStr ((bx + pw) * '1 0 0' + y * '0 1 0', s, tsv, col_green, 1.0, 0);
	}
	else
	{
		RH_ShadowStr (bx * '1 0 0' + y * '0 1 0', RH_LiveOut (pair, n_en), tsv, col_white, 1.0, 0);
	}
};

void(float w, float h, float seq, float age, float mode, float n_en, float pulse, vector cam_org, entity en1, entity en2, entity en3, vector col_red, vector col_cyan, vector col_white, vector col_green, vector col_amber) RH_DrawTerminal =
{
	local float tx, ty, tw, th, cur_th, open_u, tfont, tlh, title_h, foot_h, body_y, max_rows;
	local float neo_rows, ch_rate, cmd0_len, cmd1_len, t_cmd0, t_cmd1, t_scan, t_live;
	local float cmd0_n, cmd1_n, total_rows, start_row, row, cur_ch, stage;
	local float lidx, lt, llen, lch, live_done, k;
	local string cmd0_full, cmd1_full, c0_draw, c1_draw, live_full, live_cur, spin;
	local vector tsv, bg_col, bd_col, bar_col;

	tfont = (rh_term_font > 0) ? bound (6.8, w * 0.0115, 11.5) : bound (4.8, w * 0.0078, 8.2);
	tsv = tfont * '1 1 0';
	tlh = (rh_term_font > 0) ? (tfont + 1.4) : (tfont + 2.4);

	tx = 8;
	ty = JBH_TopLeftY ();
	tw = bound (218, floor (w * 0.37), 410);
	title_h = tlh + 4;
	foot_h = tlh + 3;
	max_rows = 15;
	th = title_h + 4 + max_rows * tlh + 3 + foot_h;

	open_u = bound (0, age / 0.14, 1);
	cur_th = max (title_h + 6, floor (th * (1 - (1 - open_u) * (1 - open_u))));

	bg_col = '0 0 0';
	bd_col = (mode == 3) ? col_red : '0.92 0.24 0.28';
	bar_col = '0.03 0.03 0.04';

	RH_WindowBox (tx, ty, tw, cur_th, bg_col, 0.72, bd_col, 0.90, (mode == 3) ? col_red : col_cyan);

	// Title bar (black)
	drawfill ((tx + 1) * '1 0 0' + (ty + 1) * '0 1 0', (tw - 2) * '1 0 0' + (title_h - 1) * '0 1 0', bar_col, 0.88, 0);
	drawfill ((tx + 1) * '1 0 0' + (ty + title_h) * '0 1 0', (tw - 2) * '1 0 0' + '0 1 0', bd_col, 0.72, 0);

	// Classic terminal window buttons (red, amber, green)
	drawfill ((tx + 5) * '1 0 0' + (ty + floor (title_h * 0.5) - 1) * '0 1 0', '3 3 0', col_red, 0.98, 0);
	drawfill ((tx + 10) * '1 0 0' + (ty + floor (title_h * 0.5) - 1) * '0 1 0', '3 3 0', col_amber, 0.98, 0);
	drawfill ((tx + 15) * '1 0 0' + (ty + floor (title_h * 0.5) - 1) * '0 1 0', '3 3 0', col_green, 0.98, 0);

	RH_ShadowStr ((tx + 22) * '1 0 0' + (ty + 2) * '0 1 0', "root@kali-rhel9: ~/wallhack", tsv * 0.96, col_white, 1.0, 0);
	RH_ShadowStrRight (tx + tw - 5, ty + 2, "[ZSH]", tsv * 0.92, col_cyan, 0.96);

	if (open_u < 0.85)
		return;

	// Timeline calculation
	cmd0_full = RH_SeqLine (seq, 0, n_en);
	cmd1_full = RH_SeqLine (seq, 2, n_en);
	cmd0_len = strlen (cmd0_full);
	cmd1_len = strlen (cmd1_full);
	ch_rate = 38;

	// 0.08..0.36s: neofetch lines 0..7 cascade in rapidly
	neo_rows = bound (1, floor ((age - 0.08) / 0.036) + 1, 8);
	t_cmd0 = 0.38;
	cmd0_n = floor (max (0, age - t_cmd0) * ch_rate);
	t_cmd1 = t_cmd0 + cmd0_len / ch_rate + 0.14;
	cmd1_n = floor (max (0, age - t_cmd1) * ch_rate);
	t_scan = t_cmd1 + cmd1_len / ch_rate + 0.12;
	t_live = t_scan + 0.48;

	cur_ch = 0;
	stage = 0;
	total_rows = neo_rows;
	c0_draw = "";
	c1_draw = "";
	live_cur = "";
	live_done = 0;
	lidx = 0;

	if (age >= t_cmd0)
	{
		if (cmd0_n < cmd0_len)
		{
			c0_draw = substring (cmd0_full, 0, cmd0_n);
			cur_ch = cmd0_n;
			total_rows = 9;
		}
		else
		{
			c0_draw = cmd0_full;
			cur_ch = cmd0_len;
			stage = 1;
			total_rows = 10;
		}
	}
	if (age >= t_cmd1)
	{
		if (cmd1_n < cmd1_len)
		{
			c1_draw = substring (cmd1_full, 0, cmd1_n);
			cur_ch = cmd0_len + cmd1_n;
			total_rows = 11;
		}
		else
		{
			c1_draw = cmd1_full;
			cur_ch = cmd0_len + cmd1_len;
			stage = 2;
			total_rows = 12;
			if (age >= t_scan)
			{
				stage = 3;
				total_rows = 13;
			}
			if (age >= t_scan + 0.16)
			{
				stage = 4;
				total_rows = 14;
			}
			if (age >= t_scan + 0.30)
			{
				total_rows = 17;
			}
		}
	}

	if (age >= t_live)
	{
		lt = age - t_live;
		lidx = floor (lt / 2.1);
		live_full = RH_LiveCmd (lidx);
		llen = strlen (live_full);
		lch = floor ((lt - lidx * 2.1) * 32);
		if (lch < llen)
		{
			live_cur = substring (live_full, 0, lch);
			cur_ch = cmd0_len + cmd1_len + lidx * 32 + lch;
			stage = 5 + lidx * 2;
			total_rows = 17 + lidx * 2 + 1;
		}
		else
		{
			live_cur = live_full;
			live_done = 1;
			cur_ch = cmd0_len + cmd1_len + (lidx + 1) * 32;
			stage = 6 + lidx * 2;
			total_rows = 17 + (lidx + 1) * 2;
		}
	}

	// Render visible rows (auto-scrolls smoothly once > max_rows)
	body_y = ty + title_h + 4;
	start_row = max (0, total_rows - max_rows);
	row = start_row;
	while (row < total_rows)
	{
		RH_DrawTermRow (
			row,
			tx + 5,
			body_y + (row - start_row) * tlh,
			tfont,
			tsv,
			seq,
			n_en,
			pulse,
			(age >= t_cmd0 && cmd0_n < cmd0_len),
			(age >= t_cmd1 && cmd1_n < cmd1_len),
			c0_draw,
			c1_draw,
			live_cur,
			live_done,
			lidx,
			en1, en2, en3,
			cam_org,
			mode,
			col_red, col_cyan, col_white, col_green, col_amber
		);
		row = row + 1;
	}

	// Footer status bar inside terminal (black)
	local float fy;
	fy = ty + th - foot_h;
	drawfill ((tx + 1) * '1 0 0' + fy * '0 1 0', (tw - 2) * '1 0 0' + '0 1 0', bd_col, 0.65, 0);
	drawfill ((tx + 1) * '1 0 0' + (fy + 1) * '0 1 0', (tw - 2) * '1 0 0' + (foot_h - 2) * '0 1 0', bar_col, 0.84, 0);
	k = floor (time * 10) - 4 * floor (floor (time * 10) / 4);
	if (k == 0) spin = "|";
	else if (k == 1) spin = "/";
	else if (k == 2) spin = "-";
	else spin = "\\";
	if (mode == 3)
		RH_ShadowStr ((tx + 5) * '1 0 0' + (fy + 2) * '0 1 0', "[!] LINK TERMINATED // SIGNAL LOST", tsv * 0.92, col_red, 1.0, 0);
	else
		RH_ShadowStr ((tx + 5) * '1 0 0' + (fy + 2) * '0 1 0', strcat (spin, " SCANNING  |  PVS:OFF  |  ", ftos (n_en), " TARGETS"), tsv * 0.92, col_cyan, 1.0, 0);
};

void(float w, float h, float mode, float timer10, float spd, float armed, float n_en, float pulse, vector cam_org, vector col_red, vector col_cyan, vector col_white, vector col_green, vector col_ally) RH_DrawMiniMap =
{
	local float sz, lh, rrad, box_w, box_h, bx0, by0, rcx, rcy;
	local float sw_deg, sw_ang, swc, sws, i, ta, tx, ty, rf, rr, px, py, bear_deg, diff, ping;
	local vector sv, delta;
	local entity t;
	local string s;

	sz = (rh_term_font > 0) ? bound (6.6, floor (w * 0.0112), 11) : bound (5, floor (w * 0.0082), 8);
	sv = sz * '1 1 0';
	lh = sz + 1.5;

	rrad = bound (36, floor (h * 0.135), 64);
	box_w = rrad * 2 + 12;
	box_h = rrad * 2 + lh + 12;
	bx0 = w - 8 - box_w;
	by0 = 8;

	RH_WindowBox (bx0, by0, box_w, box_h, '0.02 0.04 0.06', 0.24, col_cyan, 0.78, (mode == 2 || mode == 3) ? col_red : col_cyan);
	drawfill ((bx0 + 1) * '1 0 0' + (by0 + 1) * '0 1 0', (box_w - 2) * '1 0 0' + (lh + 2) * '0 1 0', '0.03 0.10 0.14', 0.38, 0);
	drawfill ((bx0 + 1) * '1 0 0' + (by0 + lh + 3) * '0 1 0', (box_w - 2) * '1 0 0' + '0 1 0', col_cyan, 0.65, 0);

	RH_ShadowStr ((bx0 + 5) * '1 0 0' + (by0 + 2) * '0 1 0', "MINIMAP", sv * 0.94, col_cyan, 1.0, 0);
	RH_ShadowStrRight (bx0 + box_w - 4, by0 + 2, strcat (ftos (n_en), (n_en == 1) ? " HOSTILE" : " HOSTILES"), sv * 0.92, (n_en > 0) ? col_red : col_green, 1.0);

	rcx = bx0 + box_w * 0.5;
	rcy = by0 + lh + 7 + rrad;

	// Concentric range rings & crosshairs
	RH_Circle (rcx, rcy, rrad, 28, 0, 1.2, col_cyan, 0.65);
	RH_Circle (rcx, rcy, rrad * 0.66, 20, 0, 1.0, col_cyan, 0.30);
	RH_Circle (rcx, rcy, rrad * 0.33, 14, 0, 1.0, col_cyan, 0.22);
	RH_Line (1.0, (rcx - rrad) * '1 0 0' + rcy * '0 1 0', (rcx + rrad) * '1 0 0' + rcy * '0 1 0', col_cyan, 0.22);
	RH_Line (1.0, rcx * '1 0 0' + (rcy - rrad) * '0 1 0', rcx * '1 0 0' + (rcy + rrad) * '0 1 0', col_cyan, 0.22);

	// Drone camera forward FOV cone (+/- 42 deg up from center)
	RH_Line (1.0, rcx * '1 0 0' + rcy * '0 1 0', (rcx - rrad * 0.66) * '1 0 0' + (rcy - rrad * 0.74) * '0 1 0', col_white, 0.28);
	RH_Line (1.0, rcx * '1 0 0' + rcy * '0 1 0', (rcx + rrad * 0.66) * '1 0 0' + (rcy - rrad * 0.74) * '0 1 0', col_white, 0.28);

	// Rotating radar sweep + 3 trailing phosphor fade rays
	sw_deg = time * 165;
	i = 3;
	while (i >= 1)
	{
		sw_ang = (sw_deg - i * 8) * RH_DEG2RAD;
		swc = RH_Cos (sw_ang);
		sws = RH_Sin (sw_ang);
		RH_Line (1.0, rcx * '1 0 0' + rcy * '0 1 0', (rcx + swc * rrad) * '1 0 0' + (rcy + sws * rrad) * '0 1 0', col_cyan, 0.32 - i * 0.07);
		i = i - 1;
	}
	sw_ang = sw_deg * RH_DEG2RAD;
	swc = RH_Cos (sw_ang);
	sws = RH_Sin (sw_ang);
	RH_Line (1.5, rcx * '1 0 0' + rcy * '0 1 0', (rcx + swc * rrad) * '1 0 0' + (rcy + sws * rrad) * '0 1 0', col_cyan, 0.92);

	// Outer 4-way ticks
	i = 0;
	while (i < 8)
	{
		ta = (i * 45) * RH_DEG2RAD;
		tx = RH_Cos (ta);
		ty = RH_Sin (ta);
		RH_Line (1.0, (rcx + tx * (rrad - 3)) * '1 0 0' + (rcy + ty * (rrad - 3)) * '0 1 0', (rcx + tx * rrad) * '1 0 0' + (rcy + ty * rrad) * '0 1 0', col_cyan, 0.55);
		i = i + 1;
	}

	// Drone center marker + forward arrow tip on top ring
	drawfill ((rcx - 1.5) * '1 0 0' + (rcy - 1.5) * '0 1 0', '3 3 0', col_white, 0.98, 0);
	drawfill ((rcx - 0.5) * '1 0 0' + (rcy - rrad - 2) * '0 1 0', '1.5 3 0', col_white, 0.85, 0);

	// Blips with sweep-triggered ping ring
	t = rh_xray_head;
	while (t)
	{
		if (time - t.rh_last_t <= 0.6)
		{
			delta = t.origin - cam_org;
			delta_z = 0;
			rf = delta * v_forward;
			rr = delta * v_right;
			px = rcx + bound (-1, rr / 2600, 1) * (rrad - 3);
			py = rcy - bound (-1, rf / 2600, 1) * (rrad - 3);

			// Sweep angle in radar screen space (0=right, +90=down): dx=rr, dy=-rf
			bear_deg = RH_Atan2Deg (-rf, rr);
			diff = fabs (RH_Wrap180 (sw_deg - bear_deg));
			ping = max (0, 1 - diff / 34);

			if (ping > 0.1)
				RH_Circle (px, py, 2.5 + (1 - ping) * 5, 10, 0, 1.0, (t.rh_flags & 2) ? col_ally : col_red, ping * 0.75);
			drawfill ((px - 1.5) * '1 0 0' + (py - 1.5) * '0 1 0', '3 3 0', (t.rh_flags & 2) ? col_ally : col_red, 0.96, 0);
		}
		t = t.rh_next;
	}

	// Telemetry stacked cleanly right below the minimap box
	local float ft_y;
	ft_y = by0 + box_h + 4;
	if (mode == 2)
		RH_ShadowStrRight (w - 8, ft_y, ">> DASHING <<", sv, col_red, 0.82 + 0.18 * pulse);
	else if (mode == 3)
		RH_ShadowStrRight (w - 8, ft_y, "SIGNAL LOST", sv, col_red, 0.94);
	else
		RH_ShadowStrRight (w - 8, ft_y, armed ? "CRUISE [ARMED]" : "CRUISE [BOOT]", sv, col_cyan, 0.92);

	if (timer10 == 999)
		s = "UNLIMITED";
	else
		s = strcat ("FUEL ", ftos (floor (timer10 / 10)), ".", ftos (timer10 - 10 * floor (timer10 / 10)), "s");
	RH_ShadowStrRight (w - 8, ft_y + lh, strcat (ftos (spd), " u/s  |  ", s), sv, (timer10 < 40 && timer10 != 999) ? col_red : col_white, 0.88);
	bm_topright_y = ft_y + 2 * lh;
};

// Detailed Raspberry Pi 4B PCB widget stacked cleanly under the minimap telemetry
void(float w, float h, float mode, vector col_red, vector col_cyan, vector col_white, vector col_green, vector col_amber) RH_DrawRaspberryPi =
{
	local float sz, rrad, box_w, px, py, pw, ph, i, pin_x, cx, cy, cw, ch, act_on, temp_c;
	local vector sv, pcb_col, pcb_bd, gold_col, chip_col, metal_col;

	sz = (rh_term_font > 0) ? 6.4 : 4.8;
	sv = sz * '1 1 0';
	rrad = bound (36, floor (h * 0.135), 64);
	box_w = rrad * 2 + 12;

	pw = box_w - 6;
	ph = floor (pw * 0.56);
	px = w - 8 - box_w + 2;
	py = bm_topright_y + 6;

	pcb_col = '0.06 0.36 0.12';
	pcb_bd = '0.28 0.92 0.42';
	gold_col = '0.96 0.80 0.24';
	chip_col = '0.04 0.04 0.06';
	metal_col = '0.72 0.78 0.84';

	// Green PCB board + trace border
	drawfill (px * '1 0 0' + py * '0 1 0', pw * '1 0 0' + ph * '0 1 0', pcb_col, 0.80, 0);
	drawfill (px * '1 0 0' + py * '0 1 0', pw * '1 0 0' + '0 1 0', pcb_bd, 0.88, 0);
	drawfill (px * '1 0 0' + (py + ph - 1) * '0 1 0', pw * '1 0 0' + '0 1 0', pcb_bd, 0.88, 0);
	drawfill (px * '1 0 0' + py * '0 1 0', '1 0 0' + ph * '0 1 0', pcb_bd, 0.88, 0);
	drawfill ((px + pw - 1) * '1 0 0' + py * '0 1 0', '1 0 0' + ph * '0 1 0', pcb_bd, 0.88, 0);

	// 4 gold corner mounting holes
	drawfill ((px + 3) * '1 0 0' + (py + 3) * '0 1 0', '3 3 0', gold_col, 0.95, 0);
	drawfill ((px + 4) * '1 0 0' + (py + 4) * '0 1 0', '1 1 0', '0 0 0', 0.95, 0);
	drawfill ((px + pw - 6) * '1 0 0' + (py + 3) * '0 1 0', '3 3 0', gold_col, 0.95, 0);
	drawfill ((px + pw - 5) * '1 0 0' + (py + 4) * '0 1 0', '1 1 0', '0 0 0', 0.95, 0);
	drawfill ((px + 3) * '1 0 0' + (py + ph - 6) * '0 1 0', '3 3 0', gold_col, 0.95, 0);
	drawfill ((px + 4) * '1 0 0' + (py + ph - 5) * '0 1 0', '1 1 0', '0 0 0', 0.95, 0);
	drawfill ((px + pw - 6) * '1 0 0' + (py + ph - 6) * '0 1 0', '3 3 0', gold_col, 0.95, 0);
	drawfill ((px + pw - 5) * '1 0 0' + (py + ph - 5) * '0 1 0', '1 1 0', '0 0 0', 0.95, 0);

	// 40-pin GPIO header strip along top edge (2 rows of gold pins)
	local float gpio_w;
	gpio_w = floor (pw * 0.56);
	drawfill ((px + 10) * '1 0 0' + (py + 2) * '0 1 0', gpio_w * '1 0 0' + '0 6 0', chip_col, 0.92, 0);
	i = 0;
	while (i < 12)
	{
		pin_x = px + 12 + i * floor ((gpio_w - 4) / 12);
		drawfill (pin_x * '1 0 0' + (py + 3) * '0 1 0', '1.5 1.5 0', gold_col, 0.95, 0);
		drawfill (pin_x * '1 0 0' + (py + 5.5) * '0 1 0', '1.5 1.5 0', gold_col, 0.95, 0);
		i = i + 1;
	}

	// Copper PCB traces
	RH_Line (1.0, (px + 12) * '1 0 0' + (py + 12) * '0 1 0', (px + floor (pw * 0.42)) * '1 0 0' + (py + floor (ph * 0.48)) * '0 1 0', pcb_bd, 0.45);
	RH_Line (1.0, (px + 16) * '1 0 0' + (py + ph - 10) * '0 1 0', (px + floor (pw * 0.42)) * '1 0 0' + (py + floor (ph * 0.58)) * '0 1 0', pcb_bd, 0.45);
	RH_Line (1.0, (px + floor (pw * 0.56)) * '1 0 0' + (py + floor (ph * 0.52)) * '0 1 0', (px + pw - 14) * '1 0 0' + (py + floor (ph * 0.52)) * '0 1 0', pcb_bd, 0.45);

	// Central Broadcom SoC CPU chip + pins
	cw = floor (pw * 0.24);
	ch = cw;
	cx = px + floor (pw * 0.34);
	cy = py + floor (ph * 0.34);
	drawfill ((cx - 1) * '1 0 0' + (cy - 1) * '0 1 0', (cw + 2) * '1 0 0' + (ch + 2) * '0 1 0', metal_col, 0.72, 0);
	drawfill (cx * '1 0 0' + cy * '0 1 0', cw * '1 0 0' + ch * '0 1 0', chip_col, 0.96, 0);
	RH_ShadowStr ((cx + 2) * '1 0 0' + (cy + floor (ch * 0.30)) * '0 1 0', "BCM", sv * 0.82, metal_col, 0.95, 0);

	// Secondary LPDDR RAM / WiFi IC on left
	drawfill ((px + 10) * '1 0 0' + (cy + 2) * '0 1 0', '11 10 0', chip_col, 0.94, 0);
	drawfill ((px + 10) * '1 0 0' + (cy + 2) * '0 1 0', '11 1 0', metal_col, 0.55, 0);

	// Raspberry berry logo mark (red berry + green leaf) near top-left of PCB
	drawfill ((px + 11) * '1 0 0' + (py + 13) * '0 1 0', '4 1.5 0', col_green, 0.96, 0);
	drawfill ((px + 10) * '1 0 0' + (py + 15) * '0 1 0', '6 6 0', col_red, 0.96, 0);

	// Metallic USB & Ethernet ports protruding on right edge
	drawfill ((px + pw - 11) * '1 0 0' + (py + 10) * '0 1 0', '13 11 0', metal_col, 0.92, 0);
	drawfill ((px + pw - 3) * '1 0 0' + (py + 12) * '0 1 0', '4 7 0', '0.10 0.12 0.15', 0.92, 0);
	drawfill ((px + pw - 10) * '1 0 0' + (py + 25) * '0 1 0', '12 9 0', metal_col, 0.90, 0);
	drawfill ((px + pw - 10) * '1 0 0' + (py + 37) * '0 1 0', '12 9 0', metal_col, 0.90, 0);

	// Bottom micro-HDMI / USB-C ports
	drawfill ((px + 16) * '1 0 0' + (py + ph - 4) * '0 1 0', '9 5 0', metal_col, 0.90, 0);
	drawfill ((px + 32) * '1 0 0' + (py + ph - 4) * '0 1 0', '8 5 0', metal_col, 0.90, 0);

	// PWR (red) and blinking ACT (green) status LEDs
	act_on = (RH_Sin (time * 24) > -0.1);
	drawfill ((px + 4) * '1 0 0' + (py + floor (ph * 0.56)) * '0 1 0', '2.5 2.5 0', col_red, 0.98, 0);
	if (act_on && mode != 3)
		drawfill ((px + 4) * '1 0 0' + (py + floor (ph * 0.68)) * '0 1 0', '2.5 2.5 0', col_green, 0.98, 0);

	// Label right below the Raspberry Pi board
	temp_c = 64 + floor (3 + 3 * RH_Sin (time * 1.7));
	RH_ShadowStrRight (w - 8, py + ph + 3, strcat ("RPi 4B  |  ", ftos (temp_c), "C  GPIO:ON"), sv, col_green, 0.96);
	bm_topright_y = py + ph + sz + 6;
};

// Bottom-center hacker computer download / upload & packet telemetry strip
void(float w, float h, float mode, float n_en, vector col_red, vector col_cyan, vector col_white, vector col_green, vector col_amber) RH_DrawHackerTransfers =
{
	local float sz, lh, pw, ph, x0, y0, bar_w, dl_u, ul_u, dl_idx, ul_idx, dl_pct, ul_pct, pkts;
	local vector sv;
	local string dl_name, ul_name, dl_spd, ul_spd;

	if (mode == 3)
		return;

	sz = (rh_term_font > 0) ? 6.6 : 4.8;
	sv = sz * '1 1 0';
	lh = sz + 1.5;
	pw = bound (220, floor (w * 0.42), 360);
	ph = lh * 3 + 15;
	x0 = floor (w * 0.5 - pw * 0.5);
	y0 = h - ph - 6;
	bar_w = pw - 12;

	RH_WindowBox (x0, y0, pw, ph, '0 0 0', 0.68, col_cyan, 0.72, col_green);

	// Downloading cycle (0..100% every 3.4s)
	dl_u = (time / 3.4) - floor (time / 3.4);
	dl_idx = floor (time / 3.4);
	dl_idx = dl_idx - 5 * floor (dl_idx / 5);
	if (dl_idx == 0)      dl_name = "quakeahh.exe";
	else if (dl_idx == 1) dl_name = "WallHacks_v4.bin";
	else if (dl_idx == 2) dl_name = "pvs_bypass.ko";
	else if (dl_idx == 3) dl_name = "enemy_coords.db";
	else                  dl_name = "rob_aimbot.tar.gz";
	dl_pct = floor (dl_u * 100);
	dl_spd = strcat (ftos (3 + floor (dl_u * 5)), ".", ftos (floor ((dl_u * 9) - 10 * floor ((dl_u * 9) / 10))), " MB/s");

	RH_ShadowStr ((x0 + 6) * '1 0 0' + (y0 + 3) * '0 1 0', strcat ("DOWNLOADING: ", dl_name), sv, col_cyan, 1.0, 0);
	RH_ShadowStrRight (x0 + pw - 6, y0 + 3, strcat (ftos (dl_pct), "%  ", dl_spd), sv, col_green, 1.0);
	drawfill ((x0 + 6) * '1 0 0' + (y0 + lh + 3) * '0 1 0', bar_w * '1 0 0' + '0 3 0', '0.08 0.14 0.18', 0.80, 0);
	drawfill ((x0 + 6) * '1 0 0' + (y0 + lh + 3) * '0 1 0', max (2, floor (bar_w * dl_u)) * '1 0 0' + '0 3 0', col_cyan, 0.96, 0);

	// Uploading cycle (0..100% every 2.8s)
	ul_u = ((time + 1.1) / 2.8) - floor ((time + 1.1) / 2.8);
	ul_idx = floor ((time + 1.1) / 2.8);
	ul_idx = ul_idx - 4 * floor (ul_idx / 4);
	if (ul_idx == 0)      ul_name = "player_ips.json";
	else if (ul_idx == 1) ul_name = "camper_locs.csv";
	else if (ul_idx == 2) ul_name = "xray_stream.pcap";
	else                  ul_name = "bako_lan_dump.sql";
	ul_pct = floor (ul_u * 100);
	ul_spd = strcat (ftos (1 + floor (ul_u * 3)), ".", ftos (floor ((ul_u * 7) - 10 * floor ((ul_u * 7) / 10))), " MB/s");

	RH_ShadowStr ((x0 + 6) * '1 0 0' + (y0 + lh + 8) * '0 1 0', strcat ("UPLOADING:   ", ul_name), sv, col_amber, 1.0, 0);
	RH_ShadowStrRight (x0 + pw - 6, y0 + lh + 8, strcat (ftos (ul_pct), "%  ", ul_spd), sv, col_white, 1.0);
	drawfill ((x0 + 6) * '1 0 0' + (y0 + lh * 2 + 8) * '0 1 0', bar_w * '1 0 0' + '0 3 0', '0.16 0.10 0.06', 0.80, 0);
	drawfill ((x0 + 6) * '1 0 0' + (y0 + lh * 2 + 8) * '0 1 0', max (2, floor (bar_w * ul_u)) * '1 0 0' + '0 3 0', col_amber, 0.96, 0);

	// Bottom hacker network footer
	pkts = 1240 + floor (420 * (0.5 + 0.5 * RH_Sin (time * 9.3)));
	RH_ShadowStr ((x0 + 6) * '1 0 0' + (y0 + lh * 2 + 13) * '0 1 0', strcat ("PKT: ", ftos (pkts), "/s  |  AES-256  |  ", ftos (n_en), " TARGETS SYNCED"), sv * 0.90, col_green, 0.95, 0);
};

void(float w, float h) RH_DrawXRayHUD =
{
	local float mode, timer10, spd, armed, seq, age, sz, lh, top_h, bot_h, old_font;
	local float pulse, sy, n_en, dist, rad, dfade, locked;
	local float cx, cy, r0, arm, off1_d, off2_d, off3_d, near1_d, near2_d, near3_d;
	local float spin_k;
	local vector col_red, col_cyan, col_white, col_green, col_amber, col_ally, sv;
	local vector cam_org, cam_ang, sp, sp_top, sp_bot;
	local entity t, off1, off2, off3, near1, near2, near3;
	local string s, tname;

	if (!rh_font_checked)
	{
		rh_font_checked = TRUE;
		rh_term_font = loadfont ("user1", "engine/fonts/Roboto-Medium.ttf", "8 12 16 24");
		if (rh_term_font <= 0)
			rh_term_font = findfont ("Roboto");
		if (rh_term_font < 0)
			rh_term_font = 0;
	}

	if (vid_conwidth > 0)
		w = vid_conwidth;
	else
		w = cvar ("vid_conwidth");
	if (vid_conheight > 0)
		h = vid_conheight;
	else
		h = cvar ("vid_conheight");
	if (w <= 0 || h <= 0)
		return;

	mode = getstati (BMST_FD_MODE);
	if (mode <= 0)
	{
		rh_prev_mode = 0;
		return;
	}
	if (rh_prev_mode == 0 && (mode == 1 || mode == 2))
	{
		rh_launch_t = time;
		rh_active_seq = getstati (BMST_FD_SEQ);
	}
	rh_prev_mode = mode;

	seq = getstati (BMST_FD_SEQ);
	if (seq < 1 || seq > 14)
	{
		if (rh_active_seq >= 1 && rh_active_seq <= 14)
			seq = rh_active_seq;
		else
			seq = 1;
	}
	timer10 = getstati (BMST_FD_TIMER);
	spd = getstati (BMST_FD_SPEED);
	armed = getstati (BMST_FD_ARM);
	age = time - rh_launch_t;

	col_red   = '1.00 0.42 0.40';
	col_cyan  = '0.32 0.96 1.00';
	col_white = '1.00 1.00 1.00';
	col_green = '0.40 1.00 0.62';
	col_amber = '1.00 0.84 0.36';
	col_ally  = '0.36 1.00 0.56';

	old_font = drawfont;
	if (rh_term_font > 0)
		drawfont = rh_term_font;
	bm_ui_skip_scale = TRUE;

	pulse = RH_Sin (time * 7);
	sz = (rh_term_font > 0) ? 7.2 : 5;
	sv = sz * '1 1 0';
	lh = (rh_term_font > 0) ? 9.0 : 8;
	top_h = 16;
	bot_h = 16;
	cx = w * 0.5;
	cy = h * 0.5;

	// Subtle perimeter scan ticks & top-center scanner status line (never blocks center viewport)
	if (mode == 1 || mode == 2)
	{
		sy = (time * 0.52 - floor (time * 0.52)) * h;
		drawfill (sy * '0 1 0', '7 1 0', col_cyan, 0.45, 0);
		drawfill ((w - 7) * '1 0 0' + sy * '0 1 0', '7 1 0', col_cyan, 0.45, 0);
		drawfill ((w - 3) * '1 0 0' + (h - sy) * '0 1 0', '3 1 0', col_red, 0.40, 0);

		if (age < 1.60)
			BM_Centered (cx, 6, "^xF66[ ^3KALI-RHEL9 ^xF66] ^5EXECUTING QUAKE WALLHACKS...", sz, col_white, 0.94 + 0.06 * pulse);
		else
			BM_Centered (cx, 6, "^5[ X-RAY SCANNER ACTIVE ] ^2PVS BYPASS: ON", sz, col_white, 0.90);

		// Sleek 1px animated scanning bar directly under top-center status
		local float bar_w, bar_x;
		bar_w = 110;
		bar_x = cx - bar_w * 0.5;
		drawfill (bar_x * '1 0 0' + '0 13 0', bar_w * '1 0 0' + '0 1 0', col_cyan, 0.22, 0);
		drawfill ((bar_x + (0.5 + 0.5 * RH_Sin (time * 4.5)) * (bar_w - 24)) * '1 0 0' + '0 13 0', '24 1 0', (mode == 2) ? col_red : col_cyan, 0.85, 0);
	}

	cam_org = getpropertyvec (VF_ORIGIN);
	cam_ang = getpropertyvec (VF_ANGLES);
	makevectors (cam_ang);

	// 1. 3D-projected enemy scan brackets, moving scanlines, target lock & nearest-3 tracking for terminal/edges
	n_en = 0;
	off1 = world; off2 = world; off3 = world;
	off1_d = 99999; off2_d = 99999; off3_d = 99999;
	near1 = world; near2 = world; near3 = world;
	near1_d = 99999; near2_d = 99999; near3_d = 99999;

	t = rh_xray_head;
	while (t)
	{
		if (time - t.rh_last_t <= 0.6)
		{
			dist = vlen (t.origin - cam_org);
			if (t.rh_flags & 2)
			{
				if (mode != 3 && dist <= 1800)
				{
					sp = cs_project (t.origin + '0 0 28');
					if (sp_z > 0 && sp_x > 16 && sp_x < w - 16 && sp_y > top_h + 8 && sp_y < h - bot_h - 8)
					{
						tname = t.netname;
						if (tname == "")
							tname = "ALLY";
						BM_ShadowCentered (sp_x, sp_y - 8, strcat ("[ALLY] ", tname), sz, col_ally, 0.70);
					}
				}
			}
			else
			{
				n_en = n_en + 1;
				if (dist < near1_d)
				{
					near3 = near2; near3_d = near2_d;
					near2 = near1; near2_d = near1_d;
					near1 = t;     near1_d = dist;
				}
				else if (dist < near2_d)
				{
					near3 = near2; near3_d = near2_d;
					near2 = t;     near2_d = dist;
				}
				else if (dist < near3_d)
				{
					near3 = t;     near3_d = dist;
				}

				if (mode != 3)
				{
					sp = cs_project (t.origin + '0 0 24');
					if (sp_z > 0 && sp_x >= 16 && sp_x <= w - 16 && sp_y >= top_h + 10 && sp_y <= h - bot_h - 10)
					{
						if (dist <= 3200)
						{
							dfade = 1 - bound (0, (dist - 1500) / 1700, 0.55);
							sp_top = cs_project (t.origin + '0 0 48');
							sp_bot = cs_project (t.origin - '0 0 18');
							rad = bound (8, fabs (sp_bot_y - sp_top_y) * 0.45, 26);
							locked = (fabs (sp_x - cx) < 34 && fabs (sp_y - cy) < 34);
							RH_DrawTargetBracket (sp_x, sp_y, rad, 0.72 * dfade, (dist < 460 || locked) ? col_red : col_cyan, locked);

							if (dist <= 2200)
							{
								tname = t.netname;
								if (tname == "")
									tname = "HOSTILE";
								if (strlen (tname) > 12)
									tname = substring (tname, 0, 12);
								if (dist <= 1300)
									s = strcat (tname, " [", ftos (t.rh_hp), "]");
								else
									s = tname;
								BM_ShadowCentered (sp_x, sp_y - rad - 8, s, sz, locked ? col_red : col_white, 0.86 * dfade);
								BM_ShadowCentered (sp_x, sp_y + rad + 2, locked ? ">> LOCKED <<" : strcat (ftos (floor (dist)), "u"), sz * 0.90, locked ? col_red : col_cyan, 0.80 * dfade);
							}
						}
					}
					else if (dist <= 2400)
					{
						if (dist < off1_d)
						{
							off3 = off2; off3_d = off2_d;
							off2 = off1; off2_d = off1_d;
							off1 = t;    off1_d = dist;
						}
						else if (dist < off2_d)
						{
							off3 = off2; off3_d = off2_d;
							off2 = t;    off2_d = dist;
						}
						else if (dist < off3_d)
						{
							off3 = t;    off3_d = dist;
						}
					}
				}
			}
		}
		t = t.rh_next;
	}

	if (mode != 3)
	{
		RH_DrawEdgePip (off1, cam_org, w, h, top_h, bot_h, sz, col_red, col_cyan);
		RH_DrawEdgePip (off2, cam_org, w, h, top_h, bot_h, sz, col_red, col_cyan);
		RH_DrawEdgePip (off3, cam_org, w, h, top_h, bot_h, sz, col_red, col_cyan);
	}

	// 2. Center tactical scanner reticle
	if (mode == 1 || mode == 2)
	{
		r0 = (mode == 2) ? 7 : 6;
		arm = 5;
		drawfill ((cx - r0 - arm) * '1 0 0' + (cy - r0) * '0 1 0', arm * '1 0 0' + '0 1 0', col_cyan, 0.65, 0);
		drawfill ((cx - r0) * '1 0 0' + (cy - r0 - arm) * '0 1 0', '1 0 0' + arm * '0 1 0', col_cyan, 0.65, 0);
		drawfill ((cx + r0) * '1 0 0' + (cy - r0) * '0 1 0', arm * '1 0 0' + '0 1 0', col_cyan, 0.65, 0);
		drawfill ((cx + r0 - 1) * '1 0 0' + (cy - r0 - arm) * '0 1 0', '1 0 0' + arm * '0 1 0', col_cyan, 0.65, 0);
		drawfill ((cx - r0 - arm) * '1 0 0' + (cy + r0 - 1) * '0 1 0', arm * '1 0 0' + '0 1 0', col_cyan, 0.65, 0);
		drawfill ((cx - r0) * '1 0 0' + (cy + r0) * '0 1 0', '1 0 0' + arm * '0 1 0', col_cyan, 0.65, 0);
		drawfill ((cx + r0) * '1 0 0' + (cy + r0 - 1) * '0 1 0', arm * '1 0 0' + '0 1 0', col_cyan, 0.65, 0);
		drawfill ((cx + r0 - 1) * '1 0 0' + (cy + r0) * '0 1 0', '1 0 0' + arm * '0 1 0', col_cyan, 0.65, 0);
		drawfill ((cx - 1) * '1 0 0' + (cy - 1) * '0 1 0', '2 2 0', col_red, 0.85, 0);
		spin_k = time * 48;
		RH_Circle (cx, cy, 15, 8, spin_k, 0.9, (mode == 2) ? col_red : col_cyan, 0.24);
	}

	// 3. Top-left Kali / Red Hat Linux hacker terminal (opens with Red Hat neofetch ASCII art, then executes wallhack commands)
	RH_DrawTerminal (w, h, seq, age, mode, n_en, pulse, cam_org, near1, near2, near3, col_red, col_cyan, col_white, col_green, col_amber);

	// 4. Top-right tactical minimap radar & telemetry + Raspberry Pi chip
	RH_DrawMiniMap (w, h, mode, timer10, spd, armed, n_en, pulse, cam_org, col_red, col_cyan, col_white, col_green, col_ally);
	RH_DrawRaspberryPi (w, h, mode, col_red, col_cyan, col_white, col_green, col_amber);

	// 5. Bottom-center hacker download/upload & network telemetry
	RH_DrawHackerTransfers (w, h, mode, n_en, col_red, col_cyan, col_white, col_green, col_amber);

	// 6. Bottom-right controls
	BM_ShadowColorRight (w - 8, BM_CornerBottomY (h) - lh - 7, "^5[MOUSE]^7 Steer   ^xF66[LMB]^7 Dash / Detonate", sz, 1.0);
	BM_ShadowColorRight (w - 8, BM_CornerBottomY (h) - 7, "^3[H]^7 Recall", sz, 1.0);

	bm_ui_skip_scale = FALSE;
	drawfont = old_font;

	// 7. Centerprint toast (bottom-left) + post-blast SIGNAL LOST line stacked above it
	BM_DrawCenterPrint (w, h);
	if (mode == 3)
		BM_DrawColorShadow (JP_IsVisible () ? 36 : 10, bm_cp_top_y - 9, "^1// SIGNAL LOST :: DETONATED //", 6, 0.86 + 0.12 * pulse);
};

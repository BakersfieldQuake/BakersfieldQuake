/*
================
robhead_xray.qc — Kali / Red Hat Linux Hacker Terminal + X-Ray Scanner HUD for Rob Head Drone
Called from CSQC_UpdateView when BMST_FD_MODE (stat 81) > 0.
Receives live map-wide enemy targets from SSQC via ENT_RD_TARGET (SendEntity).
Playtest 1.76 cleanup: bright through-wall silhouettes, small labels and reticle, a terminal that types a few
commands and closes, pulsing radar contacts, a pictured Raspberry Pi board and a bottom-left transfer readout.
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
.entity	rh_sil2;						// glow shell drawn around rh_sil
.float	rh_occl;						// set each frame by RH_AddXRayEntities: hidden behind a wall
.float	rh_phase;						// radar pulse phase
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
float	rh_rpi_ok;						// 1 = gfx/rh_rpi.png loaded, -1 = missing

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
	if (self.rh_sil2)
	{
		if (self.rh_sil2.rh_mdlname != "")
		{
			strunzone (self.rh_sil2.rh_mdlname);
			self.rh_sil2.rh_mdlname = "";
		}
		remove (self.rh_sil2);
		self.rh_sil2 = world;
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

// Through-wall "chams": every hidden enemy is drawn as a bright, solid, no-depth-test silhouette plus a soft glow
// shell, so you see people through walls at a glance. Visible enemies get nothing extra here (playtest 1.76: the old
// sweep-modulated alpha topped out at ~0.6 and was hard to see).
void(entity s, entity t, float sc, vector col, float a, float fx) RH_SetupSil =
{
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
	s.scale = ((t.rh_scale > 0) ? t.rh_scale : 1) * sc;
	setorigin (s, t.origin);
	s.effects = fx;
	s.colormod = col;
	s.alpha = a;
	addentity (s);
};

void() RH_AddXRayEntities =
{
	local entity t;
	local vector cam_org, col;
	local float dist, a, pul;

	cam_org = getpropertyvec (VF_ORIGIN);
	pul = 0.5 + 0.5 * RH_Sin (time * 6);

	t = rh_xray_head;
	while (t)
	{
		t.rh_occl = FALSE;
		if (time - t.rh_last_t <= 0.6 && !(t.rh_flags & 2) && t.rh_mdlname != "")
		{
			dist = vlen (t.origin - cam_org);
			if (dist <= 3600)
			{
				// Only hidden targets: a target in plain sight needs no glow over it
				traceline (cam_org, t.origin + '0 0 24', TRUE, world);
				if (trace_fraction < 0.995)
				{
					t.rh_occl = TRUE;
					a = 1 - bound (0, (dist - 2200) / 1400, 0.45);
					if (dist < 460)
						col = '3.2 0.45 0.35';		// close: hot red
					else
						col = '0.55 2.8 3.2';		// bright cyan
					if (!t.rh_sil)
						t.rh_sil = spawn ();
					if (!t.rh_sil2)
						t.rh_sil2 = spawn ();
					// solid bright body (EF_NODEPTHTEST | EF_FULLBRIGHT) + an additive glow shell around it
					RH_SetupSil (t.rh_sil, t, 1, col, 0.95 * a, 8192 | 512);
					RH_SetupSil (t.rh_sil2, t, 1.14, col * 0.7, (0.30 + 0.25 * pul) * a, 8192 | 512 | 32);
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

// Shortens s with ".." until it fits maxw at text size sv (the terminal text used to run off the window)
string(string s, float maxw, vector sv) RH_Fit =
{
	local float wd, n;

	wd = stringwidth (s, FALSE, sv);
	if (wd <= maxw)
		return s;
	n = floor (strlen (s) * maxw / wd);
	while (n > 1 && stringwidth (strcat (substring (s, 0, n), ".."), FALSE, sv) > maxw)
		n = n - 1;
	return strcat (substring (s, 0, max (1, n)), "..");
};

// Thin corner brackets around a target in plain sight
void(float cx, float cy, float rad, float a, vector col) RH_DrawTargetBracket =
{
	local float arm;
	local vector hx, vy;

	arm = bound (2, floor (rad * 0.35), 5);
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
};

// Small marker on the screen edge pointing at an off-screen enemy (no text): a dot with a short tip toward it.
// drawfill, not drawline: Zircon's drawline dropped these short diagonal strokes.
void(entity t, vector cam_org, float w, float h, vector col) RH_DrawEdgePip =
{
	local vector delta;
	local float dist, dirx, diry, dlen, px, py, a, pul;

	if (!t)
		return;
	delta = (t.origin + '0 0 24') - cam_org;
	dist = vlen (delta);
	a = 0.80 * (1 - bound (0, (dist - 900) / 1600, 0.5));
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
	px = bound (12, w * 0.5 + dirx * (w * 0.5 - 14), w - 12);
	py = bound (24, h * 0.5 + diry * (h * 0.5 - 26), h - 24);
	pul = 0.75 + 0.25 * RH_Sin (time * 8);
	drawfill ((px - 2) * '1 0 0' + (py - 2) * '0 1 0', '4 4 0', col, a * pul, 0);
	drawfill ((px + dirx * 3.5 - 1) * '1 0 0' + (py + diry * 3.5 - 1) * '0 1 0', '2 2 0', col, a, 0);
	drawfill ((px + dirx * 6 - 0.75) * '1 0 0' + (py + diry * 6 - 0.75) * '0 1 0', '1.5 1.5 0', col, a, 0);
};

// Top-left terminal: types a few commands from the launch's sequence, shows the result, then closes on its own
float RH_TERM_HOLD = 1.6;		// seconds the finished terminal stays up
float RH_TERM_FADE = 0.45;

void(float w, float h, float seq, float age, float mode, float n_en, vector col_red, vector col_cyan, vector col_white, vector col_green, vector col_amber) RH_DrawTerminal =
{
	local float tx, ty, tw, th, cur_th, open_u, tfont, tlh, title_h, body_y, maxw, pw, fade;
	local float ch_rate, t_cmd0, t_out0, t_cmd1, t_res, t_end, n0, n1;
	local string c0, c1, s;
	local vector tsv;

	if (mode == 3)
		return;
	ch_rate = 40;
	c0 = RH_SeqLine (seq, 0, n_en);
	c1 = RH_SeqLine (seq, 2, n_en);
	t_cmd0 = 0.20;
	t_out0 = t_cmd0 + strlen (c0) / ch_rate + 0.10;
	t_cmd1 = t_out0 + 0.25;
	t_res = t_cmd1 + strlen (c1) / ch_rate + 0.12;
	t_end = t_res + RH_TERM_HOLD;
	if (age >= t_end + RH_TERM_FADE)
		return;
	fade = 1 - bound (0, (age - t_end) / RH_TERM_FADE, 1);

	tfont = (rh_term_font > 0) ? bound (6, floor (w * 0.0105), 9) : bound (4.5, floor (w * 0.0075), 6);
	tsv = tfont * '1 1 0';
	tlh = tfont + 2;
	tx = 8;
	ty = JBH_TopLeftY ();
	tw = bound (170, floor (w * 0.30), 300);
	title_h = tlh + 3;
	th = title_h + 4 + 4 * tlh + 3;
	maxw = tw - 10;

	open_u = bound (0, age / 0.14, 1);
	cur_th = max (title_h + 2, floor (th * (1 - (1 - open_u) * (1 - open_u))));

	drawsetcliparea (tx, ty, tw, cur_th);
	RH_WindowBox (tx, ty, tw, cur_th, '0 0 0', 0.55 * fade, '0.92 0.24 0.28', 0.85 * fade, col_cyan);
	drawfill ((tx + 4) * '1 0 0' + (ty + floor (title_h * 0.5) - 1) * '0 1 0', '3 3 0', col_red, fade, 0);
	drawfill ((tx + 9) * '1 0 0' + (ty + floor (title_h * 0.5) - 1) * '0 1 0', '3 3 0', col_amber, fade, 0);
	drawfill ((tx + 14) * '1 0 0' + (ty + floor (title_h * 0.5) - 1) * '0 1 0', '3 3 0', col_green, fade, 0);
	RH_ShadowStr ((tx + 21) * '1 0 0' + (ty + 2) * '0 1 0', RH_Fit ("root@kali-rhel9: ~/wallhack", tw - 26, tsv), tsv, col_white, fade, 0);
	drawfill ((tx + 1) * '1 0 0' + (ty + title_h) * '0 1 0', (tw - 2) * '1 0 0' + '0 1 0', '0.92 0.24 0.28', 0.6 * fade, 0);

	if (open_u >= 0.85)
	{
		body_y = ty + title_h + 4;
		pw = stringwidth ("kali# ", FALSE, tsv);
		if (age >= t_cmd0)
		{
			n0 = min (strlen (c0), floor ((age - t_cmd0) * ch_rate));
			s = substring (c0, 0, n0);
			if (age < t_out0)
				s = strcat (s, "_");
			RH_ShadowStr ((tx + 5) * '1 0 0' + body_y * '0 1 0', "kali# ", tsv, col_red, fade, 0);
			RH_ShadowStr ((tx + 5 + pw) * '1 0 0' + body_y * '0 1 0', RH_Fit (s, maxw - pw, tsv), tsv, col_green, fade, 0);
		}
		if (age >= t_out0)
			RH_ShadowStr ((tx + 5) * '1 0 0' + (body_y + tlh) * '0 1 0', RH_Fit (RH_SeqLine (seq, 1, n_en), maxw, tsv), tsv, col_cyan, fade, 0);
		if (age >= t_cmd1)
		{
			n1 = min (strlen (c1), floor ((age - t_cmd1) * ch_rate));
			s = substring (c1, 0, n1);
			if (age < t_res)
				s = strcat (s, "_");
			RH_ShadowStr ((tx + 5) * '1 0 0' + (body_y + 2 * tlh) * '0 1 0', "kali# ", tsv, col_red, fade, 0);
			RH_ShadowStr ((tx + 5 + pw) * '1 0 0' + (body_y + 2 * tlh) * '0 1 0', RH_Fit (s, maxw - pw, tsv), tsv, col_white, fade, 0);
		}
		if (age >= t_res)
			RH_ShadowStr ((tx + 5) * '1 0 0' + (body_y + 3 * tlh) * '0 1 0', RH_Fit (RH_SeqLine (seq, 5, n_en), maxw, tsv), tsv, col_green, fade, 0);
	}
	drawresetcliparea ();
};

// Top-right X-ray radar: every contact pulses on its own (playtest 1.76), not only when the sweep passes it
void(float w, float h, float mode, float timer10, float spd, float armed, float n_en, float pulse, vector cam_org, vector col_red, vector col_cyan, vector col_white, vector col_green, vector col_ally) RH_DrawMiniMap =
{
	local float sz, lh, rrad, box_w, box_h, bx0, by0, rcx, rcy;
	local float sw_ang, i, ta, tx, ty, rf, rr, px, py, ph, close, ft_y;
	local vector sv, delta, bcol;
	local entity t;
	local string s;

	sz = (rh_term_font > 0) ? bound (6, floor (w * 0.0100), 9) : bound (4.5, floor (w * 0.0075), 6);
	sv = sz * '1 1 0';
	lh = sz + 1.5;

	rrad = bound (34, floor (h * 0.125), 60);
	box_w = rrad * 2 + 10;
	box_h = rrad * 2 + lh + 10;
	bx0 = w - 8 - box_w;
	by0 = 8;

	RH_WindowBox (bx0, by0, box_w, box_h, '0.02 0.04 0.06', 0.22, col_cyan, 0.6, (mode == 2 || mode == 3) ? col_red : col_cyan);
	RH_ShadowStr ((bx0 + 4) * '1 0 0' + (by0 + 2) * '0 1 0', "X-RAY", sv, col_cyan, 1.0, 0);
	RH_ShadowStrRight (bx0 + box_w - 4, by0 + 2, ftos (n_en), sv, (n_en > 0) ? col_red : col_green, 1.0);

	rcx = bx0 + box_w * 0.5;
	rcy = by0 + lh + 5 + rrad;

	RH_Circle (rcx, rcy, rrad, 24, 0, 1.0, col_cyan, 0.55);
	RH_Circle (rcx, rcy, rrad * 0.5, 16, 0, 1.0, col_cyan, 0.22);
	i = 0;
	while (i < 4)
	{
		ta = (i * 90) * RH_DEG2RAD;
		tx = RH_Cos (ta);
		ty = RH_Sin (ta);
		RH_Line (1.0, (rcx + tx * (rrad - 3)) * '1 0 0' + (rcy + ty * (rrad - 3)) * '0 1 0', (rcx + tx * rrad) * '1 0 0' + (rcy + ty * rrad) * '0 1 0', col_cyan, 0.5);
		i = i + 1;
	}
	sw_ang = (time * 165) * RH_DEG2RAD;
	RH_Line (1.2, rcx * '1 0 0' + rcy * '0 1 0', (rcx + RH_Cos (sw_ang) * rrad) * '1 0 0' + (rcy + RH_Sin (sw_ang) * rrad) * '0 1 0', col_cyan, 0.55);
	drawfill ((rcx - 1.5) * '1 0 0' + (rcy - 1.5) * '0 1 0', '3 3 0', col_white, 0.98, 0);
	drawfill ((rcx - 0.5) * '1 0 0' + (rcy - rrad - 2) * '0 1 0', '1.5 3 0', col_white, 0.85, 0);

	// Contacts: a bright dot plus an expanding ring, each on its own phase; faster and red when close
	t = rh_xray_head;
	while (t)
	{
		if (time - t.rh_last_t <= 0.6)
		{
			if (!t.rh_phase)
				t.rh_phase = 0.05 + random () * 0.9;
			delta = t.origin - cam_org;
			delta_z = 0;
			rf = delta * v_forward;
			rr = delta * v_right;
			px = rcx + bound (-1, rr / 2600, 1) * (rrad - 3);
			py = rcy - bound (-1, rf / 2600, 1) * (rrad - 3);
			close = (vlen (delta) < 700);
			ph = time * (close ? 2.4 : 1.4) + t.rh_phase;
			ph = ph - floor (ph);
			if (t.rh_flags & 2)
				bcol = col_ally;
			else if (close)
				bcol = '1 0.25 0.22';
			else
				bcol = '1 0.55 0.30';
			RH_Circle (px, py, 2 + ph * 6, 8, 0, 1.0, bcol, 0.85 * (1 - ph));
			drawfill ((px - 1.5) * '1 0 0' + (py - 1.5) * '0 1 0', '3 3 0', bcol, 0.65 + 0.35 * (1 - ph), 0);
		}
		t = t.rh_next;
	}

	ft_y = by0 + box_h + 3;
	if (mode == 2)
		RH_ShadowStrRight (w - 8, ft_y, "DASHING", sv, col_red, 0.82 + 0.18 * pulse);
	else if (mode == 3)
		RH_ShadowStrRight (w - 8, ft_y, "SIGNAL LOST", sv, col_red, 0.94);
	else
		RH_ShadowStrRight (w - 8, ft_y, armed ? "CRUISE  ARMED" : "CRUISE  BOOT", sv, col_cyan, 0.92);
	if (timer10 == 999)
		s = strcat (ftos (spd), " u/s");
	else
		s = strcat (ftos (spd), " u/s  FUEL ", ftos (floor (timer10 / 10)), ".", ftos (timer10 - 10 * floor (timer10 / 10)), "s");
	RH_ShadowStrRight (w - 8, ft_y + lh, s, sv, (timer10 < 40 && timer10 != 999) ? col_red : col_white, 0.88);
	bm_topright_y = ft_y + 2 * lh;
};

// Raspberry Pi 4B board under the radar: one detailed picture (gfx/rh_rpi.png from zz_robdrone.pk3) instead of ~50
// fills, with the PWR / ACT LEDs drawn live on top
float RH_RPI_W = 320;
float RH_RPI_H = 212;
void(float w, float h, float mode, vector col_red, vector col_green) RH_DrawRaspberryPi =
{
	local float rrad, box_w, px, py, pw, ph, sx;

	if (rh_rpi_ok == 0)
		rh_rpi_ok = (drawgetimagesize ("gfx/rh_rpi.png") != '0 0 0') ? 1 : -1;
	if (rh_rpi_ok < 0)
		return;
	rrad = bound (34, floor (h * 0.125), 60);
	box_w = rrad * 2 + 10;
	pw = box_w;
	ph = floor (pw * RH_RPI_H / RH_RPI_W);
	px = w - 8 - box_w;
	py = bm_topright_y + 4;
	sx = pw / RH_RPI_W;

	drawpic (px * '1 0 0' + py * '0 1 0', "gfx/rh_rpi.png", pw * '1 0 0' + ph * '0 1 0', '1 1 1', 0.96, 0);
	// LED pads in the picture sit at (24,150) PWR and (24,168) ACT, 8x8 px
	drawfill ((px + 24 * sx) * '1 0 0' + (py + 150 * sx) * '0 1 0', (8 * sx) * '1 1 0', col_red, 0.95, 0);
	if (mode != 3 && RH_Sin (time * 24 + RH_Sin (time * 5) * 3) > -0.2)
		drawfill ((px + 24 * sx) * '1 0 0' + (py + 168 * sx) * '0 1 0', (8 * sx) * '1 1 0', col_green, 0.98, 0);
	bm_topright_y = py + ph + 3;
};

// Bottom-left download / upload readout: random file, size, speed and timing each cycle, no box behind it
float rh_dl_t0, rh_dl_dur, rh_dl_name, rh_dl_mb, rh_dl_gap;
float rh_ul_t0, rh_ul_dur, rh_ul_name, rh_ul_mb, rh_ul_gap;

string(float i) RH_DlName =
{
	if (i == 0) return "quakeahh.exe";
	if (i == 1) return "WallHacks_v4.bin";
	if (i == 2) return "pvs_bypass.ko";
	if (i == 3) return "enemy_coords.db";
	if (i == 4) return "rob_aimbot.tar.gz";
	if (i == 5) return "dm6_spawns.zip";
	if (i == 6) return "zircon_god.dll";
	if (i == 7) return "bako_maps.pk3";
	return "rocket_jumps.dem";
};

string(float i) RH_UlName =
{
	if (i == 0) return "player_ips.json";
	if (i == 1) return "camper_locs.csv";
	if (i == 2) return "xray_stream.pcap";
	if (i == 3) return "bako_lan_dump.sql";
	if (i == 4) return "kill_cam.mp4";
	if (i == 5) return "frag_log.txt";
	return "rob_selfie.png";
};

void(float y, string verb, string nm, float u, float mb, vector col, float sz, float x0, float bar_w) RH_DrawTransferRow =
{
	local vector sv;
	local string s;

	sv = sz * '1 1 0';
	if (u >= 1)
		s = strcat (verb, " ", nm, "  DONE");
	else
	{
		s = strcat (verb, " ", nm, "  ", ftos (floor (u * 100)), "%  ");
		s = strcat (s, ftos (floor (mb)), ".", ftos (floor (mb * 10) - 10 * floor (mb)), " MB/s");
	}
	RH_ShadowStr (x0 * '1 0 0' + y * '0 1 0', RH_Fit (s, bar_w, sv), sv, col, 0.95, 0);
	drawfill (x0 * '1 0 0' + (y + sz + 1) * '0 1 0', bar_w * '1 0 0' + '0 2 0', '0 0 0', 0.45, 0);
	drawfill (x0 * '1 0 0' + (y + sz + 1) * '0 1 0', max (1, floor (bar_w * min (u, 1))) * '1 0 0' + '0 2 0', col, 0.95, 0);
};

void(float w, float h, float mode, float bottom_y, vector col_cyan, vector col_amber) RH_DrawHackerTransfers =
{
	local float sz, x0, y0, bar_w, dl_u, ul_u;

	if (mode == 3)
		return;
	if (rh_dl_dur <= 0 || time > rh_dl_t0 + rh_dl_dur + rh_dl_gap || time < rh_dl_t0)
	{
		rh_dl_t0 = time;
		rh_dl_dur = 1.4 + random () * 3.2;
		rh_dl_gap = 0.25 + random () * 0.9;
		rh_dl_name = floor (random () * 8.999);
		rh_dl_mb = 2 + random () * 14;
	}
	if (rh_ul_dur <= 0 || time > rh_ul_t0 + rh_ul_dur + rh_ul_gap || time < rh_ul_t0)
	{
		rh_ul_t0 = time;
		rh_ul_dur = 1.2 + random () * 2.8;
		rh_ul_gap = 0.25 + random () * 1.1;
		rh_ul_name = floor (random () * 6.999);
		rh_ul_mb = 0.4 + random () * 4;
	}
	dl_u = (time - rh_dl_t0) / rh_dl_dur;
	ul_u = (time - rh_ul_t0) / rh_ul_dur;

	sz = (rh_term_font > 0) ? bound (6, floor (w * 0.0098), 9) : bound (4.5, floor (w * 0.0075), 6);
	bar_w = bound (130, floor (w * 0.24), 230);
	x0 = JP_IsVisible () ? 36 : 10;
	y0 = bottom_y - 2 * (sz + 6);
	RH_DrawTransferRow (y0, "DL", RH_DlName (rh_dl_name), dl_u, rh_dl_mb * (0.8 + 0.2 * RH_Sin (time * 7)), col_cyan, sz, x0, bar_w);
	RH_DrawTransferRow (y0 + sz + 6, "UL", RH_UlName (rh_ul_name), ul_u, rh_ul_mb * (0.8 + 0.2 * RH_Sin (time * 5 + 1)), col_amber, sz, x0, bar_w);
};

void(float w, float h) RH_DrawXRayHUD =
{
	local float mode, timer10, spd, armed, seq, age, sz, lh, old_font;
	local float pulse, n_en, dist, rad, dfade, locked;
	local float cx, cy, off1_d, off2_d;
	local vector col_red, col_cyan, col_white, col_green, col_amber, col_ally;
	local vector cam_org, cam_ang, sp, sp_top, sp_bot, tcol;
	local entity t, off1, off2;
	local string tname;

	if (!rh_font_checked)
	{
		rh_font_checked = TRUE;
		// Same slot and size list as BM_GetUIFont (csqc.sbardefs.qc), so the two calls don't fight over "user1"
		rh_term_font = loadfont ("user1", "engine/fonts/Roboto-Medium.ttf", "8 12 16 24 32");
		if (rh_term_font <= 0)
			rh_term_font = findfont ("Roboto");
		if (rh_term_font < 0)
			rh_term_font = 0;
		// loadfont hands out the slot even when the .ttf is missing (Linux/macOS packages): then the wide Quake
		// font is drawn at the Roboto sizes and runs off the panels. Keep the slot only if it is proportional.
		if (rh_term_font > 0)
		{
			old_font = drawfont;
			drawfont = rh_term_font;
			if (stringwidth ("iiiiiiiiii", FALSE, '10 10 0') >= 80)
				rh_term_font = 0;
			drawfont = old_font;
		}
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
		rh_dl_dur = 0;
		rh_ul_dur = 0;
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
	// Labels over targets: small (playtest 1.76 found LOCKED / names far too big)
	sz = (rh_term_font > 0) ? 5.5 : 4.5;
	lh = (rh_term_font > 0) ? 8.0 : 7;
	cx = w * 0.5;
	cy = h * 0.5;

	cam_org = getpropertyvec (VF_ORIGIN);
	cam_ang = getpropertyvec (VF_ANGLES);
	makevectors (cam_ang);

	// 1. Target labels. Hidden enemies already glow through the wall (RH_AddXRayEntities), so they only get a small
	//    name tag; enemies in plain sight get thin brackets. Off-screen ones: up to 2 edge arrows.
	n_en = 0;
	off1 = world; off2 = world;
	off1_d = 99999; off2_d = 99999;

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
					sp = cs_project (t.origin + '0 0 34');
					if (sp_z > 0 && sp_x > 16 && sp_x < w - 16 && sp_y > 16 && sp_y < h - 16)
					{
						tname = t.netname;
						if (tname == "")
							tname = "ALLY";
						BM_ShadowCentered (sp_x, sp_y - 6, tname, sz, col_ally, 0.70);
					}
				}
			}
			else
			{
				n_en = n_en + 1;
				if (mode != 3)
				{
					sp = cs_project (t.origin + '0 0 24');
					if (sp_z > 0 && sp_x >= 12 && sp_x <= w - 12 && sp_y >= 12 && sp_y <= h - 12)
					{
						if (dist <= 3200)
						{
							dfade = 1 - bound (0, (dist - 1500) / 1700, 0.55);
							sp_top = cs_project (t.origin + '0 0 40');
							sp_bot = cs_project (t.origin - '0 0 22');
							rad = bound (6, fabs (sp_bot_y - sp_top_y) * 0.5, 22);
							locked = (fabs (sp_x - cx) < 26 && fabs (sp_y - cy) < 26);
							tcol = (dist < 460 || locked) ? col_red : col_cyan;
							if (!t.rh_occl)
								RH_DrawTargetBracket (sp_x, sp_y, rad, 0.75 * dfade, tcol);
							if (dist <= 2200 || locked)
							{
								tname = t.netname;
								if (tname == "")
									tname = "HOSTILE";
								if (strlen (tname) > 14)
									tname = substring (tname, 0, 14);
								BM_ShadowCentered (sp_x, sp_y - rad - sz - 2, tname, sz, locked ? col_red : col_white, 0.85 * dfade);
								if (locked)
									BM_ShadowCentered (sp_x, sp_y + rad + 2, "LOCKED", sz * 0.85, col_red, 0.9);
							}
						}
					}
					else if (dist <= 2400)
					{
						if (dist < off1_d)
						{
							off2 = off1; off2_d = off1_d;
							off1 = t;    off1_d = dist;
						}
						else if (dist < off2_d)
						{
							off2 = t;    off2_d = dist;
						}
					}
				}
			}
		}
		t = t.rh_next;
	}

	if (mode != 3)
	{
		RH_DrawEdgePip (off1, cam_org, w, h, col_red);
		RH_DrawEdgePip (off2, cam_org, w, h, col_red);
	}

	// 2. Small centre reticle: four 2px ticks and a dot (was ~30px with a spinning circle)
	if (mode == 1 || mode == 2)
	{
		tcol = (mode == 2) ? col_red : col_cyan;
		drawfill ((cx - 6) * '1 0 0' + (cy - 0.5) * '0 1 0', '3 1 0', tcol, 0.8, 0);
		drawfill ((cx + 3) * '1 0 0' + (cy - 0.5) * '0 1 0', '3 1 0', tcol, 0.8, 0);
		drawfill ((cx - 0.5) * '1 0 0' + (cy - 6) * '0 1 0', '1 3 0', tcol, 0.8, 0);
		drawfill ((cx - 0.5) * '1 0 0' + (cy + 3) * '0 1 0', '1 3 0', tcol, 0.8, 0);
		drawfill ((cx - 1) * '1 0 0' + (cy - 1) * '0 1 0', '2 2 0', col_red, 0.9, 0);
	}

	// 3. Top-left terminal (a few commands, then it closes)
	RH_DrawTerminal (w, h, seq, age, mode, n_en, col_red, col_cyan, col_white, col_green, col_amber);

	// 4. Top-right radar + telemetry + Raspberry Pi board
	RH_DrawMiniMap (w, h, mode, timer10, spd, armed, n_en, pulse, cam_org, col_red, col_cyan, col_white, col_green, col_ally);
	RH_DrawRaspberryPi (w, h, mode, col_red, col_green);

	// 5. Bottom-right controls
	BM_ShadowColorRight (w - 8, BM_CornerBottomY (h) - lh - 7, "^5[MOUSE]^7 Steer   ^xF66[LMB]^7 Dash / Detonate", sz, 1.0);
	BM_ShadowColorRight (w - 8, BM_CornerBottomY (h) - 7, "^3[H]^7 Recall", sz, 1.0);

	bm_ui_skip_scale = FALSE;
	drawfont = old_font;

	// 6. Bottom-left: centerprint toast, then the download/upload readout stacked above it
	BM_DrawCenterPrint (w, h);
	if (mode == 3)
		BM_DrawColorShadow (JP_IsVisible () ? 36 : 10, bm_cp_top_y - 9, "^1// SIGNAL LOST :: DETONATED //", 6, 0.86 + 0.12 * pulse);
	else
	{
		if (rh_term_font > 0)
			drawfont = rh_term_font;
		bm_ui_skip_scale = TRUE;
		RH_DrawHackerTransfers (w, h, mode, bm_cp_top_y - 4, col_cyan, col_amber);
		bm_ui_skip_scale = FALSE;
		drawfont = old_font;
	}
};

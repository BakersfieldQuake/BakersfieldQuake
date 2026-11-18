/*
================
robhead_xray.qc — Red Hat Linux Hacking Terminal + X-Ray Vision HUD for Rob Head Drone
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
entity	rh_snd_ent;
float	rh_prev_mode;
float	rh_launch_t;
float	rh_active_seq;
float	rh_type_last_ch;
float	rh_type_snd_t;
float	rh_type_stage;

float	RH_DEG2RAD			= 0.01745329;

void(vector org, string snd, float vol) RH_PlayKey =
{
	if (!rh_snd_ent)
		rh_snd_ent = spawn ();
	setorigin (rh_snd_ent, org);
	sound (rh_snd_ent, 0, snd, vol, 0);
};

void(vector org, float cur_ch, float stage) RH_TypeTickAudio =
{
	local float k;
	local string s;

	if (cur_ch > rh_type_last_ch && (time - rh_type_snd_t) >= 0.030)
	{
		k = cur_ch - 4 * floor (cur_ch / 4);
		if (k == 0) s = "robhead/key1.wav";
		else if (k == 1) s = "robhead/key2.wav";
		else if (k == 2) s = "robhead/key3.wav";
		else s = "robhead/key4.wav";
		RH_PlayKey (org, s, 0.56);
		rh_type_snd_t = time;
		rh_type_last_ch = cur_ch;
	}
	if (stage > rh_type_stage)
	{
		if (stage == 1 || stage == 2 || stage >= 5)
			RH_PlayKey (org, "robhead/key_enter.wav", 0.65);
		else if (stage == 3 || stage == 4)
			RH_PlayKey (org, "robhead/key_beep.wav", 0.45);
		rh_type_stage = stage;
	}
};

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

	t = rh_xray_head;
	while (t)
	{
		if (time - t.rh_last_t <= 0.6 && !(t.rh_flags & 2) && t.rh_mdlname != "")
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
			s.colormod = '0 2.6 3.0';
			s.alpha = 0.65;
			addentity (s);
		}
		t = t.rh_next;
	}
};

// (RH_Box, the dark filled panel, is gone: the HUD rule allows no dark boxes. Everything below is corner text.)
float() JBH_TopLeftY;		// john_bird_hud.qc: top-left start that clears the con_notify lines

// drop-shadowed plain text in an exact colour (same 0.7 offset / 0.85 shadow as BM_DrawColorShadow); drawstring's argument order
void(vector pos, string s, vector sc, vector rgb, float a, float fl) RH_ShadowStr =
{
	drawstring (pos + '0.7 0.7 0', s, sc, '0 0 0', 0.85 * a, fl);
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

void(float cx, float cy, float rad, float pulse, vector col_red, vector col_cyan) RH_DrawXMarker =
{
	local float xr, cr, rot;
	local vector a1, a2, b1, b2;

	cr = rad * (1.0 + 0.08 * pulse);
	rot = time * 55;
	RH_Circle (cx, cy, cr, 16, rot, 1.5, col_red, 0.90);
	RH_Circle (cx, cy, cr * 1.24, 8, -rot * 0.7, 1.0, col_cyan, 0.52);

	xr = rad * 0.82;
	a1 = (cx - xr) * '1 0 0' + (cy - xr) * '0 1 0';
	a2 = (cx + xr) * '1 0 0' + (cy + xr) * '0 1 0';
	b1 = (cx - xr) * '1 0 0' + (cy + xr) * '0 1 0';
	b2 = (cx + xr) * '1 0 0' + (cy - xr) * '0 1 0';
	RH_Line (2.8, a1, a2, col_red, 0.95);
	RH_Line (2.8, b1, b2, col_red, 0.95);
	RH_Line (1.1, a1, a2, col_cyan, 0.80);
	RH_Line (1.1, b1, b2, col_cyan, 0.80);
};

void(float px, float py, float dx, float dy, float dist, float sz, vector col_red, vector col_cyan) RH_DrawEdgeArrow =
{
	local float nx, ny, tx, ty;
	local vector tip, lwing, rwing, x1, x2, x3, x4;

	tip = (px + dx * 8) * '1 0 0' + (py + dy * 8) * '0 1 0';
	nx = -dy;
	ny = dx;
	lwing = (px - dx * 6 + nx * 6.5) * '1 0 0' + (py - dy * 6 + ny * 6.5) * '0 1 0';
	rwing = (px - dx * 6 - nx * 6.5) * '1 0 0' + (py - dy * 6 - ny * 6.5) * '0 1 0';
	RH_Line (2.2, tip, lwing, col_red, 0.95);
	RH_Line (2.2, tip, rwing, col_red, 0.95);
	RH_Line (1.4, lwing, rwing, col_cyan, 0.85);

	x1 = (px - 3) * '1 0 0' + (py - 3) * '0 1 0';
	x2 = (px + 3) * '1 0 0' + (py + 3) * '0 1 0';
	x3 = (px - 3) * '1 0 0' + (py + 3) * '0 1 0';
	x4 = (px + 3) * '1 0 0' + (py - 3) * '0 1 0';
	RH_Line (1.4, x1, x2, col_red, 0.92);
	RH_Line (1.4, x3, x4, col_red, 0.92);

	tx = px - dx * 18;
	ty = py - dy * 12 - sz * 0.5;
	BM_ShadowCentered (tx, ty, strcat (ftos (floor (dist)), "u"), sz * 0.82, col_cyan, 0.94);
};

// 14 unique Red Hat Linux hacking sequences (all lines <= 28 chars for a compact terminal)
string(float seq, float slot, float n_en) RH_SeqLine =
{
	local string nstr;

	nstr = ftos (n_en);
	if (seq == 1)
	{
		if (slot == 0) return "$ cd /hacks/redhat-linux";
		if (slot == 1) return "$ exec hacks/wallhacks.exe";
		if (slot == 2) return "| RED HAT HACKER MODE ON!! |";
		if (slot == 3) return "SCANNING QUAKE 4 NEWBIES..";
		return strcat ("FOUND ", nstr, " NOOBS THRU WALLS!");
	}
	if (seq == 2)
	{
		if (slot == 0) return "$ sudo su - root@fedora";
		if (slot == 1) return "$ ./wallhack.sh --no-pvs";
		if (slot == 2) return "| FEDORA WALLHACK ONLINE!! |";
		if (slot == 3) return "BYPASSING PVS LIKE MENACE.";
		return strcat (nstr, " NOOBS EXPOSED IN X-RAY!");
	}
	if (seq == 3)
	{
		if (slot == 0) return "$ cd /bin/bakersfield_os";
		if (slot == 1) return "$ python3 xray.py --hax";
		if (slot == 2) return "| RHEL9 SUPERCOMPUTER BOOT |";
		if (slot == 3) return "READING ENEMY IP ADDRS...";
		return strcat ("TRACED ", nstr, " PLAYERS IN SOCKS!");
	}
	if (seq == 4)
	{
		if (slot == 0) return "$ ssh fedora@quake-node1";
		if (slot == 1) return "$ modprobe nvidia_wallhack";
		if (slot == 2) return "| ROB DOB CYBER-BRAIN ON!! |";
		if (slot == 3) return "ENHANCE. ENHANCE. ENHANCE.";
		return strcat ("X-RAY LOCKED ON ", nstr, " VICTIMS!");
	}
	if (seq == 5)
	{
		if (slot == 0) return "$ cat /proc/enemy_coords";
		if (slot == 1) return "$ ./hacks.exe --fedora";
		if (slot == 2) return "| LINUX SUPER-HACKER MODE  |";
		if (slot == 3) return "PINGING FOR CAMPERS...";
		return strcat (nstr, " NOOBS BEHIND BRICK WALL!");
	}
	if (seq == 6)
	{
		if (slot == 0) return "$ chmod +x /tmp/xray.bin";
		if (slot == 1) return "$ nohup /tmp/xray.bin &";
		if (slot == 2) return "| RED HAT CYBER-WARFARE ON |";
		if (slot == 3) return "DOWNLOADING MORE XRAY RAM.";
		return strcat ("GOT ", nstr, " CHUMPS IN HD X-RAY!");
	}
	if (seq == 7)
	{
		if (slot == 0) return "$ yum install -y wallhack";
		if (slot == 1) return "$ systemctl start xrayd";
		if (slot == 2) return "| YUM INSTALL: EZ WALLHACK |";
		if (slot == 3) return "HACKING MAINFRAME GIBSON..";
		return strcat (nstr, " TARGETS TOTAL EXPOSED!!");
	}
	if (seq == 8)
	{
		if (slot == 0) return "$ cd /opt/fedora/exploits";
		if (slot == 1) return "$ nmap -sS --xray 10.0/16";
		if (slot == 2) return "| FEDORA ROOT SHELL READY! |";
		if (slot == 3) return "DECRYPTING SPAWN COORDS...";
		return strcat (nstr, " CAMPERS FLAGGED 4 KISS!");
	}
	if (seq == 9)
	{
		if (slot == 0) return "$ gcc -O3 xray.c -o hax";
		if (slot == 1) return "$ ./hax --no-mercy --cyan";
		if (slot == 2) return "| COMPILED WITH 0 WARNINGS |";
		if (slot == 3) return "TELLING ROB ALL COORDS...";
		return strcat (nstr, " COWARDS BEHIND DOORS!");
	}
	if (seq == 10)
	{
		if (slot == 0) return "$ mount /dev/hax /mnt/xray";
		if (slot == 1) return "$ tail -f /var/log/noobs";
		if (slot == 2) return "| KERNEL PANIC: 2 MUCH HAX |";
		if (slot == 3) return "SCANNING ROCKET JUMPERS...";
		return strcat ("FOUND ", nstr, " FREE FRAGS ON MAP!");
	}
	if (seq == 11)
	{
		if (slot == 0) return "$ docker run redhat/xray";
		if (slot == 1) return "$ exec /bin/rob_terminator";
		if (slot == 2) return "| DOCKER WALLHACK READY!!  |";
		if (slot == 3) return "BRUTE-FORCING ENGINE PVS..";
		return strcat (nstr, " TARGETS OFFICIAL DOXXED!");
	}
	if (seq == 12)
	{
		if (slot == 0) return "$ curl https://hax.sh | sh";
		if (slot == 1) return "$ LD_PRELOAD=/lib/xray.so";
		if (slot == 2) return "| LD_PRELOAD HAX INJECTED! |";
		if (slot == 3) return "COMPUTING POCKET CALC...";
		return strcat ("TRACKING ", nstr, " POOR VICTIMS!");
	}
	if (seq == 13)
	{
		if (slot == 0) return "$ systemctl start fedorax";
		if (slot == 1) return "$ gdb -p $(pidof zircon)";
		if (slot == 2) return "| MEMORY PATCH: DEPTH=OFF! |";
		if (slot == 3) return "PEEKING THRU EVERY WALL...";
		return strcat (nstr, " NEWBIES CANNOT HIDE NOW!");
	}
	if (slot == 0) return "$ cd ~/Desktop/legit_linux";
	if (slot == 1) return "$ ./not_wallhacks_swear.exe";
	if (slot == 2) return "| 100% LEGIT LINUX STATS   |";
	if (slot == 3) return "AUDITING CAMPING SPOTS...";
	return strcat ("CAUGHT ", nstr, " FOES RED-HANDED!");
};

string(float idx) RH_LiveCmd =
{
	local float k;

	k = idx - 6 * floor (idx / 6);
	if (k == 0) return "tail -n1 /proc/xray";
	if (k == 1) return "nmap --top 10 10.0";
	if (k == 2) return "grep noob /proc/map";
	if (k == 3) return "watch -n0 wallhax";
	if (k == 4) return "cat /dev/fedora_hax";
	return "ping -c1 127.0.0.1";
};

void(float w, float h) RH_DrawXRayHUD =
{
	local float mode, timer10, spd, armed, seq, age, sz, lh, top_h, bot_h;
	local float pulse, sy, n_en, dist, rad, dirx, diry, dlen, px, py;
	local float tx, ty, tbar_h, rrad, rcx, rcy, sw_ang, swc, sws, bx, by, rf, rr;
	local float cx, cy, r0, r1;
	local vector col_red, col_cyan, col_white, col_green, col_muted, col_ally, sv;
	local vector cam_org, cam_ang, sp, sp_top, sp_bot, delta;
	local entity t;
	local string s, tname;

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
		rh_type_last_ch = -1;
		rh_type_stage = 0;
		return;
	}
	if (rh_prev_mode == 0 && (mode == 1 || mode == 2))
	{
		rh_launch_t = time;
		rh_active_seq = getstati (BMST_FD_SEQ);
		rh_type_last_ch = -1;
		rh_type_stage = 0;
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

	col_red   = '0.96 0.14 0.16';
	col_cyan  = '0.05 0.94 1.00';
	col_white = '0.94 0.97 1.00';
	col_green = '0.28 0.96 0.45';
	col_muted = '0.55 0.75 0.82';
	col_ally  = '0.25 0.95 0.45';

	pulse = RH_Sin (time * 7);
	sz = bound (7, floor (w * 0.0115), 11);
	sv = sz * '1 1 0';
	lh = sz + 3;
	top_h = sz + 10;
	bot_h = sz + 8;

	// Subtle X-ray sweep: a short tick on each screen edge only (no line or glow band across the middle of the view)
	if (mode == 1 || mode == 2)
	{
		sy = (time * 0.42 - floor (time * 0.42)) * h;
		drawfill (sy * '0 1 0', '8 1 0', col_cyan, 0.34, 0);
		drawfill ((w - 8) * '1 0 0' + sy * '0 1 0', '8 1 0', col_cyan, 0.34, 0);
	}

	cam_org = getpropertyvec (VF_ORIGIN);
	cam_ang = getpropertyvec (VF_ANGLES);
	makevectors (cam_ang);

	// 1. 3D-projected enemy X-markers, lock circles & full-viewport off-screen arrows
	n_en = 0;
	t = rh_xray_head;
	while (t)
	{
		if (time - t.rh_last_t <= 0.6)
		{
			dist = vlen (t.origin - cam_org);
			if (t.rh_flags & 2)
			{
				if (mode != 3)
				{
					sp = cs_project (t.origin + '0 0 28');
					if (sp_z > 0 && sp_x > 16 && sp_x < w - 16 && sp_y > top_h + 8 && sp_y < h - bot_h - 8)
					{
						tname = t.netname;
						if (tname == "")
							tname = "ALLY";
						BM_ShadowCentered (sp_x, sp_y - sz - 3, strcat ("[ALLY] ", tname), sz * 0.80, col_ally, 0.85);
					}
				}
			}
			else
			{
				n_en = n_en + 1;
				if (mode != 3)
				{
					sp = cs_project (t.origin + '0 0 24');
					if (sp_z > 0 && sp_x >= 16 && sp_x <= w - 16 && sp_y >= top_h + 12 && sp_y <= h - bot_h - 12)
					{
						sp_top = cs_project (t.origin + '0 0 48');
						sp_bot = cs_project (t.origin - '0 0 18');
						rad = bound (12, fabs (sp_bot_y - sp_top_y) * 0.56, 40);
						RH_DrawXMarker (sp_x, sp_y, rad, pulse, col_red, col_cyan);

						tname = t.netname;
						if (tname == "")
							tname = "HOSTILE";
						if (strlen (tname) > 14)
							tname = substring (tname, 0, 14);
						BM_ShadowCentered (sp_x, sp_y - rad - sz - 4, tname, sz * 0.88, col_white, 0.96);
						BM_ShadowCentered (sp_x, sp_y + rad + 2, strcat (ftos (floor (dist)), "u | ", ftos (t.rh_hp), "HP"), sz * 0.78, col_cyan, 0.92);
					}
					else
					{
						delta = (t.origin + '0 0 24') - cam_org;
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
						px = w * 0.5 + dirx * (w * 0.5 - 24);
						py = h * 0.5 + diry * (h * 0.5 - top_h - 24);
						px = bound (20, px, w - 20);
						py = bound (top_h + 18, py, h - bot_h - 18);
						RH_DrawEdgeArrow (px, py, dirx, diry, dist, sz, col_red, col_cyan);
					}
				}
			}
		}
		t = t.rh_next;
	}

	// 2. Center tactical reticle (clean corner brackets)
	if (mode == 1 || mode == 2)
	{
		cx = w * 0.5;
		cy = h * 0.5;
		r0 = 6;
		r1 = 13;
		RH_Line (1.3, (cx - r1) * '1 0 0' + (cy - r0) * '0 1 0', (cx - r0) * '1 0 0' + (cy - r0) * '0 1 0', col_cyan, 0.78);
		RH_Line (1.3, (cx - r0) * '1 0 0' + (cy - r1) * '0 1 0', (cx - r0) * '1 0 0' + (cy - r0) * '0 1 0', col_cyan, 0.78);
		RH_Line (1.3, (cx + r0) * '1 0 0' + (cy - r0) * '0 1 0', (cx + r1) * '1 0 0' + (cy - r0) * '0 1 0', col_cyan, 0.78);
		RH_Line (1.3, (cx + r0) * '1 0 0' + (cy - r1) * '0 1 0', (cx + r0) * '1 0 0' + (cy - r0) * '0 1 0', col_cyan, 0.78);
		RH_Line (1.3, (cx - r1) * '1 0 0' + (cy + r0) * '0 1 0', (cx - r0) * '1 0 0' + (cy + r0) * '0 1 0', col_cyan, 0.78);
		RH_Line (1.3, (cx - r0) * '1 0 0' + (cy + r0) * '0 1 0', (cx - r0) * '1 0 0' + (cy + r1) * '0 1 0', col_cyan, 0.78);
		RH_Line (1.3, (cx + r0) * '1 0 0' + (cy + r0) * '0 1 0', (cx + r1) * '1 0 0' + (cy + r0) * '0 1 0', col_cyan, 0.78);
		RH_Line (1.3, (cx + r0) * '1 0 0' + (cy + r0) * '0 1 0', (cx + r0) * '1 0 0' + (cy + r1) * '0 1 0', col_cyan, 0.78);
		drawfill ((cx - 1) * '1 0 0' + (cy - 1) * '0 1 0', '2 2 0', col_red, 0.92, 0);
	}

	// 3. Top-right status: "INITIALIZING ALL HACKS... / EXECUTING HACKS.EXE" as two right-aligned drop-shadowed lines
	//    (was a dark full-width banner across the top). rty walks down the top-right stack.
	local string ban1, ban2;
	local float ba, rty;
	ba = 0.90 + 0.10 * pulse;
	if (age < 1.60)
	{
		ban1 = "INITIALIZING ALL HACKS...";
		ban2 = "EXECUTING HACKS.EXE";
	}
	else
	{
		ban1 = "HACKING...";
		ban2 = strcat ("HACKS.EXE ACTIVE  |  HOSTILES: ", ftos (n_en));
	}
	rty = 8;
	RH_ShadowStrRight (w - 8, rty, ban1, sv, '1 0.36 0.36', ba);
	RH_ShadowStrRight (w - 8, rty + lh, ban2, sv, col_cyan, ba);
	rty = rty + 2 * lh + 4;

	// 4. Top-left Red Hat Linux terminal (active typing + retro keyboard SFX): drop-shadowed lines from JBH_TopLeftY(),
	//    clear of the con_notify lines, with no window panel or title bar fill
	local float tfont, tlh, body_y, total_ch, len0, len1, len3, len4, rem, cur_ch, stage;
	local float live_t, lidx, lch, llen;
	local string ts0, ts1, ts2, ts3, ts4, live_s, cur, prompt_s;
	local vector tsv;

	tfont = max (7, sz * 0.84);
	tsv = tfont * '1 1 0';
	tlh = tfont + 3;
	tx = 10;
	ty = JBH_TopLeftY ();
	tbar_h = tlh + 4;
	RH_ShadowStr (tx * '1 0 0' + ty * '0 1 0', "root@rhel9:/hacks", tsv * 0.94, col_white, 0.98, 0);

	ts0 = RH_SeqLine (seq, 0, n_en);
	ts1 = RH_SeqLine (seq, 1, n_en);
	ts2 = RH_SeqLine (seq, 2, n_en);
	ts3 = RH_SeqLine (seq, 3, n_en);
	ts4 = RH_SeqLine (seq, 4, n_en);
	len0 = strlen (ts0);
	len1 = strlen (ts1);
	len3 = strlen (ts3);
	len4 = strlen (ts4);

	if (pulse > 0)
		cur = "_";
	else
		cur = " ";

	total_ch = floor (max (0, age - 0.04) * 28);
	cur_ch = 0;
	stage = 0;
	body_y = ty + tlh + 3;
	prompt_s = strcat ("[root@rhel9]#", (pulse > 0) ? " _" : "");

	if (total_ch <= len0)
	{
		cur_ch = total_ch;
		stage = 0;
		RH_ShadowStr (tx * '1 0 0' + body_y * '0 1 0', strcat (substring (ts0, 0, total_ch), "_"), tsv, col_green, 0.98, 0);
	}
	else if (total_ch < len0 + 4)
	{
		cur_ch = len0;
		stage = 1;
		RH_ShadowStr (tx * '1 0 0' + body_y * '0 1 0', ts0, tsv, col_green, 0.98, 0);
		RH_ShadowStr (tx * '1 0 0' + (body_y + tlh) * '0 1 0', "_", tsv, col_white, 0.96, 0);
	}
	else if (total_ch <= len0 + 4 + len1)
	{
		cur_ch = total_ch - 4;
		stage = 1;
		RH_ShadowStr (tx * '1 0 0' + body_y * '0 1 0', ts0, tsv, col_green, 0.98, 0);
		RH_ShadowStr (tx * '1 0 0' + (body_y + tlh) * '0 1 0', strcat (substring (ts1, 0, total_ch - (len0 + 4)), "_"), tsv, col_white, 0.98, 0);
	}
	else if (total_ch < len0 + 4 + len1 + 5)
	{
		cur_ch = len0 + len1;
		stage = 2;
		RH_ShadowStr (tx * '1 0 0' + body_y * '0 1 0', ts0, tsv, col_green, 0.98, 0);
		RH_ShadowStr (tx * '1 0 0' + (body_y + tlh) * '0 1 0', ts1, tsv, col_white, 0.98, 0);
	}
	else
	{
		RH_ShadowStr (tx * '1 0 0' + body_y * '0 1 0', ts0, tsv, col_green, 0.98, 0);
		RH_ShadowStr (tx * '1 0 0' + (body_y + tlh) * '0 1 0', ts1, tsv, col_white, 0.98, 0);
		RH_ShadowStr (tx * '1 0 0' + (body_y + 2 * tlh) * '0 1 0', "+==========================+", tsv, col_red, 0.96, 0);
		RH_ShadowStr (tx * '1 0 0' + (body_y + 3 * tlh) * '0 1 0', ts2, tsv, col_red, 0.98, 0);
		RH_ShadowStr (tx * '1 0 0' + (body_y + 4 * tlh) * '0 1 0', "+==========================+", tsv, col_red, 0.96, 0);
		rem = total_ch - (len0 + 4 + len1 + 5);
		if (rem <= len3)
		{
			cur_ch = len0 + len1 + rem;
			stage = 3;
			RH_ShadowStr (tx * '1 0 0' + (body_y + 5 * tlh) * '0 1 0', strcat (substring (ts3, 0, rem), "_"), tsv, col_cyan, 0.96, 0);
		}
		else if (rem < len3 + 3)
		{
			cur_ch = len0 + len1 + len3;
			stage = 3;
			RH_ShadowStr (tx * '1 0 0' + (body_y + 5 * tlh) * '0 1 0', ts3, tsv, col_cyan, 0.96, 0);
		}
		else if (rem <= len3 + 3 + len4)
		{
			cur_ch = len0 + len1 + rem - 3;
			stage = 3;
			RH_ShadowStr (tx * '1 0 0' + (body_y + 5 * tlh) * '0 1 0', ts3, tsv, col_cyan, 0.96, 0);
			RH_ShadowStr (tx * '1 0 0' + (body_y + 6 * tlh) * '0 1 0', strcat (substring (ts4, 0, rem - (len3 + 3)), "_"), tsv, col_white, 0.98, 0);
		}
		else
		{
			RH_ShadowStr (tx * '1 0 0' + (body_y + 5 * tlh) * '0 1 0', ts3, tsv, col_cyan, 0.96, 0);
			RH_ShadowStr (tx * '1 0 0' + (body_y + 6 * tlh) * '0 1 0', ts4, tsv, col_white, 0.98, 0);
			live_t = (rem - (len3 + 3 + len4)) / 28;
			lidx = floor (live_t / 2.2);
			live_s = RH_LiveCmd (lidx);
			llen = strlen (live_s);
			lch = floor ((live_t - lidx * 2.2) * 26);
			if (lch <= llen)
			{
				cur_ch = len0 + len1 + len3 + len4 + lidx * 24 + lch;
				stage = 4 + lidx;
				prompt_s = strcat ("# ", substring (live_s, 0, lch), "_");
			}
			else
			{
				cur_ch = len0 + len1 + len3 + len4 + (lidx + 1) * 24;
				stage = 5 + lidx;
				prompt_s = strcat ("# ", live_s, (pulse > 0) ? "_" : "");
			}
			RH_ShadowStr (tx * '1 0 0' + (body_y + 7 * tlh + 2) * '0 1 0', prompt_s, tsv, col_green, 0.95, 0);
		}
	}
	if (stage <= 3)
		RH_ShadowStr (tx * '1 0 0' + (body_y + 7 * tlh + 2) * '0 1 0', prompt_s, tsv, col_green, 0.95, 0);

	if (mode == 1 || mode == 2)
		RH_TypeTickAudio (cam_org, cur_ch, stage);

	// 5. Top-right mini-map (radar: rings, cross and sweep as lines, blips as dots, no filled background) + drone telemetry,
	//    right-aligned under the status lines
	rrad = bound (34, floor (h * 0.115), 58);
	RH_ShadowStrRight (w - 8, rty, strcat ("X-RAY RADAR [", ftos (n_en), "]"), sv * 0.84, col_white, 0.96);

	rcx = w - 10 - rrad;
	rcy = rty + tbar_h + rrad + 5;
	RH_Circle (rcx, rcy, rrad, 24, 0, 1.3, col_cyan, 0.78);
	RH_Circle (rcx, rcy, rrad * 0.5, 16, 0, 1.0, col_cyan, 0.36);
	RH_Line (1.0, (rcx - rrad) * '1 0 0' + rcy * '0 1 0', (rcx + rrad) * '1 0 0' + rcy * '0 1 0', col_cyan, 0.30);
	RH_Line (1.0, rcx * '1 0 0' + (rcy - rrad) * '0 1 0', rcx * '1 0 0' + (rcy + rrad) * '0 1 0', col_cyan, 0.30);

	sw_ang = (time * 180) * RH_DEG2RAD;
	swc = RH_Cos (sw_ang);
	sws = RH_Sin (sw_ang);
	RH_Line (1.6, rcx * '1 0 0' + rcy * '0 1 0', (rcx + swc * rrad) * '1 0 0' + (rcy + sws * rrad) * '0 1 0', col_cyan, 0.88);
	drawfill ((rcx - 1.5) * '1 0 0' + (rcy - 1.5) * '0 1 0', '3 3 0', col_white, 0.96, 0);

	t = rh_xray_head;
	while (t)
	{
		if (time - t.rh_last_t <= 0.6)
		{
			delta = t.origin - cam_org;
			delta_z = 0;
			rf = delta * v_forward;
			rr = delta * v_right;
			bx = rcx + bound (-1, rr / 2600, 1) * (rrad - 3);
			by = rcy - bound (-1, rf / 2600, 1) * (rrad - 3);
			drawfill ((bx - 2) * '1 0 0' + (by - 2) * '0 1 0', '4 4 0', (t.rh_flags & 2) ? col_ally : col_red, 0.96, 0);
		}
		t = t.rh_next;
	}

	local float ft_y;
	ft_y = rcy + rrad + 6;
	if (mode == 2)
		RH_ShadowStrRight (w - 8, ft_y, ">> DASHING <<", sv * 0.82, col_red, 0.80 + 0.20 * pulse);
	else if (mode == 3)
		RH_ShadowStrRight (w - 8, ft_y, "SIGNAL LOST", sv * 0.82, col_red, 0.96);
	else
		RH_ShadowStrRight (w - 8, ft_y, armed ? "CRUISE [ARMED]" : "CRUISE [BOOT]", sv * 0.82, col_cyan, 0.94);

	RH_ShadowStrRight (w - 8, ft_y + lh, strcat ("VEL : ", ftos (spd), " u/s"), sv * 0.80, col_white, 0.92);
	if (timer10 == 999)
		s = "FUEL: UNLIMITED";
	else
		s = strcat ("FUEL: ", ftos (floor (timer10 / 10)), ".", ftos (timer10 - 10 * floor (timer10 / 10)), "s");
	RH_ShadowStrRight (w - 8, ft_y + 2 * lh, s, sv * 0.80, (timer10 < 40 && timer10 != 999) ? col_red : col_cyan, 0.94);
	bm_topright_y = ft_y + 3 * lh;

	// 6. Controls: bottom-right, right-aligned above BM_CornerBottomY(h) in two short lines (was a dark full-width bottom strip
	//    with centred text). Bottom-left stays free for the centerprint toast and the SIGNAL LOST line.
	local float csz;
	csz = sz * 0.90;
	BM_ShadowColorRight (w - 8, BM_CornerBottomY (h) - csz * 2 - 3, "^5[MOUSE]^7 STEER   ^1[LMB]^7 DASH / DETONATE", csz, 0.94);
	BM_ShadowColorRight (w - 8, BM_CornerBottomY (h) - csz, "^3[H]^7 RECALL", csz, 0.94);

	// 7. Centerprint toast (bottom-left; CSQC_Parse_CenterPrint swallows centerprints, so it must be drawn here too
	//    while the drone flies), then the post-blast SIGNAL LOST line stacked just above it
	BM_DrawCenterPrint (w, h);
	if (mode == 3)
	{
		BM_DrawColorShadow (JP_IsVisible () ? 36 : 10, bm_cp_top_y - sz * 0.95 - 3, "^1// SIGNAL LOST :: DETONATED //", sz * 0.95, 0.88 + 0.12 * pulse);
	}
};

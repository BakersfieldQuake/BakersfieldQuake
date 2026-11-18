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

	if (cur_ch > rh_type_last_ch && (time - rh_type_snd_t) >= 0.045)
	{
		k = cur_ch - 4 * floor (cur_ch / 4);
		if (k == 0) s = "robhead/key1.wav";
		else if (k == 1) s = "robhead/key2.wav";
		else if (k == 2) s = "robhead/key3.wav";
		else s = "robhead/key4.wav";
		RH_PlayKey (org, s, 0.24);
		rh_type_snd_t = time;
		rh_type_last_ch = cur_ch;
	}
	if (stage > rh_type_stage)
	{
		if (stage == 1)
			RH_PlayKey (org, "robhead/key_enter.wav", 0.30);
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
	local vector cam_org;
	local float dist, a;

	cam_org = getpropertyvec (VF_ORIGIN);
	t = rh_xray_head;
	while (t)
	{
		if (time - t.rh_last_t <= 0.6 && !(t.rh_flags & 2) && t.rh_mdlname != "")
		{
			dist = vlen (t.origin - cam_org);
			if (dist <= 3200)
			{
				// Skip targets already in direct line-of-sight so we don't double-render a cyan glow over visible enemies
				traceline (cam_org, t.origin + '0 0 24', TRUE, world);
				if (trace_fraction < 0.995)
				{
					a = 0.24 * (1 - bound (0, (dist - 1800) / 1400, 1));
					if (a > 0.02)
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
						s.colormod = '0 0.55 0.68';
						s.alpha = a;
						addentity (s);
					}
				}
			}
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

void(float cx, float cy, float rad, float a, vector col) RH_DrawTargetBracket =
{
	local float arm;
	local vector hx, vy;

	arm = bound (3, floor (rad * 0.38), 5);
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

void(entity t, vector cam_org, float w, float h, float top_h, float bot_h, vector col_red) RH_DrawEdgePip =
{
	local vector delta, tip, lwing, rwing;
	local float dist, dirx, diry, dlen, px, py, nx, ny, a;

	if (!t)
		return;
	delta = (t.origin + '0 0 24') - cam_org;
	dist = vlen (delta);
	a = 0.58 * (1 - bound (0, (dist - 800) / 1400, 0.65));
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

	tip = (px + dirx * 4.5) * '1 0 0' + (py + diry * 4.5) * '0 1 0';
	nx = -diry;
	ny = dirx;
	lwing = (px - dirx * 3.5 + nx * 4) * '1 0 0' + (py - diry * 3.5 + ny * 4) * '0 1 0';
	rwing = (px - dirx * 3.5 - nx * 4) * '1 0 0' + (py - diry * 3.5 - ny * 4) * '0 1 0';
	RH_Line (1.2, tip, lwing, col_red, a);
	RH_Line (1.2, tip, rwing, col_red, a);
};

// 14 unique Red Hat Linux hacking sequences (cmd + compact status line)
string(float seq, float is_result, float n_en) RH_SeqLine =
{
	local string nstr;

	nstr = ftos (n_en);
	if (seq == 1)
		return is_result ? strcat ("FOUND ", nstr, " NOOBS THRU WALLS!") : "$ exec hacks/wallhacks.exe";
	if (seq == 2)
		return is_result ? strcat (nstr, " NOOBS EXPOSED IN X-RAY!") : "$ ./wallhack.sh --no-pvs";
	if (seq == 3)
		return is_result ? strcat ("TRACED ", nstr, " PLAYERS IN SOCKS!") : "$ python3 xray.py --hax";
	if (seq == 4)
		return is_result ? strcat ("X-RAY LOCKED ON ", nstr, " VICTIMS!") : "$ modprobe nvidia_wallhack";
	if (seq == 5)
		return is_result ? strcat (nstr, " NOOBS BEHIND BRICK WALL!") : "$ ./hacks.exe --fedora";
	if (seq == 6)
		return is_result ? strcat ("GOT ", nstr, " CHUMPS IN HD X-RAY!") : "$ nohup /tmp/xray.bin &";
	if (seq == 7)
		return is_result ? strcat (nstr, " TARGETS TOTAL EXPOSED!!") : "$ systemctl start xrayd";
	if (seq == 8)
		return is_result ? strcat (nstr, " CAMPERS FLAGGED 4 KISS!") : "$ nmap -sS --xray 10.0/16";
	if (seq == 9)
		return is_result ? strcat (nstr, " COWARDS BEHIND DOORS!") : "$ ./hax --no-mercy --cyan";
	if (seq == 10)
		return is_result ? strcat ("FOUND ", nstr, " FREE FRAGS ON MAP!") : "$ tail -f /var/log/noobs";
	if (seq == 11)
		return is_result ? strcat (nstr, " TARGETS OFFICIAL DOXXED!") : "$ exec /bin/rob_terminator";
	if (seq == 12)
		return is_result ? strcat ("TRACKING ", nstr, " POOR VICTIMS!") : "$ LD_PRELOAD=/lib/xray.so";
	if (seq == 13)
		return is_result ? strcat (nstr, " NEWBIES CANNOT HIDE NOW!") : "$ gdb -p $(pidof zircon)";
	return is_result ? strcat ("CAUGHT ", nstr, " FOES RED-HANDED!") : "$ ./not_wallhacks_swear.exe";
};

void(float w, float h) RH_DrawXRayHUD =
{
	local float mode, timer10, spd, armed, seq, age, sz, lh, top_h, bot_h;
	local float pulse, sy, n_en, dist, rad, dfade;
	local float tx, ty, rrad, rcx, rcy, sw_ang, swc, sws, bx, by, rf, rr;
	local float cx, cy, r0, arm, off1_d, off2_d, off3_d;
	local float len_cmd, total_ch, cur_ch, stage;
	local vector col_red, col_cyan, col_white, col_green, col_ally, sv;
	local vector cam_org, cam_ang, sp, sp_top, sp_bot, delta;
	local entity t, off1, off2, off3;
	local string s, tname, tcmd, tres;

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

	col_red   = '0.96 0.20 0.20';
	col_cyan  = '0.18 0.88 0.98';
	col_white = '0.94 0.97 1.00';
	col_green = '0.32 0.92 0.48';
	col_ally  = '0.28 0.92 0.48';

	pulse = RH_Sin (time * 7);
	sz = 5;
	sv = sz * '1 1 0';
	lh = 8;
	top_h = 16;
	bot_h = 16;

	// Subtle edge scan ticks only
	if (mode == 1 || mode == 2)
	{
		sy = (time * 0.42 - floor (time * 0.42)) * h;
		drawfill (sy * '0 1 0', '6 1 0', col_cyan, 0.22, 0);
		drawfill ((w - 6) * '1 0 0' + sy * '0 1 0', '6 1 0', col_cyan, 0.22, 0);
	}

	cam_org = getpropertyvec (VF_ORIGIN);
	cam_ang = getpropertyvec (VF_ANGLES);
	makevectors (cam_ang);

	// 1. Minimal 3D-projected corner brackets + up to 3 nearest off-screen edge chevrons
	n_en = 0;
	off1 = world;
	off2 = world;
	off3 = world;
	off1_d = 99999;
	off2_d = 99999;
	off3_d = 99999;

	t = rh_xray_head;
	while (t)
	{
		if (time - t.rh_last_t <= 0.6)
		{
			dist = vlen (t.origin - cam_org);
			if (t.rh_flags & 2)
			{
				if (mode != 3 && dist <= 1600)
				{
					sp = cs_project (t.origin + '0 0 28');
					if (sp_z > 0 && sp_x > 16 && sp_x < w - 16 && sp_y > top_h + 8 && sp_y < h - bot_h - 8)
					{
						tname = t.netname;
						if (tname == "")
							tname = "ALLY";
						BM_ShadowCentered (sp_x, sp_y - 8, strcat ("[ALLY] ", tname), sz, col_ally, 0.65);
					}
				}
			}
			else
			{
				n_en = n_en + 1;
				if (mode != 3)
				{
					sp = cs_project (t.origin + '0 0 24');
					if (sp_z > 0 && sp_x >= 16 && sp_x <= w - 16 && sp_y >= top_h + 10 && sp_y <= h - bot_h - 10)
					{
						if (dist <= 2800)
						{
							dfade = 1 - bound (0, (dist - 1400) / 1400, 0.60);
							sp_top = cs_project (t.origin + '0 0 48');
							sp_bot = cs_project (t.origin - '0 0 18');
							rad = bound (7, fabs (sp_bot_y - sp_top_y) * 0.40, 20);
							RH_DrawTargetBracket (sp_x, sp_y, rad, 0.58 * dfade, (dist < 420) ? col_red : col_cyan);

							if (dist <= 1800)
							{
								tname = t.netname;
								if (tname == "")
									tname = "HOSTILE";
								if (strlen (tname) > 12)
									tname = substring (tname, 0, 12);
								if (dist <= 1100)
									s = strcat (tname, " ", ftos (t.rh_hp));
								else
									s = tname;
								BM_ShadowCentered (sp_x, sp_y - rad - 7, s, sz, col_white, 0.78 * dfade);
							}
						}
					}
					else if (dist <= 2200)
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
		RH_DrawEdgePip (off1, cam_org, w, h, top_h, bot_h, col_red);
		RH_DrawEdgePip (off2, cam_org, w, h, top_h, bot_h, col_red);
		RH_DrawEdgePip (off3, cam_org, w, h, top_h, bot_h, col_red);
	}

	// 2. Center reticle (crisp 1px corner ticks + dot)
	if (mode == 1 || mode == 2)
	{
		cx = w * 0.5;
		cy = h * 0.5;
		r0 = 5;
		arm = 4;
		drawfill ((cx - r0 - arm) * '1 0 0' + (cy - r0) * '0 1 0', arm * '1 0 0' + '0 1 0', col_cyan, 0.55, 0);
		drawfill ((cx - r0) * '1 0 0' + (cy - r0 - arm) * '0 1 0', '1 0 0' + arm * '0 1 0', col_cyan, 0.55, 0);
		drawfill ((cx + r0) * '1 0 0' + (cy - r0) * '0 1 0', arm * '1 0 0' + '0 1 0', col_cyan, 0.55, 0);
		drawfill ((cx + r0 - 1) * '1 0 0' + (cy - r0 - arm) * '0 1 0', '1 0 0' + arm * '0 1 0', col_cyan, 0.55, 0);
		drawfill ((cx - r0 - arm) * '1 0 0' + (cy + r0 - 1) * '0 1 0', arm * '1 0 0' + '0 1 0', col_cyan, 0.55, 0);
		drawfill ((cx - r0) * '1 0 0' + (cy + r0) * '0 1 0', '1 0 0' + arm * '0 1 0', col_cyan, 0.55, 0);
		drawfill ((cx + r0) * '1 0 0' + (cy + r0 - 1) * '0 1 0', arm * '1 0 0' + '0 1 0', col_cyan, 0.55, 0);
		drawfill ((cx + r0 - 1) * '1 0 0' + (cy + r0) * '0 1 0', '1 0 0' + arm * '0 1 0', col_cyan, 0.55, 0);
		drawfill ((cx - 1) * '1 0 0' + (cy - 1) * '0 1 0', '2 2 0', col_red, 0.70, 0);
	}

	// 3. Top-left compact 2-line Red Hat terminal (clears con_notify via JBH_TopLeftY())
	tx = 10;
	ty = JBH_TopLeftY ();
	tcmd = RH_SeqLine (seq, FALSE, n_en);
	tres = RH_SeqLine (seq, TRUE, n_en);
	len_cmd = strlen (tcmd);
	total_ch = floor (max (0, age - 0.04) * 34);
	cur_ch = 0;
	stage = 0;

	if (total_ch <= len_cmd)
	{
		cur_ch = total_ch;
		stage = 0;
		RH_ShadowStr (tx * '1 0 0' + ty * '0 1 0', strcat (substring (tcmd, 0, total_ch), "_"), sv, col_green, 0.88, 0);
	}
	else
	{
		cur_ch = len_cmd;
		stage = 1;
		RH_ShadowStr (tx * '1 0 0' + ty * '0 1 0', tcmd, sv, col_green, 0.85, 0);
		RH_ShadowStr (tx * '1 0 0' + (ty + lh) * '0 1 0', tres, sv, col_white, 0.88, 0);
	}
	if (mode == 1 || mode == 2)
		RH_TypeTickAudio (cam_org, cur_ch, stage);

	// 4. Top-right compact X-ray header, mini-radar & telemetry
	RH_ShadowStrRight (w - 8, 8, strcat ("X-RAY  |  ", ftos (n_en), (n_en == 1) ? " HOSTILE" : " HOSTILES"), sv, col_cyan, 0.88);

	rrad = bound (20, floor (h * 0.065), 32);
	rcx = w - 10 - rrad;
	rcy = 8 + lh + 4 + rrad;
	RH_Circle (rcx, rcy, rrad, 20, 0, 1.0, col_cyan, 0.48);
	RH_Circle (rcx, rcy, rrad * 0.5, 14, 0, 1.0, col_cyan, 0.20);
	RH_Line (1.0, (rcx - rrad) * '1 0 0' + rcy * '0 1 0', (rcx + rrad) * '1 0 0' + rcy * '0 1 0', col_cyan, 0.18);
	RH_Line (1.0, rcx * '1 0 0' + (rcy - rrad) * '0 1 0', rcx * '1 0 0' + (rcy + rrad) * '0 1 0', col_cyan, 0.18);

	sw_ang = (time * 150) * RH_DEG2RAD;
	swc = RH_Cos (sw_ang);
	sws = RH_Sin (sw_ang);
	RH_Line (1.1, rcx * '1 0 0' + rcy * '0 1 0', (rcx + swc * rrad) * '1 0 0' + (rcy + sws * rrad) * '0 1 0', col_cyan, 0.42);
	drawfill ((rcx - 1) * '1 0 0' + (rcy - 1) * '0 1 0', '2 2 0', col_white, 0.85, 0);

	t = rh_xray_head;
	while (t)
	{
		if (time - t.rh_last_t <= 0.6)
		{
			delta = t.origin - cam_org;
			delta_z = 0;
			rf = delta * v_forward;
			rr = delta * v_right;
			bx = rcx + bound (-1, rr / 2400, 1) * (rrad - 2);
			by = rcy - bound (-1, rf / 2400, 1) * (rrad - 2);
			drawfill ((bx - 1) * '1 0 0' + (by - 1) * '0 1 0', '2.5 2.5 0', (t.rh_flags & 2) ? col_ally : col_red, 0.88, 0);
		}
		t = t.rh_next;
	}

	local float ft_y;
	ft_y = rcy + rrad + 5;
	if (mode == 2)
		RH_ShadowStrRight (w - 8, ft_y, ">> DASHING <<", sv, col_red, 0.82 + 0.18 * pulse);
	else if (mode == 3)
		RH_ShadowStrRight (w - 8, ft_y, "SIGNAL LOST", sv, col_red, 0.90);
	else
		RH_ShadowStrRight (w - 8, ft_y, armed ? "CRUISE [ARMED]" : "CRUISE [BOOT]", sv, col_cyan, 0.86);

	if (timer10 == 999)
		s = "UNLIMITED";
	else
		s = strcat ("FUEL ", ftos (floor (timer10 / 10)), ".", ftos (timer10 - 10 * floor (timer10 / 10)), "s");
	RH_ShadowStrRight (w - 8, ft_y + lh, strcat (ftos (spd), " u/s  |  ", s), sv, (timer10 < 40 && timer10 != 999) ? col_red : col_white, 0.84);
	bm_topright_y = ft_y + 2 * lh;

	// 5. Bottom-right controls (standard HUD size 5 above BM_CornerBottomY)
	BM_ShadowColorRight (w - 8, BM_CornerBottomY (h) - lh - 7, "^5[MOUSE]^7 Steer   ^1[LMB]^7 Dash / Detonate", sz, 0.88);
	BM_ShadowColorRight (w - 8, BM_CornerBottomY (h) - 7, "^3[H]^7 Recall", sz, 0.88);

	// 6. Centerprint toast (bottom-left) + post-blast SIGNAL LOST line stacked above it
	BM_DrawCenterPrint (w, h);
	if (mode == 3)
		BM_DrawColorShadow (JP_IsVisible () ? 36 : 10, bm_cp_top_y - 9, "^1// SIGNAL LOST :: DETONATED //", 6, 0.86 + 0.12 * pulse);
};

/*
================
bm_killcam_hud.qc — Call of Duty style Killcam replay & corner HUD (CSQC)

Receives a 9-chunk ENT_BM_KILLCAM (10) snapshot during the 0.55s death linger,
then smoothly interpolates the 16 Hz frames at native refresh rate from the
killer's exact camera (1P viewmodel or 3P vehicle cam) with a brief slow-mo beat
on the fatal hit, weapon SFX, tracer + CoD hitmarker, and clean corner HUD.
================
*/

float	ENT_BM_KILLCAM		= 10;
float	BMST_KC_ACTIVE		= 122;		// 0=off, 1=linger, 2=playing
float	BMST_KC_SEQ			= 123;

float	KC_C_HIST			= 36;
float	KC_C_OTH			= 3;
float	KC_C_PROJ			= 6;
float	KC_C_PLAY_SEC		= 2.75;
float	KC_C_TFAST			= 1.90;

float	KC_RF_VIEWMODEL		= 1;
float	KC_RF_DEPTHHACK		= 4;
float	KC_RF_WORLDOBJECT	= 128;

// Client preference sync
float	kc_cvar_sent;
float	kc_cvar_send_t;

// Received replay state
float	kc_rx_seq;
float	kc_rx_chunks;
float	kc_rx_nframes;
float	kc_rx_kill_tick;
float	kc_rx_ready;
string	kc_rx_kname;
string	kc_rx_wname;

// Frame buffers (36 frames)
vector	kc_ck_eye[36];
vector	kc_ck_ang[36];
float	kc_ck_vm[36];
float	kc_ck_vfrm[36];
float	kc_ck_fl[36];
float	kc_ck_snd[36];
float	kc_ck_dn3[36];
vector	kc_ck_org[36];
float	kc_ck_yaw[36];
float	kc_ck_mdl[36];
float	kc_ck_frm[36];
float	kc_ck_skin[36];
float	kc_ck_col[36];
vector	kc_ck_tend[36];

vector	kc_cv_org[36];
float	kc_cv_yaw[36];
float	kc_cv_mdl[36];
float	kc_cv_frm[36];
float	kc_cv_skin[36];
float	kc_cv_col[36];
float	kc_cv_alive[36];

float	kc_co_cnt[36];
vector	kc_co_org[108];
float	kc_co_yaw[108];
float	kc_co_mdl[108];
float	kc_co_frm[108];
float	kc_co_skin[108];
float	kc_co_col[108];

float	kc_cp_cnt[36];
vector	kc_cp_org[216];
vector	kc_cp_ang[216];
float	kc_cp_mdl[216];
float	kc_cp_frm[216];
float	kc_cp_sc[216];

// Playback state & scratch CSQC entities
float	kc_play_started;
float	kc_play_seq;
float	kc_play_t0;
float	kc_last_tick;
float	kc_hit_t;
float	kc_hit_fatal;
float	kc_flash_t;
vector	kc_flash_org;
float	kc_tracer_t;
vector	kc_tracer_a;
vector	kc_tracer_b;
float	kc_cur_dn3;

entity	kc_ent_vm;
entity	kc_ent_kbody;
entity	kc_ent_victim;
entity	kc_ent_oth[3];
entity	kc_ent_prj[6];

// Optional weapon fire sounds (with guaranteed fallbacks)
string	kc_snd_m4;
string	kc_snd_gar;
string	kc_snd_mm;

string(string path, string fallback) KC_PickSound =
{
	local float fh;

	fh = fopen (strcat ("sound/", path), 0);
	if (fh < 0)
		return fallback;
	fclose (fh);
	precache_sound (path);
	return strzone (path);
};

void() BM_Killcam_Init =
{
	registercvar ("bm_killcam", "1");
	kc_cvar_sent = -1;
	kc_cvar_send_t = 0;
	kc_rx_seq = 0;
	kc_rx_chunks = 0;
	kc_rx_ready = FALSE;
	kc_play_started = FALSE;
	kc_rx_kname = "";
	kc_rx_wname = "";

	precache_sound ("misc/mmhit2.wav");
	precache_sound ("misc/mmhit3.wav");
	precache_sound ("weapons/guncock.wav");
	precache_sound ("weapons/shotgn2.wav");
	precache_sound ("weapons/spike2.wav");
	precache_sound ("weapons/grenade.wav");
	precache_sound ("weapons/rocket1i.wav");
	precache_sound ("weapons/lhit.wav");
	precache_sound ("weapons/sawatck.wav");
	precache_sound ("weapons/sgun1.wav");

	kc_snd_m4 = KC_PickSound ("weapons/m4a1_unsil-1.wav", "weapons/spike2.wav");
	kc_snd_gar = KC_PickSound ("weapons/garand_shoot.wav", "weapons/guncock.wav");
	kc_snd_mm = KC_PickSound ("megaman/mm_fire.wav", "weapons/rocket1i.wav");
};

void() BM_Killcam_SendChoice =
{
	local float v, demo;

	demo = isdemo ();
	if (demo)
		return;
	v = (cvar ("bm_killcam") != 0) ? 1 : 0;
	if (v == kc_cvar_sent && time < kc_cvar_send_t && time > kc_cvar_send_t - 6)
		return;
	kc_cvar_sent = v;
	kc_cvar_send_t = time + 5;
	localcmd (strcat ("cmd bm_killcam ", ftos (v), "\n"));
};

float(float a, float b, float t) KC_LerpAngle =
{
	local float d;

	d = b - a;
	d = d - 360 * rint (d / 360);
	return a + d * t;
};

vector(vector a, vector b) KC_Cross =
{
	local vector out;

	out_x = a_y * b_z - a_z * b_y;
	out_y = a_z * b_x - a_x * b_z;
	out_z = a_x * b_y - a_y * b_x;
	return out;
};

void(float cw, float ch, float st, float spd) DN3SG_DrawFrame;

// Zircon drawline only renders segments where p1_y <= p0_y.
void(float wline, vector p0, vector p1, vector col, float a) KC_Line2D =
{
	if (a <= 0.01)
		return;
	if (p1_y > p0_y)
		drawline (wline, p1, p0, col, a, 0);
	else
		drawline (wline, p0, p1, col, a, 0);
};

entity() KC_EnsureEnt =
{
	local entity e;

	e = spawn ();
	e.classname = "kc_ghost";
	e.drawmask = 0;
	e.alpha = 1;
	e.scale = 1;
	return e;
};

void(float isnew) BM_Killcam_EntUpdate =
{
	local float mask, seq, chunk, bit, f0, cnt, k, f, fl, n_oth, n_prj, i, base;
	local float need_chunks;
	local string kn, wn;
	local vector v;

	self.drawmask = 0;
	mask = ReadShort ();
	seq = ReadByte ();

	if (seq != kc_rx_seq)
	{
		kc_rx_seq = seq;
		kc_rx_chunks = 0;
		kc_rx_nframes = 0;
		kc_rx_ready = FALSE;
		kc_play_started = FALSE;
		if (kc_rx_kname != "")
		{
			strunzone (kc_rx_kname);
			kc_rx_kname = "";
		}
		if (kc_rx_wname != "")
		{
			strunzone (kc_rx_wname);
			kc_rx_wname = "";
		}
	}

	if (mask & 1)
	{
		kc_rx_nframes = bound (1, ReadByte (), KC_C_HIST);
		kc_rx_kill_tick = ReadByte ();
		kn = ReadString ();
		wn = ReadString ();
		kc_rx_kname = strzone (kn);
		kc_rx_wname = strzone (wn);
	}

	bit = 1;
	for (chunk = 0; chunk < 9; chunk = chunk + 1)
	{
		if (mask & bit)
		{
			f0 = ReadByte ();
			cnt = ReadByte ();
			for (k = 0; k < cnt; k = k + 1)
			{
				f = f0 + k;
				if (f >= KC_C_HIST)
					f = KC_C_HIST - 1;

				v_x = ReadCoord ();
				v_y = ReadCoord ();
				v_z = ReadCoord ();
				kc_ck_eye[f] = v;

				v_x = ReadShort () / 64;
				v_y = ReadShort () / 64;
				v_z = 0;
				kc_ck_ang[f] = v;

				kc_ck_vm[f] = ReadShort ();
				kc_ck_vfrm[f] = ReadByte ();
				fl = ReadByte ();
				kc_ck_fl[f] = fl;
				kc_ck_snd[f] = ReadByte ();
				kc_ck_dn3[f] = ReadShort ();

				if (fl & 4)
				{
					v_x = ReadCoord ();
					v_y = ReadCoord ();
					v_z = ReadCoord ();
					kc_ck_org[f] = v;
					kc_ck_yaw[f] = ReadByte () * (360 / 255);
					kc_ck_mdl[f] = ReadShort ();
					kc_ck_frm[f] = ReadByte ();
					kc_ck_skin[f] = ReadByte ();
					kc_ck_col[f] = ReadByte ();
				}
				if (fl & 16)
				{
					v_x = ReadCoord ();
					v_y = ReadCoord ();
					v_z = ReadCoord ();
					kc_ck_tend[f] = v;
				}

				// Victim
				v_x = ReadCoord ();
				v_y = ReadCoord ();
				v_z = ReadCoord ();
				kc_cv_org[f] = v;
				kc_cv_yaw[f] = ReadByte () * (360 / 255);
				kc_cv_mdl[f] = ReadShort ();
				kc_cv_frm[f] = ReadByte ();
				kc_cv_skin[f] = ReadByte ();
				kc_cv_col[f] = ReadByte ();
				kc_cv_alive[f] = ReadByte ();

				// Nearby others
				n_oth = bound (0, ReadByte (), KC_C_OTH);
				kc_co_cnt[f] = n_oth;
				base = f * KC_C_OTH;
				for (i = 0; i < n_oth; i = i + 1)
				{
					v_x = ReadCoord ();
					v_y = ReadCoord ();
					v_z = ReadCoord ();
					kc_co_org[base + i] = v;
					kc_co_yaw[base + i] = ReadByte () * (360 / 255);
					kc_co_mdl[base + i] = ReadShort ();
					kc_co_frm[base + i] = ReadByte ();
					kc_co_skin[base + i] = ReadByte ();
					kc_co_col[base + i] = ReadByte ();
				}

				// Projectiles
				n_prj = bound (0, ReadByte (), KC_C_PROJ);
				kc_cp_cnt[f] = n_prj;
				base = f * KC_C_PROJ;
				for (i = 0; i < n_prj; i = i + 1)
				{
					v_x = ReadCoord ();
					v_y = ReadCoord ();
					v_z = ReadCoord ();
					kc_cp_org[base + i] = v;
					v_x = ReadByte () * (360 / 255);
					v_y = ReadByte () * (360 / 255);
					v_z = 0;
					kc_cp_ang[base + i] = v;
					kc_cp_mdl[base + i] = ReadShort ();
					kc_cp_frm[base + i] = ReadByte ();
					kc_cp_sc[base + i] = ReadByte () / 32;
				}
			}
			kc_rx_chunks = kc_rx_chunks | bit;
		}
		bit = bit * 2;
	}

	if (kc_rx_nframes > 0)
	{
		need_chunks = ceil (kc_rx_nframes / 4);
		if (kc_rx_chunks >= pow (2, need_chunks) - 1)
			kc_rx_ready = TRUE;
	}
};

float() BM_Killcam_IsActive =
{
	local float st, sseq, demo;

	demo = isdemo ();
	if (inMenu || intermission || finale || demo)
	{
		kc_play_started = FALSE;
		return FALSE;
	}
	if (cvar ("bm_killcam") == 0)
	{
		kc_play_started = FALSE;
		return FALSE;
	}
	st = getstati (BMST_KC_ACTIVE);
	sseq = getstati (BMST_KC_SEQ);
	if (st != 2 || !kc_rx_ready || sseq != kc_rx_seq || kc_rx_nframes <= 0)
	{
		if (st == 0)
			kc_play_started = FALSE;
		return FALSE;
	}
	return TRUE;
};

void(float code) KC_PlayFireSnd =
{
	local string s;

	if (code == 1)			s = "weapons/guncock.wav";
	else if (code == 2)		s = "weapons/shotgn2.wav";
	else if (code == 3)		s = "weapons/spike2.wav";
	else if (code == 4)		s = "weapons/grenade.wav";
	else if (code == 5)		s = "weapons/rocket1i.wav";
	else if (code == 6)		s = "weapons/lhit.wav";
	else if (code == 7)		s = "weapons/sgun1.wav";
	else if (code == 8)		s = "weapons/sawatck.wav";
	else if (code == 9)		s = kc_snd_m4;
	else if (code == 10)	s = kc_snd_gar;
	else if (code == 11)	s = kc_snd_mm;
	else					s = "weapons/guncock.wav";
	if (s != "")
		sound (world, CHAN_WEAPON, s, 0.72, ATTN_NONE);
};

// Compute interpolated frame position & trigger discrete shot/hit events
float() KC_EvalTime =
{
	local float elapsed, split_f, u, f;

	elapsed = max (0, time - kc_play_t0);
	if (kc_rx_nframes <= 1)
		return 0;

	split_f = max (0, kc_rx_nframes - 6);
	if (elapsed <= KC_C_TFAST)
		f = (elapsed / KC_C_TFAST) * split_f;
	else
	{
		u = bound (0, (elapsed - KC_C_TFAST) / max (0.05, KC_C_PLAY_SEC - KC_C_TFAST), 1);
		f = split_f + u * (kc_rx_nframes - 1 - split_f);
	}
	return bound (0, f, kc_rx_nframes - 1);
};

void() BM_Killcam_ApplyScene =
{
	local float f, f0, f1, frac, t, i, base, cnt;
	local vector cam_org, cam_ang, porg, pang, a0, a1;
	local entity e;

	if (!kc_play_started || kc_play_seq != kc_rx_seq)
	{
		kc_play_started = TRUE;
		kc_play_seq = kc_rx_seq;
		kc_play_t0 = time;
		kc_last_tick = -1;
		kc_hit_t = 0;
		kc_hit_fatal = FALSE;
		kc_flash_t = 0;
		kc_tracer_t = 0;
		sound (world, CHAN_AUTO, "misc/menu2.wav", 0.55, ATTN_NONE);
	}

	f = KC_EvalTime ();
	f0 = bound (0, floor (f), kc_rx_nframes - 1);
	f1 = min (kc_rx_nframes - 1, f0 + 1);
	frac = f - f0;

	cam_org = kc_ck_eye[f0] * (1 - frac) + kc_ck_eye[f1] * frac;
	a0 = kc_ck_ang[f0];
	a1 = kc_ck_ang[f1];
	cam_ang_x = a0_x * (1 - frac) + a1_x * frac;
	cam_ang_y = KC_LerpAngle (a0_y, a1_y, frac);
	cam_ang_z = 0;
	kc_cur_dn3 = kc_ck_dn3[f0];

	setproperty (VF_ORIGIN, cam_org);
	setproperty (VF_ANGLES, cam_ang);
	setproperty (VF_DRAWCROSSHAIR, FALSE);
	setproperty (VF_DRAWENGINESBAR, FALSE);

	makevectors (cam_ang);

	// Trigger shot / hit events for newly crossed ticks
	if (f0 > kc_last_tick)
	{
		for (t = kc_last_tick + 1; t <= f0; t = t + 1)
		{
			if (kc_ck_fl[t] & 1)
			{
				KC_PlayFireSnd (kc_ck_snd[t]);
				kc_flash_t = time + 0.08;
				kc_flash_org = kc_ck_eye[t] + v_forward * 28;
				if (kc_ck_fl[t] & 16)
				{
					kc_tracer_t = time + 0.11;
					kc_tracer_a = kc_ck_eye[t] + v_forward * 20 - v_up * 5 + v_right * 4;
					kc_tracer_b = kc_ck_tend[t];
				}
			}
			if (kc_ck_fl[t] & 2)
			{
				kc_hit_t = time + 0.24;
				kc_hit_fatal = (t >= kc_rx_kill_tick);
				sound (world, CHAN_ITEM, kc_hit_fatal ? "misc/mmhit3.wav" : "misc/mmhit2.wav", 0.65, ATTN_NONE);
			}
		}
		kc_last_tick = f0;
	}

	if (time < kc_flash_t)
		adddynamiclight (kc_flash_org, 180, '1.1 0.80 0.35');

	// Render 3D tracer beam for hitscan shots
	if (time < kc_tracer_t && vlen (kc_tracer_b - kc_tracer_a) > 8)
	{
		local vector tr_dir, tr_side;
		local float tr_a;

		tr_a = bound (0, (kc_tracer_t - time) / 0.11, 1);
		tr_dir = normalize (kc_tracer_b - kc_tracer_a);
		tr_side = normalize (KC_Cross (tr_dir, v_up)) * 1.1;
		if (vlen (tr_side) < 0.1)
			tr_side = v_right * 1.1;
		R_BeginPolygon ("", 0, FALSE);
		R_PolygonVertex (kc_tracer_a - tr_side, '0 0 0', '1.0 0.92 0.55', 0.55 * tr_a);
		R_PolygonVertex (kc_tracer_a + tr_side, '0 1 0', '1.0 0.92 0.55', 0.55 * tr_a);
		R_PolygonVertex (kc_tracer_b + tr_side, '1 1 0', '1.0 0.65 0.20', 0.85 * tr_a);
		R_PolygonVertex (kc_tracer_b - tr_side, '1 0 0', '1.0 0.65 0.20', 0.85 * tr_a);
		R_EndPolygon ();
	}

	// Killer 1st-person viewmodel (if not in 3P vehicle)
	if (!(kc_ck_fl[f0] & 4) && kc_ck_vm[f0] > 0 && kc_cur_dn3 <= 0)
	{
		if (!kc_ent_vm)
			kc_ent_vm = KC_EnsureEnt ();
		setmodelindex (kc_ent_vm, kc_ck_vm[f0]);
		kc_ent_vm.frame = kc_ck_vfrm[f0];
		kc_ent_vm.skin = 0;
		setorigin (kc_ent_vm, cam_org);
		kc_ent_vm.angles = (0 - cam_ang_x) * '1 0 0' + cam_ang_y * '0 1 0';
		kc_ent_vm.renderflags = KC_RF_DEPTHHACK | KC_RF_WORLDOBJECT;
		addentity (kc_ent_vm);
	}

	// Killer 3rd-person body/vehicle (when driving/flying)
	if ((kc_ck_fl[f0] & 4) && kc_ck_mdl[f0] > 0)
	{
		if (!kc_ent_kbody)
			kc_ent_kbody = KC_EnsureEnt ();
		porg = kc_ck_org[f0] * (1 - frac) + kc_ck_org[f1] * frac;
		pang_x = 0;
		pang_y = KC_LerpAngle (kc_ck_yaw[f0], kc_ck_yaw[f1], frac);
		pang_z = 0;
		setmodelindex (kc_ent_kbody, kc_ck_mdl[f0]);
		setorigin (kc_ent_kbody, porg);
		kc_ent_kbody.angles = pang;
		kc_ent_kbody.frame = kc_ck_frm[f0];
		kc_ent_kbody.skin = kc_ck_skin[f0];
		kc_ent_kbody.colormap = kc_ck_col[f0];
		kc_ent_kbody.renderflags = 0;
		addentity (kc_ent_kbody);
	}

	// Victim ghost (you!)
	if (kc_cv_mdl[f0] > 0)
	{
		if (!kc_ent_victim)
			kc_ent_victim = KC_EnsureEnt ();
		porg = kc_cv_org[f0] * (1 - frac) + kc_cv_org[f1] * frac;
		pang_x = 0;
		pang_y = KC_LerpAngle (kc_cv_yaw[f0], kc_cv_yaw[f1], frac);
		pang_z = 0;
		setmodelindex (kc_ent_victim, kc_cv_mdl[f0]);
		setorigin (kc_ent_victim, porg);
		kc_ent_victim.angles = pang;
		kc_ent_victim.frame = kc_cv_frm[f0];
		kc_ent_victim.skin = kc_cv_skin[f0];
		kc_ent_victim.colormap = kc_cv_col[f0];
		kc_ent_victim.renderflags = 0;
		addentity (kc_ent_victim);
	}

	// Nearby other players
	cnt = kc_co_cnt[f0];
	base = f0 * KC_C_OTH;
	for (i = 0; i < cnt; i = i + 1)
	{
		if (kc_co_mdl[base + i] > 0)
		{
			if (!kc_ent_oth[i])
				kc_ent_oth[i] = KC_EnsureEnt ();
			e = kc_ent_oth[i];
			setmodelindex (e, kc_co_mdl[base + i]);
			setorigin (e, kc_co_org[base + i]);
			e.angles = kc_co_yaw[base + i] * '0 1 0';
			e.frame = kc_co_frm[base + i];
			e.skin = kc_co_skin[base + i];
			e.colormap = kc_co_col[base + i];
			e.renderflags = 0;
			addentity (e);
		}
	}

	// Projectiles
	cnt = kc_cp_cnt[f0];
	base = f0 * KC_C_PROJ;
	for (i = 0; i < cnt; i = i + 1)
	{
		if (kc_cp_mdl[base + i] > 0)
		{
			if (!kc_ent_prj[i])
				kc_ent_prj[i] = KC_EnsureEnt ();
			e = kc_ent_prj[i];
			setmodelindex (e, kc_cp_mdl[base + i]);
			setorigin (e, kc_cp_org[base + i]);
			e.angles = kc_cp_ang[base + i];
			e.frame = kc_cp_frm[base + i];
			e.scale = (kc_cp_sc[base + i] > 0) ? kc_cp_sc[base + i] : 1;
			e.renderflags = 0;
			addentity (e);
		}
	}
};

void(float cw, float ch) BM_Killcam_DrawHUD =
{
	local float cx, cy, prog, hs, top_y, bot_y, pulse, ha, bar_w, sz_hdr, sz_sub;
	local vector hcol;
	local string line2;

	// Draw killer's 2D DN3DooM Pump Shotgun viewmodel if active
	if (kc_cur_dn3 > 0 && !(kc_ck_fl[bound (0, floor (KC_EvalTime ()), kc_rx_nframes - 1)] & 4))
		DN3SG_DrawFrame (cw, ch, kc_cur_dn3, 180);

	// Subtle center crosshair so killer's aim reads clearly
	cx = cw * 0.5;
	cy = ch * 0.5;
	KC_Line2D (1.0, (cx - 4) * '1 0 0' + cy * '0 1 0', (cx - 1.5) * '1 0 0' + cy * '0 1 0', '1 1 1', 0.55);
	KC_Line2D (1.0, (cx + 1.5) * '1 0 0' + cy * '0 1 0', (cx + 4) * '1 0 0' + cy * '0 1 0', '1 1 1', 0.55);
	KC_Line2D (1.0, cx * '1 0 0' + (cy - 4) * '0 1 0', cx * '1 0 0' + (cy - 1.5) * '0 1 0', '1 1 1', 0.55);
	KC_Line2D (1.0, cx * '1 0 0' + (cy + 1.5) * '0 1 0', cx * '1 0 0' + (cy + 4) * '0 1 0', '1 1 1', 0.55);

	// CoD X-hitmarker on hit / fatal blow
	if (time < kc_hit_t)
	{
		ha = bound (0, (kc_hit_t - time) / 0.24, 1);
		hcol = kc_hit_fatal ? '1.0 0.22 0.18' : '1.0 1.0 1.0';
		KC_Line2D (1.5, (cx - 7) * '1 0 0' + (cy - 7) * '0 1 0', (cx - 3) * '1 0 0' + (cy - 3) * '0 1 0', hcol, ha);
		KC_Line2D (1.5, (cx + 7) * '1 0 0' + (cy - 7) * '0 1 0', (cx + 3) * '1 0 0' + (cy - 3) * '0 1 0', hcol, ha);
		KC_Line2D (1.5, (cx - 7) * '1 0 0' + (cy + 7) * '0 1 0', (cx - 3) * '1 0 0' + (cy + 3) * '0 1 0', hcol, ha);
		KC_Line2D (1.5, (cx + 7) * '1 0 0' + (cy + 7) * '0 1 0', (cx + 3) * '1 0 0' + (cy + 3) * '0 1 0', hcol, ha);
	}

	// Corner-only text (no dark overlay boxes, per HUD & Screen Overlay Rule)
	hs = cvar ("bm_hud_style");
	top_y = (hs == 2) ? 62 : ((hs == 3) ? 24 : 34);
	pulse = 0.65 + 0.35 * sin (time * 9);
	sz_hdr = 10;
	sz_sub = 7.5;

	BM_DrawColorShadow (12, top_y, strcat ((pulse > 0.78) ? "^1[REC] " : "^3[REC] ", "^7KILLCAM"), sz_hdr, 0.96);
	line2 = strcat ("^7KILLED BY ^3", (kc_rx_kname != "") ? kc_rx_kname : "Enemy", "  ^8(", (kc_rx_wname != "") ? kc_rx_wname : "Weapon", ")");
	BM_DrawColorShadow (12, top_y + 15, line2, sz_sub, 0.94);

	// Thin 2px progress bar directly below corner text (no box)
	prog = bound (0, (time - kc_play_t0) / KC_C_PLAY_SEC, 1);
	bar_w = 136;
	local vector bpos, bsz_bg, bsz_fg;
	bpos = '12 0 0';
	bpos_y = top_y + 28;
	bsz_bg = '0 2 0';
	bsz_bg_x = bar_w;
	bsz_fg = '0 2 0';
	bsz_fg_x = bar_w * prog;
	drawfill (bpos, bsz_bg, '0.1 0.1 0.1', 0.55, 0);
	drawfill (bpos, bsz_fg, '0.95 0.25 0.20', 0.92, 0);

	// Bottom-left skip hint
	bot_y = ch - 26;
	BM_DrawColorShadow (12, bot_y, "^3[FIRE / JUMP] ^7Skip to Respawn", 7.5, 0.90);
};

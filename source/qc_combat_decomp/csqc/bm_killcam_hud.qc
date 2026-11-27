/*
================
bm_killcam_hud.qc — 3rd-person killer-follow deathcam & corner HUD (CSQC)

Receives lightweight ENT_BM_KILLCAM (10) updates (killer/weapon + smoothed
3rd-person camera pose) and renders at native refresh rate with a clean
corner-only HUD and instant skip prompt.
================
*/

float	ENT_BM_KILLCAM		= 10;
float	BMST_KC_ACTIVE		= 122;		// 0=off, 1=linger, 2=playing
float	BMST_KC_SEQ			= 123;

float	KC_C_PLAY_SEC		= 3.00;

// Client preference sync
float	kc_cvar_sent;
float	kc_cvar_send_t;
float	kc_cvar_retries;

// Received killer-follow state
float	kc_rx_seq;
float	kc_rx_has_pose;
string	kc_rx_kname;
string	kc_rx_wname;
vector	kc_tgt_org;
vector	kc_tgt_ang;

// Smoothed playback state
float	kc_play_started;
float	kc_play_seq;
float	kc_play_t0;
vector	kc_cam_org;
vector	kc_cam_ang;

void() BM_Killcam_Init =
{
	registercvar ("bm_killcam", "1");
	kc_cvar_sent = -1;
	kc_cvar_send_t = 0;
	kc_cvar_retries = 0;
	kc_rx_seq = 0;
	kc_rx_has_pose = FALSE;
	kc_play_started = FALSE;
	kc_rx_kname = "";
	kc_rx_wname = "";
};

void() BM_Killcam_SendChoice =
{
	local float v, demo;

	demo = isdemo ();
	if (demo)
		return;
	v = (cvar ("bm_killcam") != 0) ? 1 : 0;
	if (v != kc_cvar_sent)
	{
		kc_cvar_sent = v;
		kc_cvar_retries = 1;
		kc_cvar_send_t = time + 2;
		localcmd (strcat ("cmd bm_killcam ", ftos (v), "\n"));
		return;
	}
	if (kc_cvar_retries > 0 && (time >= kc_cvar_send_t || time < kc_cvar_send_t - 4))
	{
		kc_cvar_retries = 0;
		localcmd (strcat ("cmd bm_killcam ", ftos (v), "\n"));
	}
};

float(float a, float b, float t) KC_LerpAngle =
{
	local float d;

	d = b - a;
	d = d - 360 * rint (d / 360);
	return a + d * t;
};

void(float isnew) BM_Killcam_EntUpdate =
{
	local float mask, seq;
	local string kn, wn;
	local vector v;

	self.drawmask = 0;
	mask = ReadByte ();
	seq = ReadByte ();

	if (seq != kc_rx_seq)
	{
		kc_rx_seq = seq;
		kc_rx_has_pose = FALSE;
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
		kn = ReadString ();
		wn = ReadString ();
		if (kc_rx_kname != "")
			strunzone (kc_rx_kname);
		if (kc_rx_wname != "")
			strunzone (kc_rx_wname);
		kc_rx_kname = strzone (kn);
		kc_rx_wname = strzone (wn);
	}
	if (mask & 2)
	{
		v_x = ReadCoord ();
		v_y = ReadCoord ();
		v_z = ReadCoord ();
		kc_tgt_org = v;

		v_x = ReadShort () / 64;
		v_y = ReadShort () / 64;
		v_z = 0;
		kc_tgt_ang = v;
		kc_rx_has_pose = TRUE;
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
	if (st != 2 || !kc_rx_has_pose || sseq != kc_rx_seq)
	{
		if (st == 0)
			kc_play_started = FALSE;
		return FALSE;
	}
	return TRUE;
};

void() BM_Killcam_ApplyScene =
{
	local float dt, sp, sa;

	if (!kc_play_started || kc_play_seq != kc_rx_seq)
	{
		kc_play_started = TRUE;
		kc_play_seq = kc_rx_seq;
		kc_play_t0 = time;
		kc_cam_org = kc_tgt_org;
		kc_cam_ang = kc_tgt_ang;
		sound (world, CHAN_AUTO, "misc/menu2.wav", 0.50, ATTN_NONE);
	}
	else
	{
		dt = bound (0.001, frametime, 0.1);
		if (vlen (kc_tgt_org - kc_cam_org) > 500)
		{
			kc_cam_org = kc_tgt_org;
			kc_cam_ang = kc_tgt_ang;
		}
		else
		{
			sp = min (1, dt * 18);
			sa = min (1, dt * 14);
			kc_cam_org = kc_cam_org + (kc_tgt_org - kc_cam_org) * sp;
			kc_cam_ang_x = kc_cam_ang_x + (kc_tgt_ang_x - kc_cam_ang_x) * sa;
			kc_cam_ang_y = KC_LerpAngle (kc_cam_ang_y, kc_tgt_ang_y, sa);
			kc_cam_ang_z = 0;
		}
	}

	setproperty (VF_ORIGIN, kc_cam_org);
	setproperty (VF_ANGLES, kc_cam_ang);
	setproperty (VF_DRAWCROSSHAIR, FALSE);
	setproperty (VF_DRAWENGINESBAR, FALSE);
};

void(float cw, float ch) BM_Killcam_DrawHUD =
{
	local float prog, hs, top_y, bot_y, sn, pulse, bar_w, sz_hdr, sz_sub;
	local string line2;
	local vector bpos, bsz_bg, bsz_fg;

	// Corner-only text (no dark overlay boxes, per HUD & Screen Overlay Rule)
	hs = cvar ("bm_hud_style");
	top_y = (hs == 2) ? 62 : ((hs == 3) ? 24 : 34);
	sn = sin (time * 9);
	pulse = 0.65 + 0.35 * sn;
	sz_hdr = 10;
	sz_sub = 7.5;

	BM_DrawColorShadow (12, top_y, strcat ((pulse > 0.78) ? "^1[CAM] " : "^3[CAM] ", "^7FOLLOWING KILLER"), sz_hdr, 0.96);
	line2 = strcat ("^7KILLED BY ^3", (kc_rx_kname != "") ? kc_rx_kname : "Enemy", "  ^8(", (kc_rx_wname != "") ? kc_rx_wname : "Weapon", ")");
	BM_DrawColorShadow (12, top_y + 15, line2, sz_sub, 0.94);

	prog = bound (0, (time - kc_play_t0) / KC_C_PLAY_SEC, 1);
	bar_w = 136;
	bpos = '12 0 0';
	bpos_y = top_y + 28;
	bsz_bg = '0 2 0';
	bsz_bg_x = bar_w;
	bsz_fg = '0 2 0';
	bsz_fg_x = bar_w * prog;
	drawfill (bpos, bsz_bg, '0.1 0.1 0.1', 0.55, 0);
	drawfill (bpos, bsz_fg, '0.95 0.25 0.20', 0.92, 0);

	bot_y = ch - 26;
	BM_DrawColorShadow (12, bot_y, "^3[FIRE / JUMP] ^7Skip to Respawn", 7.5, 0.90);
};

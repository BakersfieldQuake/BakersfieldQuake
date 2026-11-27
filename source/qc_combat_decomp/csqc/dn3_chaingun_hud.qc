/*
================
DN3DOOM CHAINGUN CANNON (2D CSQC Viewmodel Overlay)
Draws pixel-crisp CGGN* PNG frames using their exact Doom grAb offsets,
figure-8 walk bobbing, raise/reload slide, recoil offsets, and muzzle-flash brightness.
Reads clientstats 122 (dn3_cg_st_frame) and 113 (dn3_st_speed).
================
*/

float BMST_DN3CG_FRAME	= 159;
float BMST_DN3CG_SPEED	= 113;

float dn3cg_bob_phase;
float dn3cg_bob_amp;

void() DN3CG_PrecachePics =
{
	precache_pic("gfx/dn3cg/cggn_a.png");
	precache_pic("gfx/dn3cg/cggn_b.png");
	precache_pic("gfx/dn3cg/cggn_c.png");
	precache_pic("gfx/dn3cg/cggn_d.png");
	precache_pic("gfx/dn3cg/cggn_e.png");
	precache_pic("gfx/dn3cg/cggn_f.png");
	precache_pic("gfx/dn3cg/cggn_g.png");
	precache_pic("gfx/dn3cg/cggn_h.png");
	precache_pic("gfx/dn3cg/cggn_i.png");
	precache_pic("gfx/dn3cg/cggn_j.png");
	precache_pic("gfx/dn3cg/cggn_k.png");
	precache_pic("gfx/dn3cg/cggn_l.png");
	precache_pic("gfx/dn3cg/cggn_m.png");
	precache_pic("gfx/dn3cg/cggn_n.png");
	precache_pic("gfx/dn3cg/cggn_o.png");
	precache_pic("gfx/dn3cg/cggn_p.png");
	precache_pic("gfx/dn3cg/cggn_q.png");
	precache_pic("gfx/dn3cg/cggn_r.png");
	precache_pic("gfx/dn3cg/hud_icon.png");
};

void(float cw, float ch, float st, float spd) DN3CG_DrawFrame =
{
	local float fr, bright, ofs_idx, raise_px;
	local float xofs, yofs, sw, sh, sx, sy, px, py, pw, ph;
	local float target_amp, bx, by, cs, cs2, dt;
	local string pic;
	local vector col;

	fr = st & 31;
	if (fr < 1 || fr > 18)
		return;
	bright = st & 32;
	ofs_idx = floor(st / 64) & 7;
	raise_px = floor(st / 512);

	xofs = 109;
	yofs = 76;
	sw = 211;
	sh = 111;

	if (fr == 1)		pic = "gfx/dn3cg/cggn_a.png";
	else if (fr == 2)	pic = "gfx/dn3cg/cggn_b.png";
	else if (fr == 3)	pic = "gfx/dn3cg/cggn_c.png";
	else if (fr == 4)	pic = "gfx/dn3cg/cggn_d.png";
	else if (fr == 5)	pic = "gfx/dn3cg/cggn_e.png";
	else if (fr == 6)	pic = "gfx/dn3cg/cggn_f.png";
	else if (fr == 7)	pic = "gfx/dn3cg/cggn_g.png";
	else if (fr == 8)	pic = "gfx/dn3cg/cggn_h.png";
	else if (fr == 9)	pic = "gfx/dn3cg/cggn_i.png";
	else if (fr == 10)	pic = "gfx/dn3cg/cggn_j.png";
	else if (fr == 11)	pic = "gfx/dn3cg/cggn_k.png";
	else if (fr == 12)	pic = "gfx/dn3cg/cggn_l.png";
	else if (fr == 13)	pic = "gfx/dn3cg/cggn_m.png";
	else if (fr == 14)	pic = "gfx/dn3cg/cggn_n.png";
	else if (fr == 15)	pic = "gfx/dn3cg/cggn_o.png";
	else if (fr == 16)	pic = "gfx/dn3cg/cggn_p.png";
	else if (fr == 17)	pic = "gfx/dn3cg/cggn_q.png";
	else				pic = "gfx/dn3cg/cggn_r.png";

	dt = frametime;
	if (dt < 0 || dt > 0.1)
		dt = 0.016;
	target_amp = min(1, spd / 320) * 7.5;
	if (fr > 1 && raise_px <= 0)
		target_amp = target_amp * 0.25;
	dn3cg_bob_amp = dn3cg_bob_amp + (target_amp - dn3cg_bob_amp) * min(1, dt * 12);
	dn3cg_bob_phase = dn3cg_bob_phase + dt * 7.5;

	cs = cos(dn3cg_bob_phase);
	cs2 = cos(dn3cg_bob_phase * 2);
	bx = dn3cg_bob_amp * cs;
	by = dn3cg_bob_amp * 0.5 * (1 - cs2);

	if (ofs_idx == 1)		{ bx = bx - 2; by = by - 2; }
	else if (ofs_idx == 2)	{ bx = bx + 1; by = by + 1; }
	else if (ofs_idx == 3)	{ bx = bx - 1; by = by - 1; }
	else if (ofs_idx == 4)	{ bx = bx + 2; by = by + 2; }
	else if (ofs_idx == 5)	{ bx = bx + 1; by = by - 1; }
	else if (ofs_idx == 6)	{ bx = bx - 1; by = by + 1; }

	by = by + raise_px + 2;

	sy = ch / 172;
	sx = sy / 1.15;
	px = cw * 0.5 + ((xofs - 160) + bx) * sx;
	py = (yofs + by) * sy;
	pw = sw * sx;
	ph = sh * sy;

	if (bright)
		col = '1 1 1';
	else
		col = '0.9 0.9 0.9';

	drawpic(px * '1 0 0' + py * '0 1 0', pic, pw * '1 0 0' + ph * '0 1 0', col, 1, 0);
};

void(float cw, float ch) DN3CG_DrawViewmodel =
{
	local float st, spd;

	st = getstati(BMST_DN3CG_FRAME);
	if (st <= 0)
		return;
	if (inMenu || intermission || finale)
		return;
	if (getstati(STAT_HEALTH) <= 0)
		return;
	if (cvar("r_drawviewmodel") <= 0 || cvar("chase_active") > 0)
		return;
	spd = getstati(BMST_DN3CG_SPEED);
	DN3CG_DrawFrame(cw, ch, st, spd);
};

/*
================
DN3DOOM PUMP SHOTGUN (2D CSQC Viewmodel Overlay)
Draws pixel-crisp DSGG* PNG frames using their exact Doom grAb offsets,
figure-8 walk bobbing, raise slide, and muzzle-flash brightness.
Reads clientstats 112 (dn3_st_frame) and 113 (dn3_st_speed).
================
*/

float BMST_DN3SG_FRAME	= 112;
float BMST_DN3SG_SPEED	= 113;

float dn3sg_bob_phase;
float dn3sg_bob_amp;

void() DN3SG_PrecachePics =
{
	precache_pic("gfx/dn3sg/dsgg_a.png");
	precache_pic("gfx/dn3sg/dsgg_b.png");
	precache_pic("gfx/dn3sg/dsgg_c.png");
	precache_pic("gfx/dn3sg/dsgg_d.png");
	precache_pic("gfx/dn3sg/dsgg_e.png");
	precache_pic("gfx/dn3sg/dsgg_f.png");
	precache_pic("gfx/dn3sg/dsgg_g.png");
	precache_pic("gfx/dn3sg/dsgg_h.png");
	precache_pic("gfx/dn3sg/dsgg_i.png");
	precache_pic("gfx/dn3sg/dsgg_j.png");
	precache_pic("gfx/dn3sg/dsgg_k.png");
	precache_pic("gfx/dn3sg/dsgg_m.png");
	precache_pic("gfx/dn3sg/dsgg_n.png");
	precache_pic("gfx/dn3sg/dsgg_o.png");
	precache_pic("gfx/dn3sg/dsgg_q.png");
	precache_pic("gfx/dn3sg/dsgg_r.png");
	precache_pic("gfx/dn3sg/dsgg_s.png");
	precache_pic("gfx/dn3sg/dsgg_t.png");
	precache_pic("gfx/dn3sg/dsgg_u.png");
	precache_pic("gfx/dn3sg/dsgg_v.png");
	precache_pic("gfx/dn3sg/hud_icon.png");
};

void(float cw, float ch) DN3SG_DrawViewmodel =
{
	local float st, fr, ofs_flag, bright, raise_px, spd;
	local float xofs, yofs, sw, sh, sx, sy, px, py, pw, ph;
	local float target_amp, bx, by, cs, cs2, dt;
	local string pic;
	local vector col;

	st = getstati(BMST_DN3SG_FRAME);
	if (st <= 0)
		return;
	if (inMenu || intermission || finale)
		return;
	if (getstati(STAT_HEALTH) <= 0)
		return;
	if (cvar("r_drawviewmodel") <= 0 || cvar("chase_active") > 0)
		return;

	fr = st & 63;
	if (fr < 1 || fr > 20)
		return;
	ofs_flag = st & 64;
	bright = st & 128;
	raise_px = floor(st / 256);

	if (fr == 1)		{ pic = "gfx/dn3sg/dsgg_a.png"; xofs = 167; yofs = 89;  sw = 102; sh = 84;  }
	else if (fr == 2)	{ pic = "gfx/dn3sg/dsgg_b.png"; xofs = 170; yofs = 67;  sw = 118; sh = 131; }
	else if (fr == 3)	{ pic = "gfx/dn3sg/dsgg_c.png"; xofs = 157; yofs = 46;  sw = 160; sh = 136; }
	else if (fr == 4)	{ pic = "gfx/dn3sg/dsgg_d.png"; xofs = 166; yofs = 1;   sw = 160; sh = 175; }
	else if (fr == 5)	{ pic = "gfx/dn3sg/dsgg_e.png"; xofs = 189; yofs = 6;   sw = 134; sh = 172; }
	else if (fr == 6)	{ pic = "gfx/dn3sg/dsgg_f.png"; xofs = 182; yofs = 90;  sw = 102; sh = 100; }
	else if (fr == 7)	{ pic = "gfx/dn3sg/dsgg_g.png"; xofs = 164; yofs = 83;  sw = 118; sh = 131; }
	else if (fr == 8)	{ pic = "gfx/dn3sg/dsgg_h.png"; xofs = 167; yofs = 74;  sw = 118; sh = 131; }
	else if (fr == 9)	{ pic = "gfx/dn3sg/dsgg_i.png"; xofs = 175; yofs = 97;  sw = 102; sh = 84;  }
	else if (fr == 10)	{ pic = "gfx/dn3sg/dsgg_j.png"; xofs = 169; yofs = 94;  sw = 102; sh = 84;  }
	else if (fr == 11)	{ pic = "gfx/dn3sg/dsgg_k.png"; xofs = 147; yofs = 61;  sw = 160; sh = 136; }
	else if (fr == 12)	{ pic = "gfx/dn3sg/dsgg_m.png"; xofs = 158; yofs = 24;  sw = 160; sh = 175; }
	else if (fr == 13)	{ pic = "gfx/dn3sg/dsgg_n.png"; xofs = 160; yofs = 22;  sw = 160; sh = 175; }
	else if (fr == 14)	{ pic = "gfx/dn3sg/dsgg_o.png"; xofs = 161; yofs = 19;  sw = 160; sh = 175; }
	else if (fr == 15)	{ pic = "gfx/dn3sg/dsgg_q.png"; xofs = 159; yofs = 15;  sw = 160; sh = 175; }
	else if (fr == 16)	{ pic = "gfx/dn3sg/dsgg_r.png"; xofs = 157; yofs = 1;   sw = 160; sh = 175; }
	else if (fr == 17)	{ pic = "gfx/dn3sg/dsgg_s.png"; xofs = 157; yofs = 1;   sw = 160; sh = 175; }
	else if (fr == 18)	{ pic = "gfx/dn3sg/dsgg_t.png"; xofs = 157; yofs = 1;   sw = 160; sh = 175; }
	else if (fr == 19)	{ pic = "gfx/dn3sg/dsgg_u.png"; xofs = 158; yofs = 0;   sw = 160; sh = 175; }
	else				{ pic = "gfx/dn3sg/dsgg_v.png"; xofs = 165; yofs = 80;  sw = 118; sh = 131; }

	// Doom/Duke figure-8 walk bob (only bobs downward so wrist never lifts off bottom edge)
	dt = frametime;
	if (dt < 0 || dt > 0.1)
		dt = 0.016;
	spd = getstati(BMST_DN3SG_SPEED);
	target_amp = min(1, spd / 320) * 7.5;
	if (fr > 1 && fr != 1 && raise_px <= 0)
		target_amp = target_amp * 0.25;
	dn3sg_bob_amp = dn3sg_bob_amp + (target_amp - dn3sg_bob_amp) * min(1, dt * 12);
	dn3sg_bob_phase = dn3sg_bob_phase + dt * 7.5;

	cs = cos(dn3sg_bob_phase);
	cs2 = cos(dn3sg_bob_phase * 2);
	bx = dn3sg_bob_amp * cs;
	by = dn3sg_bob_amp * 0.5 * (1 - cs2);

	if (ofs_flag)
	{
		bx = bx - 4;
		by = by - 1;
	}
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

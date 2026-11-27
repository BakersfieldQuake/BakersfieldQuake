#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
DN3DOOM CHAINGUN CANNON (slot 4: IT_NAILGUN)
Faithful 35 Hz rotary CGGN* animation, sounds, zoom/pitch tremor,
gold tracers, smoke, brass casings, and wall impact sparks/ricochets.
================
*/

float dn3cg_fx_casing;

void() DN3CG_Precache =
{
	precache_sound ("dn3cg/fire.wav");
	precache_sound ("dn3cg/select.wav");
	precache_sound ("dn3cg/dryfire.wav");
	dn3cg_fx_casing = particleeffectnum ("dn3cg_casing");
};

void() DN3CG_Reset =
{
	self.dn3_cg_active = 0;
	self.dn3_cg_draw_t = 0;
	self.dn3_cg_draw_snd = 0;
	self.dn3_cg_fire_t = 0;
	self.dn3_cg_step = 0;
	self.dn3_cg_spindown_t = 0;
	self.dn3_cg_st_frame = 0;
	if (self.viewzoom > 1.0 && !Binoc_On (self))
		self.viewzoom = 0;
};

float(entity p) DN3CG_IsHidden =
{
	if (p.health <= 0 || p.deadflag != DEAD_NO)
		return TRUE;
	if (p.weapon != IT_NAILGUN)
		return TRUE;
	if (p.meleeing || p.throwing)
		return TRUE;
	if (p.veh_van != world || p.veh_ride != world || p.jb_vehicle != world || p.rr_vehicle != world || MMTank_Driving (p) || FD_Flying (p) || EricCannon_Active (p))
		return TRUE;
	return FALSE;
};

float() DN3CG_CanFire =
{
	local float mag;

	if (autocvar_bm_reload)
		mag = BM_GetMag (self, BM_NG);
	else
		mag = self.ammo_nails;

	if (mag < 1)
	{
		sound7 (self, CHAN_WEAPON, "dn3cg/dryfire.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
		self.attack_finished = time + 0.285;
		if (autocvar_bm_reload)
		{
			self.bm_rl_quiet = FALSE;
			BM_StartReload (BM_NG);
		}
		return FALSE;
	}

	if (self.bm_rl_slot == BM_NG)
	{
		self.bm_rl_slot = 0;
		self.bm_rl_quiet = FALSE;
	}
	return TRUE;
};

void() DN3CG_Fire =
{
	local vector dir, eye, src, tracer_org, muzz, direction;
	local vector shotvector, align;
	local float mag, crit, continuous;
	local entity shot;

	makevectors (self.v_angle);
	sound7 (self, CHAN_WEAPON, "dn3cg/fire.wav", 1, ATTN_NORM, self.PLR_SNDSPD);

	continuous = (self.dn3_cg_fire_t > 0 && (time - self.dn3_cg_fire_t) < 0.11);
	if (continuous)
	{
		self.dn3_cg_step = self.dn3_cg_step + 1;
		if (self.dn3_cg_step > 6)
			self.dn3_cg_step = 1;
	}
	else
	{
		self.dn3_cg_step = 0;
	}
	self.dn3_cg_fire_t = time;
	self.dn3_cg_spindown_t = 0;
	self.effects = self.effects | EF_MUZZLEFLASH;

	muzz = self.origin + self.view_ofs + (v_forward * 22) + (v_right * 2) + (v_up * -7);
	if (autocvar_muzzleflash == 1)
		sendParticle ("shotgun_muzzleflash", muzz, self.velocity * 50, 1, 0);
	if (self.waterlevel >= 3)
		Sprite_Emitter (self, "progs/s_bubble.spr", 2, '22 -8 -16', '280 20 -10', '25 18 10', 0.7, TYPE_SMOKE);

	// Vertical pitch tremor & subtle 0.98 zoom pulse (zero left/right roll)
	if (autocvar_effects_explosion_shake != 0)
	{
		self.viewzoom = 1.0204;
		self.punchangle_x = -0.9;
	}

	if (dn3cg_fx_casing >= 0 && autocvar_shellcasing != 0)
		pointparticles (dn3cg_fx_casing, muzz + (v_right * 8) + (v_up * 2), (v_right * 140) + (v_up * 95) + (v_forward * 25), 1);

	// Spend 1 belt round
	if (autocvar_bm_reload)
	{
		mag = max (0, BM_GetMag (self, BM_NG) - 1);
		BM_SetMag (self, BM_NG, mag);
		self.ammo_nails = mag;
		self.bm_shown_n = mag;
		self.currentammo = mag;
		self.bm_lastshot = time;
	}
	else
	{
		self.ammo_nails = max (0, self.ammo_nails - 1);
		self.currentammo = self.ammo_nails;
	}

	// Hitscan bullet with DN3DooM 3.5 x 3.0 degree spread
	eye = self.origin + self.view_ofs;
	traceline (eye, eye + (v_forward * 10), TRUE, self);
	src = (trace_fraction < 1) ? (eye + (v_forward * max (0, (trace_fraction * 10) - 1))) : (eye + (v_forward * 10));
	tracer_org = self.origin + self.view_ofs + (v_forward * 18) + (v_right * 2) + (v_up * -8);

	dir = aim (self, 100000);
	direction = normalize (dir + (crandom () * 0.061 * v_right) + (crandom () * 0.052 * v_up));

	crit = (random () <= 0.01) ? 1 : 0;
	ClearMultiDamage ();
	Antilag_Rewind (self);
	traceline (src, src + (direction * 2048), FALSE, self);
	Antilag_Restore ();

	if (dn3sg_fx_tracer >= 0 && trace_fraction > 0.02)
		trailparticles (self, dn3sg_fx_tracer, tracer_org, trace_endpos);

	if (!PC_TraceIntercept (self, src, trace_endpos, DN3CG_BULLET_DMG + crit))
	{
		if (trace_fraction != 1)
		{
			if (trace_ent.takedamage || trace_ent.inflamed == 1)
				TraceAttack (DN3CG_BULLET_DMG + crit, direction);
			else
				DN3SG_WallImpact (direction);
		}
	}

	if (autocvar_gyroset != 0 || gyro_objectlist_head)
	{
		align = direction + (v_up * 0.2);
		traceline (self.origin, self.origin + (align * 180), FALSE, self);
		shotvector = (trace_endpos - self.origin) + (direction * 60);
		shot = Gyro_Force_Create ("gunshot", self.origin);
		Gyro_Force_ApplyFalloff_ConeLinear (shot, shotvector, 14, 14);
		Gyro_Force_ApplyAffector_Directional (shot, shotvector, 70, FALSE);
		Gyro_Force_AddProperty_Instant (shot);
		Gyro_Force_Ignore (shot, self);
	}
	W_BulletSplash (direction);
	ApplyMultiDamage ();
};

// Encode packed CSQC state: frame (1..18) + bright*32 + ofs_idx*64
float(float step, float dt, float held) DN3CG_FireFrame =
{
	local float t;

	t = floor (dt / DN3CG_TIC);
	if (step == 0)
	{
		if (t == 0)		return 2  | 32 | (1 * 64);	// B bright (-2,-2)
		if (t == 1)		return 12 | 32 | (1 * 64);	// L bright (-2,-2)
		if (held)		return 3  | 32 | (2 * 64);	// C bridge (+1,+1)
		if (t < 4)		return 3  |      (2 * 64);	// C (+1,+1)
		if (t < 6)		return 11;					// K (0,0)
		return 1;									// A ready
	}
	if (step == 1)
	{
		if (t == 0)		return 4  | 32 | (3 * 64);	// D bright (-1,-1)
		return 13 | 32 | (3 * 64);					// M bright (-1,-1)
	}
	if (step == 2)
	{
		if (t == 0)		return 5  | 32 | (4 * 64);	// E bright (+2,+2)
		return 6  | 32 | (4 * 64);					// F bright (+2,+2)
	}
	if (step == 3)
	{
		if (t == 0)		return 7  | 32;				// G bright (0,0)
		return 14 | 32;								// N bright (0,0)
	}
	if (step == 4)
	{
		if (t == 0)		return 3  | 32;				// C bright (0,0)
		return 15 | 32 | (1 * 64);					// O bright (-2,-2)
	}
	if (step == 5)
	{
		if (t == 0)		return 16 | 32 | (1 * 64);	// P bright (-2,-2)
		return 17 | 32 | (2 * 64);					// Q bright (+1,+1)
	}
	// step == 6
	if (t == 0)			return 18 | 32 | (2 * 64);	// R bright (+1,+1)
	return 8 | 32;									// H bright (0,0)
};

void() DN3CG_Frame =
{
	local float f, dt, raise_px, total, u;
	local vector vxy;

	if (self.weapon != IT_NAILGUN)
	{
		if (self.dn3_cg_active)
		{
			self.dn3_cg_active = 0;
			self.dn3_cg_spindown_t = 0;
			self.dn3_cg_st_frame = 0;
			if (self.viewzoom > 1.0 && !Binoc_On (self))
				self.viewzoom = 0;
		}
		return;
	}

	if (!self.dn3_cg_active)
	{
		self.dn3_cg_active = 1;
		self.dn3_cg_draw_t = time;
		self.dn3_cg_draw_snd = 0;
		self.dn3_cg_step = 0;
		self.dn3_cg_spindown_t = 0;
		self.weaponmodel = "";
	}
	else if (self.weaponmodel != "")
	{
		self.weaponmodel = "";
	}

	// Equip click once when drawn
	if (!self.dn3_cg_draw_snd && self.ishuman == 1 && !DN3CG_IsHidden (self))
	{
		self.dn3_cg_draw_snd = 1;
		sound7 (self, CHAN_ITEM, "dn3cg/select.wav", 0.8, ATTN_NORM, self.PLR_SNDSPD);
	}

	// Reset subtle 0.98 zoom pulse after 1 tic
	if (self.dn3_cg_fire_t > 0 && (time - self.dn3_cg_fire_t) >= DN3CG_TIC)
	{
		if (self.viewzoom > 1.01 && self.viewzoom < 1.04)
			self.viewzoom = 0;
	}

	// Trigger glowing H->I->J spindown when releasing after rotary spin
	if (self.dn3_cg_step >= 1 && self.dn3_cg_spindown_t == 0 && (time - self.dn3_cg_fire_t) >= (2.5 * DN3CG_TIC))
	{
		self.dn3_cg_spindown_t = time;
	}
	if (self.dn3_cg_spindown_t > 0 && (time - self.dn3_cg_spindown_t) >= (6 * DN3CG_TIC))
	{
		self.dn3_cg_spindown_t = 0;
		self.dn3_cg_step = 0;
	}

	if (self.ishuman != 1)
		return;

	if (DN3CG_IsHidden (self))
	{
		self.dn3_cg_st_frame = 0;
		return;
	}

	// Pick current CGGN sprite frame + flags
	f = 1;
	if (self.dn3_cg_spindown_t > 0)
	{
		dt = floor ((time - self.dn3_cg_spindown_t) / DN3CG_TIC);
		if (dt < 2)			f = 8  | 32;			// H bright (0,0)
		else if (dt < 4)	f = 9  | 32 | (5 * 64);	// I bright (+1,-1)
		else				f = 10 | 32;			// J bright (0,0)
	}
	else if (self.dn3_cg_fire_t > 0)
	{
		dt = time - self.dn3_cg_fire_t;
		if (self.dn3_cg_step == 0 && dt < (6 * DN3CG_TIC))
			f = DN3CG_FireFrame (0, dt, self.button0);
		else if (self.dn3_cg_step >= 1 && dt < (3 * DN3CG_TIC))
			f = DN3CG_FireFrame (self.dn3_cg_step, dt, self.button0);
	}

	// Slide offset: draw raise + belt reload lower/raise animation
	raise_px = 0;
	if (self.bm_rl_slot == BM_NG && !self.bm_rl_quiet && self.bm_rl_end > self.bm_rl_start)
	{
		total = self.bm_rl_end - self.bm_rl_start;
		u = (time - self.bm_rl_start) / total;
		if (u < 0) u = 0;
		if (u > 1) u = 1;
		if (u < 0.2)
			raise_px = floor (62 * (u / 0.2));
		else if (u > 0.8)
			raise_px = floor (62 * ((1 - u) / 0.2));
		else
			raise_px = 62;
	}
	else
	{
		dt = time - self.dn3_cg_draw_t;
		if (dt < DN3CG_DRAW_TIME)
			raise_px = floor (48 * (1 - dt / DN3CG_DRAW_TIME));
	}
	if (raise_px < 0)
		raise_px = 0;
	if (raise_px > 63)
		raise_px = 63;

	self.dn3_cg_st_frame = f + (raise_px * 512);

	if (self.flags & FL_ONGROUND)
	{
		vxy = self.velocity;
		vxy_z = 0;
		self.dn3_st_speed = min (600, floor (vlen (vxy) / 16) * 16);
	}
	else
		self.dn3_st_speed = 0;
};

#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
DN3DOOM PUMP SHOTGUN (replaces IT_SUPER_SHOTGUN slot 3)
Faithful 35 Hz DSGG animation, sounds, zoom/pitch kick, tracers, smoke,
shell-by-shell tilt reload, and 45 u/s directional recoil pushback.
================
*/

float dn3sg_fx_tracer;
float dn3sg_fx_hole;
float dn3sg_fx_spark;

void() DN3SG_Precache =
{
	precache_sound ("dn3sg/fire.wav");
	precache_sound ("dn3sg/pump.wav");
	precache_sound ("dn3sg/shell.wav");
	precache_sound ("dn3sg/dryfire.wav");

	dn3sg_fx_tracer = particleeffectnum ("dn3sg_tracer");
	dn3sg_fx_hole = particleeffectnum ("m4_hole");
	dn3sg_fx_spark = particleeffectnum ("m4_spark");
};

void() DN3SG_Reset =
{
	self.dn3_sg_active = 0;
	self.dn3_sg_draw_t = 0;
	self.dn3_sg_draw_snd = 0;
	self.dn3_sg_fire_t = 0;
	self.dn3_sg_pump_done = 1;
	self.dn3_sg_kick_step = 5;
	self.dn3_sg_rl_phase = 0;
	self.dn3_sg_rl_t = 0;
	self.dn3_sg_rl_snd = 0;
	self.dn3_st_frame = 0;
	self.dn3_st_speed = 0;
	if (self.viewzoom > 1.0 && !Binoc_On (self))
		self.viewzoom = 0;
};

float(entity p) DN3SG_IsHidden =
{
	if (p.health <= 0 || p.deadflag != DEAD_NO)
		return TRUE;
	if (p.weapon != IT_SUPER_SHOTGUN)
		return TRUE;
	if (p.meleeing || p.throwing)
		return TRUE;
	if (p.veh_van != world || p.veh_ride != world || p.jb_vehicle != world || p.rr_vehicle != world || MMTank_Driving (p) || FD_Flying (p) || EricCannon_Active (p))
		return TRUE;
	return FALSE;
};

float() DN3SG_CanFire =
{
	local float mag;

	if (autocvar_bm_reload)
		mag = BM_GetMag (self, BM_SSG);
	else
		mag = self.ammo_shells;

	if (mag < 1)
	{
		sound7 (self, CHAN_WEAPON, "dn3sg/dryfire.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
		self.attack_finished = time + 0.285;
		if (autocvar_bm_reload)
		{
			self.bm_rl_quiet = FALSE;
			DN3SG_StartReload ();
		}
		return FALSE;
	}

	// Firing mid-reload cancels the tilt-reload immediately so you can shoot loaded shells
	if (self.dn3_sg_rl_phase > 0)
	{
		self.dn3_sg_rl_phase = 0;
		self.dn3_sg_rl_snd = 0;
		if (self.bm_rl_slot == BM_SSG)
		{
			self.bm_rl_slot = 0;
			self.bm_rl_quiet = FALSE;
		}
	}
	return TRUE;
};

void(vector dir) DN3SG_WallImpact =
{
	if (pointcontents (trace_endpos) == CONTENT_SKY || pointcontents (trace_endpos + dir * 2) == CONTENT_SKY || pointcontents (trace_endpos - dir * 2) == CONTENT_SKY)
		return;

	if (dn3sg_fx_hole >= 0)
		pointparticles (dn3sg_fx_hole, trace_endpos, VEC_ORIGIN, 1);
	if (dn3sg_fx_spark >= 0)
		pointparticles (dn3sg_fx_spark, trace_endpos + trace_plane_normal * 1.5, trace_plane_normal * 85, 1);
	else
		sendParticle ("TE_GUNSHOT", trace_endpos - dir * 1, VEC_ORIGIN, 1, 0);
	DN3FX_OnWallImpact (trace_endpos + trace_plane_normal * 1.5, trace_plane_normal);
};

void(float shotcount, vector dir, vector spread, float pdmg) DN3SG_FirePellets =
{
	local vector eye, src, tracer_org;
	local vector direction;
	local float crit, i;
	local entity shot;
	local vector shotvector, align;

	makevectors (self.v_angle);
	if (cvar ("slowmo") < 0.9 || autocvar_bullet_projectiles == 1 || self.waterlevel >= 3)
	{
		FireBullets_Projectile ();
		return;
	}

	eye = self.origin + self.view_ofs;
	traceline (eye, eye + (v_forward * 10), TRUE, self);
	src = (trace_fraction < 1) ? (eye + (v_forward * max (0, (trace_fraction * 10) - 1))) : (eye + (v_forward * 10));
	tracer_org = self.origin + self.view_ofs + (v_forward * 18) + (v_right * 4) + (v_up * -7);
	crit = 0;
	if (random () <= 0.01)
		crit = 1;

	ClearMultiDamage ();
	Antilag_Rewind (self);
	i = 0;
	while (i < shotcount)
	{
		direction = normalize (dir + (crandom () * spread_x * v_right) + (crandom () * spread_y * v_up));
		traceline (src, src + (direction * 2048), FALSE, self);
		if (i < 5 && dn3sg_fx_tracer >= 0 && trace_fraction > 0.02)
			trailparticles (self, dn3sg_fx_tracer, tracer_org, trace_endpos);

		if (!PC_TraceIntercept (self, src, trace_endpos, pdmg + crit))
		{
			if (trace_fraction != 1)
			{
				if (trace_ent.takedamage || trace_ent.inflamed == 1)
					TraceAttack (pdmg + crit, direction);
				else
					DN3SG_WallImpact (direction);
			}
		}

		i = i + 1;
	}
	Antilag_Restore ();
	if (autocvar_gyroset != 0 || gyro_objectlist_head)
	{
		align = dir + (v_up * 0.25);
		traceline (self.origin, self.origin + (align * 200), FALSE, self);
		shotvector = (trace_endpos - self.origin) + (normalize (dir) * 80);
		shot = Gyro_Force_Create ("gunshot", self.origin);
		Gyro_Force_ApplyFalloff_ConeLinear (shot, shotvector, 18, 18);
		Gyro_Force_ApplyAffector_Directional (shot, shotvector, 95, FALSE);
		Gyro_Force_AddProperty_Instant (shot);
		Gyro_Force_Ignore (shot, self);
	}
	W_BulletSplash (dir);
	ApplyMultiDamage ();
};

void() DN3SG_Fire =
{
	local vector dir, direc, muzz;
	local float mag;

	makevectors (self.v_angle);
	sound7 (self, CHAN_WEAPON, "dn3sg/fire.wav", 1, ATTN_NORM, self.PLR_SNDSPD);

	self.effects = self.effects | EF_MUZZLEFLASH;
	self.dn3_sg_fire_t = time;
	self.dn3_sg_pump_done = 0;
	self.dn3_sg_kick_step = 0;

	// World muzzle flash & gun smoke (no 3D viewmodel flash sprite since CSQC 2D DSGGI/F draws it)
	muzz = self.origin + self.view_ofs + (v_forward * 20) + (v_right * 4) + (v_up * -7);
	if (autocvar_muzzleflash == 1)
		sendParticle ("shotgun_muzzleflash", muzz, self.velocity * 50, 1, 0);
	SpawnSmoke_Flash (1, '8 5 12', 1, '0.5 0.5 0.5', 0.5);
	if (self.waterlevel >= 3)
	{
		Sprite_Emitter (self, "progs/s_bubble.spr", 2, '20 -13 -20', '320 30 -10', '25 18 10', 0.7, TYPE_SMOKE);
		Sprite_Emitter (self, "progs/s_bubble.spr", 2, '20 -13 -20', '150 -10 -30', '25 18 10', 0.7, TYPE_SMOKE);
	}

	// DN3DooM zoom snap (0.95 -> viewzoom = 1/0.95) & initial punch
	if (autocvar_effects_explosion_shake != 0)
	{
		self.viewzoom = 1.0526;
		self.punchangle_x = -2.2;
	}

	// Directional pushback opposite where you shoot (45 u/s)
	if (autocvar_pushback != 0)
	{
		direc = aim (self, 100);
		self.velocity = self.velocity - (direc * DN3SG_PUSHBACK);
	}

	// Spend 1 shell
	if (autocvar_bm_reload)
	{
		mag = max (0, BM_GetMag (self, BM_SSG) - 1);
		BM_SetMag (self, BM_SSG, mag);
		self.ammo_shells = mag;
		self.bm_shown_s = mag;
		self.currentammo = mag;
		self.bm_lastshot = time;
	}
	else
	{
		self.ammo_shells = max (0, self.ammo_shells - 1);
		self.currentammo = self.ammo_shells;
	}

	dir = aim (self, 100000);
	DN3SG_FirePellets (DN3SG_PELLETS, dir, '0.063 0.063 0', DN3SG_PELLET_DMG);
};

void() DN3SG_StartReload =
{
	local float mag, size, loops, total;

	if (self.dn3_sg_rl_phase > 0)
		return;
	if (!autocvar_bm_reload)
		return;
	size = BM_MagSize (BM_SSG);
	mag = BM_GetMag (self, BM_SSG);
	if (mag >= size)
		return;

	// If still mid-pump right after firing, wait for pump to finish unless empty
	if (self.dn3_sg_fire_t > 0 && (time - self.dn3_sg_fire_t) < DN3SG_REFIRE && mag > 0)
		return;

	loops = ceil ((size - mag) * 0.5);
	if (loops < 1)
		loops = 1;
	total = (8 * DN3SG_TIC) + (loops * 7 * DN3SG_TIC) + (8 * DN3SG_TIC);
	if (autocvar_bm_reload_scale > 0)
		total = total * autocvar_bm_reload_scale;

	self.bm_rl_slot = BM_SSG;
	self.bm_rl_start = time;
	self.bm_rl_end = time + total;

	if (self.bm_rl_quiet)
	{
		self.dn3_sg_rl_phase = 0;
		return;
	}

	self.dn3_sg_rl_phase = 1;
	self.dn3_sg_rl_t = time;
	self.dn3_sg_rl_snd = 0;
};

// Map fire elapsed tics (0..30) to DSGG frame + flags
// DSGG index: 1=A 2=B 3=C 4=D 5=E 6=F 7=G 8=H 9=I 10=J 11=K 12=M 13=N 14=O 15=Q 16=R 17=S 18=T 19=U 20=V
float(float dt) DN3SG_FireFrame =
{
	local float t;

	t = floor (dt / DN3SG_TIC);
	if (t < 2)		return 9 | 128;			// I (bright)
	if (t < 4)		return 6 | 128;			// F (bright)
	if (t < 7)		return 7;				// G
	if (t < 9)		return 8;				// H
	if (t < 12)		return 2 | 64;			// B offset(-4, 31)
	if (t < 15)		return 3;				// C
	if (t < 18)		return 4;				// D
	if (t < 22)		return 5;				// E (pump + shell eject)
	if (t < 25)		return 4;				// D
	if (t < 28)		return 3;				// C
	if (t < 31)		return 2;				// B
	return 1;								// A
};

float(float phase, float dt) DN3SG_ReloadFrame =
{
	local float t;

	t = floor (dt / DN3SG_TIC);
	if (phase == 1)
	{
		// J(1), V(1), K(1), M(1), N(1), O(1), Q(1), R(1)
		if (t == 0) return 10;
		if (t == 1) return 20;
		if (t == 2) return 11;
		if (t == 3) return 12;
		if (t == 4) return 13;
		if (t == 5) return 14;
		if (t == 6) return 15;
		return 16;
	}
	if (phase == 2)
	{
		// S(2), T(1), U(2), R(2)
		if (t < 2) return 17;
		if (t < 3) return 18;
		if (t < 5) return 19;
		return 16;
	}
	// Phase 3 finish: R(1), M(2), K(2), J(3)
	if (t < 1) return 16;
	if (t < 3) return 12;
	if (t < 5) return 11;
	return 10;
};

void() DN3SG_Frame =
{
	local float f, dt, mag, size, raise_px;
	local vector vxy;

	if (self.weapon != IT_SUPER_SHOTGUN)
	{
		if (self.dn3_sg_active)
		{
			self.dn3_sg_active = 0;
			self.dn3_sg_rl_phase = 0;
			self.dn3_st_frame = 0;
			self.dn3_st_speed = 0;
			if (self.viewzoom > 1.0 && !Binoc_On (self))
				self.viewzoom = 0;
		}
		return;
	}

	if (!self.dn3_sg_active)
	{
		self.dn3_sg_active = 1;
		self.dn3_sg_draw_t = time;
		self.dn3_sg_draw_snd = 0;
		self.dn3_sg_rl_phase = 0;
		self.weaponmodel = "";
	}
	else if (self.weaponmodel != "")
	{
		self.weaponmodel = "";
	}

	// Equip pump sound once when drawn
	if (!self.dn3_sg_draw_snd && self.ishuman == 1 && !DN3SG_IsHidden (self))
	{
		self.dn3_sg_draw_snd = 1;
		sound7 (self, CHAN_ITEM, "dn3sg/pump.wav", 0.75, ATTN_NORM, self.PLR_SNDSPD);
	}

	// Post-fire zoom reset, pitch-kick curve, and delayed pump sound + casing
	if (self.dn3_sg_fire_t > 0)
	{
		dt = time - self.dn3_sg_fire_t;
		if (dt >= DN3SG_FLASH_END && self.viewzoom > 1.01 && self.viewzoom < 1.1)
			self.viewzoom = 0;

		if (autocvar_effects_explosion_shake != 0)
		{
			if (self.dn3_sg_kick_step == 0 && dt >= 4 * DN3SG_TIC)
			{
				self.dn3_sg_kick_step = 1;
				self.punchangle_x = -2.0;
			}
			else if (self.dn3_sg_kick_step == 1 && dt >= 7 * DN3SG_TIC)
			{
				self.dn3_sg_kick_step = 2;
				self.punchangle_x = 0.8;
			}
			else if (self.dn3_sg_kick_step == 2 && dt >= 8 * DN3SG_TIC)
			{
				self.dn3_sg_kick_step = 3;
				self.punchangle_x = 0.6;
			}
			else if (self.dn3_sg_kick_step == 3 && dt >= 9 * DN3SG_TIC)
			{
				self.dn3_sg_kick_step = 4;
				self.punchangle_x = 0.4;
			}
			else if (self.dn3_sg_kick_step == 4 && dt >= 10 * DN3SG_TIC)
			{
				self.dn3_sg_kick_step = 5;
				self.punchangle_x = 0.2;
			}
		}

		if (!self.dn3_sg_pump_done && dt >= DN3SG_PUMP_AT)
		{
			self.dn3_sg_pump_done = 1;
			sound7 (self, CHAN_AUTO, "dn3sg/pump.wav", 0.9, ATTN_NORM, self.PLR_SNDSPD);
			makevectors (self.v_angle);
			casing (0);
		}
	}

	// Auto-start reload right after pump completes if mag is 0
	if (autocvar_bm_reload && self.dn3_sg_rl_phase == 0 && self.bm_rl_slot == 0)
	{
		mag = BM_GetMag (self, BM_SSG);
		if (mag < 1 && (self.dn3_sg_fire_t <= 0 || (time - self.dn3_sg_fire_t) >= DN3SG_REFIRE))
		{
			self.bm_rl_quiet = FALSE;
			DN3SG_StartReload ();
		}
	}

	// Reload state machine (8-tic tilt-in -> 7-tic shell insert loop -> 8-tic tilt-out)
	if (self.dn3_sg_rl_phase > 0)
	{
		if (self.bm_rl_slot != BM_SSG || self.health <= 0)
		{
			self.dn3_sg_rl_phase = 0;
		}
		else
		{
			size = BM_MagSize (BM_SSG);
			mag = BM_GetMag (self, BM_SSG);
			// Interruptible by +attack once at least 1 shell is in the tube
			if (self.button0 && mag >= 1 && self.dn3_sg_rl_phase < 3 && (time - self.bm_rl_start) > 0.12)
			{
				self.dn3_sg_rl_phase = 0;
				self.bm_rl_slot = 0;
				self.bm_rl_quiet = FALSE;
				self.attack_finished = time;
			}
			else if (self.dn3_sg_rl_phase == 1)
			{
				dt = time - self.dn3_sg_rl_t;
				if (dt >= 8 * DN3SG_TIC)
				{
					self.dn3_sg_rl_phase = 2;
					self.dn3_sg_rl_t = time;
					self.dn3_sg_rl_snd = 0;
				}
			}
			else if (self.dn3_sg_rl_phase == 2)
			{
				dt = time - self.dn3_sg_rl_t;
				if (!self.dn3_sg_rl_snd && dt >= 3 * DN3SG_TIC)
				{
					self.dn3_sg_rl_snd = 1;
					sound7 (self, CHAN_AUTO, "dn3sg/shell.wav", 0.9, ATTN_NORM, self.PLR_SNDSPD);
					mag = min (size, mag + 2);
					BM_SetMag (self, BM_SSG, mag);
					BM_WriteFields ();
				}
				if (dt >= 7 * DN3SG_TIC)
				{
					if (mag < size)
					{
						self.dn3_sg_rl_t = time;
						self.dn3_sg_rl_snd = 0;
					}
					else
					{
						self.dn3_sg_rl_phase = 3;
						self.dn3_sg_rl_t = time;
					}
				}
			}
			else if (self.dn3_sg_rl_phase == 3)
			{
				dt = time - self.dn3_sg_rl_t;
				if (dt >= 8 * DN3SG_TIC)
				{
					self.dn3_sg_rl_phase = 0;
					self.bm_rl_slot = 0;
					self.bm_rl_quiet = FALSE;
				}
			}
		}
	}

	if (self.ishuman != 1)
		return;

	if (DN3SG_IsHidden (self))
	{
		self.dn3_st_frame = 0;
		self.dn3_st_speed = 0;
		return;
	}

	// Pick current DSGG sprite frame
	f = 1;
	if (self.dn3_sg_rl_phase > 0)
		f = DN3SG_ReloadFrame (self.dn3_sg_rl_phase, time - self.dn3_sg_rl_t);
	else if (self.dn3_sg_fire_t > 0 && (time - self.dn3_sg_fire_t) < (31 * DN3SG_TIC))
		f = DN3SG_FireFrame (time - self.dn3_sg_fire_t);

	raise_px = 0;
	dt = time - self.dn3_sg_draw_t;
	if (dt < DN3SG_DRAW_TIME)
		raise_px = floor (48 * (1 - dt / DN3SG_DRAW_TIME));
	if (raise_px < 0)
		raise_px = 0;
	if (raise_px > 63)
		raise_px = 63;

	self.dn3_st_frame = f + (raise_px * 256);

	if (self.flags & FL_ONGROUND)
	{
		vxy = self.velocity;
		vxy_z = 0;
		self.dn3_st_speed = min (600, floor (vlen (vxy) / 16) * 16);
	}
	else
		self.dn3_st_speed = 0;
};

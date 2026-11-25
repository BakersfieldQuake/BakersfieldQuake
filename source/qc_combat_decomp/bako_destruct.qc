#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
BAKERSFIELD-ISH DESTRUCTIBLE LANDMARKS, ROLLING BOULDERS & SHATTERABLE GLASS (bako_destruct.qc)

Round 3 Cinema-Grade Systems:
  1. Continuous 60 Hz smooth damped-sine camera shake (Bako_TickSmoothShake in BakoDestruct_Frame)
     with strict per-frame slew clamp (<= 0.45 deg/frame) and hard bounds (pitch <= +-3.0,
     roll <= +-2.0, yaw <= +-0.6) -> ZERO single-frame whip snaps!
  2. 100% bulletproof rooftop entity hider/restorer (dynamic footprint scan + setmodel("") +
     EF_NODRAW + traileffectnum=0 + paused nextthink enforced every tick) -> ZERO floating items!
  3. Historic Fox Theater: coupled 2-piece clock tower kinematics (tower_upper welded to
     tower_lower's live rotated top collar via exact Zircon makevectors math, shearing forward
     past ~28 deg) -> ~8.6s collapse with localized dust-veiled finish on EVERY piece -> clean
     zero-tilt bottom-up 25s rebuild with continuous golden welding sparks & bell chime lock-in.
  4. The Padre Hotel: visible outer-facade 75/50/25% dark-grey window smoke vents + top-right
     corner HUD -> 10 crisp 1F-3F perimeter charge pops (0.05..2.05s) -> coupled 12s inward
     V-collapse (crown locked <= 0.15s to tier4) + horizontal floor-seam piston dust jets ->
     3 waves (24 weathered dark concrete boulders, wave 3 right at P3 touchdown!) -> 8-10s warm
     tan matte street base surge -> organic 2-story rubble.
  5. The Bakersfield Sign: pier-anchored Plane-A fracture blasts + stray rocket-fire purge ->
     u^2.4 north topple -> immediate 0.52s damped elastic street rebound (-88 -> -80 -> -88 ->
     -85.5 -> -88 deg) veiled in full-width 80-ft warm beige-tan dust across BOTH fallen towers
     & center span -> exact-pose rampable fallen arch.
  6. Shatterable Glass: 20 semi-translucent faceted crystalline shard MD3s (alpha=0.56, cool
     glass tint, ~1.5s clean fade-out) + cool silver-cyan bako_glass_sparkle + 120s respawn.
================
*/

void() RandomNPCs_Precache;
void() Vehicles_Precache;
void() funcbreakable_use;
void() breakable_on;

// ============================================================================
// 1. PRECACHE, MATH, LOCALIZED AUDIO & SMOOTH 60 Hz SEISMIC OSCILLATOR
// ============================================================================

void() BakoDestruct_Precache =
{
	if (bako_precached)
		return;
	bako_precached = TRUE;

	RandomNPCs_Precache ();
	Vehicles_Precache ();

	precache_model ("progs/bako_boulder1.md3");
	precache_model ("progs/bako_boulder2.md3");
	precache_model ("progs/bako_boulder3.md3");
	precache_model ("progs/bako_boulder4.md3");
	precache_model ("progs/bako_glass_shard1.md3");
	precache_model ("progs/bako_glass_shard2.md3");
	precache_model ("progs/bako_glass_shard3.md3");
	precache_model ("progs/gib1.mdl");
	precache_model ("progs/gib2.mdl");
	precache_model ("progs/gib3.mdl");

	precache_sound ("weapons/r_exp3.wav");
	precache_sound ("weapons/explodedist.wav");
	precache_sound ("vehicles/car_boom1.wav");
	precache_sound ("vehicles/car_boom2.wav");
	precache_sound ("vehicles/clang1.wav");
	precache_sound ("vehicles/clang2.wav");
	precache_sound ("vehicles/hit_metal1.wav");
	precache_sound ("break/glass_impact.wav");
	precache_sound ("break/glass_i1.wav");
	precache_sound ("break/glass_i2.wav");
	precache_sound ("break/rock_impact.wav");
	precache_sound ("break/rock_i1.wav");
	precache_sound ("break/rock_i2.wav");
	precache_sound ("break/metal_impact.wav");
	precache_sound ("lan/glass_tink.wav");
	precache_sound ("ltgun/zap.wav");
	precache_sound ("custom/spark5.wav");
	precache_sound ("misc/spark.wav");
	precache_sound ("hammer/hammer_clang.wav");
	precache_sound ("hammer/hammer_clang2.wav");
	precache_sound ("bikes/bell_ring.wav");
	precache_sound ("misc/medkey.wav");
	precache_sound ("ambience/woodcreak2a.wav");
	precache_sound ("player/udeath.wav");

	bako_fx_dust_surge = particleeffectnum ("bako_demolition_dust_surge");
	bako_fx_collapse_plume = particleeffectnum ("bako_collapse_plume");
	bako_fx_window_smoke = particleeffectnum ("bako_window_smoke");
	bako_fx_masonry_burst = particleeffectnum ("bako_masonry_burst");
	bako_fx_charge_pop = particleeffectnum ("bako_charge_pop");
	bako_fx_big_boom = particleeffectnum ("bako_big_boom");
	bako_fx_sign_sparks = particleeffectnum ("bako_sign_sparks");
	bako_fx_rebuild_weld = particleeffectnum ("bako_rebuild_weld");
	bako_fx_rock_dust = particleeffectnum ("bako_rock_dust");
	bako_fx_glass_break = particleeffectnum ("glass_break");
	bako_fx_glass_sparkle = particleeffectnum ("bako_glass_sparkle");
	bako_fx_rocket_burn = particleeffectnum ("rocket_burn");
};

void(vector org, float chan, string wav, float vol, float attn, float pitch) Bako_SoundAt =
{
	if (bako_snd_ent == world || bm_wasfreed (bako_snd_ent))
	{
		bako_snd_ent = spawn ();
		bako_snd_ent.classname = "bako_snd_emitter";
		bako_snd_ent.movetype = MOVETYPE_NONE;
		bako_snd_ent.solid = SOLID_NOT;
	}
	setorigin (bako_snd_ent, org);
	sound7 (bako_snd_ent, chan, wav, vol, attn, pitch);
};

// Pure top-right corner HUD toast (via BMST_BAKO_EVENT stat 121) - ZERO centerprint/minimap overlap!
void(float code, float dur) Bako_SetToast =
{
	bako_toast_code = code;
	bako_toast_end = time + dur;
};

float(float rad) Bako_SinRad =
{
	local float s;
	s = sin (rad);
	return s;
};

float(float rad) Bako_CosRad =
{
	local float c;
	c = cos (rad);
	return c;
};

float(float x) Bako_Sqrt =
{
	local float r;
	if (x <= 0)
		return 0;
	r = sqrt (x);
	return r;
};

float(float u) Bako_Clamp01 =
{
	if (u <= 0)
		return 0;
	if (u >= 1)
		return 1;
	return u;
};

// True accelerating gravity curve (~u^2.4): slow menacing yield at start, whipping fastest at impact!
float(float u) Bako_EaseGravity24 =
{
	u = Bako_Clamp01 (u);
	return u * u * (0.12 + 0.88 * Bako_Sqrt (u));
};

float(float u) Bako_EaseSmooth =
{
	u = Bako_Clamp01 (u);
	return u * u * (3.0 - 2.0 * u);
};

// Feed seismic energy into our continuous 60 Hz damped-sine oscillator (NEVER snaps punchangle!)
void(vector org, float radius, float strength, float push_kick) Bako_SafeShake =
{
	local entity p;
	local float d, frac;
	local vector dir;

	if (strength > 0)
	{
		bako_eq_org = org;
		if (radius > bako_eq_rad || bako_eq_amp < 0.08)
			bako_eq_rad = radius;
		bako_eq_amp = bound (0, max (bako_eq_amp, strength * 0.90) + strength * 0.10, 1.0);
	}

	if (push_kick <= 0)
		return;

	p = bm_player_head;
	while (p)
	{
		if (p.health > 0 && p.movetype == MOVETYPE_WALK && p.veh_van == world && p.veh_ride == world)
		{
			d = vlen (p.origin - org);
			if (d < 620)
			{
				dir = p.origin - org;
				dir_z = 0;
				if (vlen (dir) < 4)
					dir = '1 0 0';
				else
					dir = normalize (dir);
				frac = 1.0 - (d / 620);
				p.velocity = p.velocity + dir * (push_kick * frac) + '0 0 1' * (140 * frac);
				p.flags = p.flags - (p.flags & FL_ONGROUND);
			}
		}
		p = p.bm_player_next;
	}
};

// Continuous 60 Hz smooth damped-sine seismic rumble (runs EVERY server frame in BakoDestruct_Frame!)
// Strictly clamped: pitch <= +-3.0 deg, roll <= +-2.0 deg, yaw <= +-0.65 deg, slew <= 0.45 deg/frame!
void() Bako_TickSmoothShake =
{
	local float dt_f, frac, d, e, rmul, max_step;
	local float tgt_x, tgt_y, tgt_z;
	local entity p;

	if (bako_eq_last_t <= 0 || time < bako_eq_last_t)
	{
		bako_eq_last_t = time;
		return;
	}
	dt_f = bound (0.001, time - bako_eq_last_t, 0.05);
	bako_eq_last_t = time;

	if (bako_eq_amp > 0.004)
	{
		bako_eq_amp = bako_eq_amp * max (0.0, 1.0 - 2.30 * dt_f);
		if (bako_eq_amp < 0.004)
			bako_eq_amp = 0;
		bako_eq_phase = bako_eq_phase + dt_f;
	}

	max_step = min (0.42, 18.0 * dt_f);
	p = bm_player_head;
	while (p)
	{
		if (p.health > 0 && p.ishuman == 1 && autocvar_effects_explosion_shake != 0)
		{
			if (bako_eq_amp > 0.004 || vlen (p.bako_shake_cur) > 0.015)
			{
				tgt_x = 0;
				tgt_y = 0;
				tgt_z = 0;
				if (bako_eq_amp > 0.004 && bako_eq_rad > 1)
				{
					d = vlen (p.origin - bako_eq_org);
					if (d < bako_eq_rad)
					{
						if (bako_eq_rad >= 20000)
							frac = bound (0.40, 1.0 - (d / bako_eq_rad) * 0.60, 1.0);
						else
							frac = bound (0.0, (1.0 - (d / bako_eq_rad)) * 1.15, 1.0);
						rmul = 1.0;
						if (p.veh_van != world || p.mmt_tank != world || p.jb_vehicle != world || p.rr_vehicle != world)
							rmul = 0.55;
						e = bako_eq_amp * frac;
						tgt_x = bound (-3.0, e * 2.9 * Bako_SinRad (bako_eq_phase * 15.0), 3.0);
						tgt_y = bound (-0.65, e * 0.58 * Bako_SinRad (bako_eq_phase * 9.5 + 1.4), 0.65);
						tgt_z = bound (-2.0, e * 1.95 * Bako_SinRad (bako_eq_phase * 11.8 + 0.7) * rmul, 2.0);
					}
				}
				p.bako_shake_cur_x = p.bako_shake_cur_x + bound (0 - max_step, tgt_x - p.bako_shake_cur_x, max_step);
				p.bako_shake_cur_y = p.bako_shake_cur_y + bound (0 - max_step * 0.35, tgt_y - p.bako_shake_cur_y, max_step * 0.35);
				p.bako_shake_cur_z = p.bako_shake_cur_z + bound (0 - max_step * 0.68, tgt_z - p.bako_shake_cur_z, max_step * 0.68);
				if (bako_eq_amp <= 0.004 && vlen (p.bako_shake_cur) <= 0.02)
					p.bako_shake_cur = VEC_ORIGIN;
				p.punchangle_x = bound (-3.1, p.bako_shake_cur_x, 3.1);
				p.punchangle_y = bound (-0.7, p.bako_shake_cur_y, 0.7);
				p.punchangle_z = bound (-2.1, p.bako_shake_cur_z, 2.1);
			}
		}
		p = p.bm_player_next;
	}
};

// Purge any stray Q1.5 rocket_burn corona fireballs near a landmark (or all if rad <= 0)
void(vector org, float rad) Bako_PurgeStrayFires =
{
	local entity e, nxt;

	if (bako_fx_rocket_burn <= 0)
		return;
	e = nextent (world);
	while (e != world)
	{
		nxt = nextent (e);
		if (e.traileffectnum == bako_fx_rocket_burn && e.classname != "player" && e.bako_group == 0)
		{
			if (rad <= 0 || vlen (e.origin - org) <= rad)
				remove (e);
		}
		e = nxt;
	}
};

vector(vector pt, vector bmin, vector bmax) Bako_ClosestPtAABB =
{
	local vector c;

	c_x = bound (bmin_x, pt_x, bmax_x);
	c_y = bound (bmin_y, pt_y, bmax_y);
	c_z = bound (bmin_z, pt_z, bmax_z);
	return c;
};

// Ground-hugging radial street base-surge warm matte tan dust ring (rolls 400-650u outward down streets!)
void(vector org, vector bmin, vector bmax, float spd) Bako_EmitDustRing =
{
	local vector p, span, rdir;
	local float i, ang, rx, ry;

	if (bako_fx_dust_surge <= 0)
		return;

	span = (bmax - bmin) * 0.5;
	rx = max (120, span_x * 0.96);
	ry = max (120, span_y * 0.96);

	for (i = 0; i < 8; i = i + 1)
	{
		ang = (i * 45 + random () * 18) * 0.01745329;
		rdir_x = Bako_CosRad (ang);
		rdir_y = Bako_SinRad (ang);
		rdir_z = 0;
		p_x = org_x + rdir_x * rx;
		p_y = org_y + rdir_y * ry;
		p_z = bmin_z + 18 + random () * 42;
		pointparticles (bako_fx_dust_surge, p, rdir * (spd * (0.85 + random () * 0.30)) + '0 0 22', 1);
	}
};

// Full-width line base surge (for 80-ft wide Bakersfield Sign across BOTH fallen towers + center span!)
void(vector p0, vector p1, vector out_dir, float n_pts, float spd) Bako_EmitLineDustSurge =
{
	local float i, f;
	local vector p, side_dir, vel;

	if (bako_fx_dust_surge <= 0 || n_pts < 1)
		return;

	for (i = 0; i < n_pts; i = i + 1)
	{
		f = (n_pts > 1) ? (i / (n_pts - 1)) : 0.5;
		p = p0 + (p1 - p0) * f;
		p_z = p_z + 14 + random () * 34;
		side_dir = out_dir * ((i - 2 * floor (i / 2) == 0) ? 1.0 : -0.65);
		side_dir_x = side_dir_x + crandom () * 0.45;
		side_dir_y = side_dir_y + crandom () * 0.35;
		side_dir_z = 0;
		if (vlen (side_dir) > 0.05)
			side_dir = normalize (side_dir);
		vel = side_dir * (spd * (0.82 + random () * 0.35)) + '0 0 26';
		pointparticles (bako_fx_dust_surge, p, vel, 1);
	}
};

float(entity e) Bako_IsVehicle =
{
	if (e == world)
		return FALSE;
	if (e.veh_kind > 0)
		return TRUE;
	if (e.classname == "misc_vehicle_johnbird" || e.classname == "misc_vehicle_rocketrider")
		return TRUE;
	return FALSE;
};

// Safely lift walking players, bots, or ALL vehicles (karts/vans/tanks/Winged John/Rocket Rider) overlapping newly solidified rubble!
void(entity rub) Bako_LiftPlayersOnto =
{
	local entity p, v;
	local vector top_from, top_to;
	local float target_z;

	if (!rub)
		return;

	p = bm_player_head;
	while (p)
	{
		if (p.health > 0 && p.movetype != MOVETYPE_NOCLIP && p.movetype != MOVETYPE_NONE && p.veh_van == world && p.veh_ride == world)
		{
			if (p.absmax_x > rub.absmin_x - 20 && p.absmin_x < rub.absmax_x + 20
				&& p.absmax_y > rub.absmin_y - 20 && p.absmin_y < rub.absmax_y + 20
				&& p.absmin_z < rub.absmax_z + 24 && p.absmax_z > rub.absmin_z - 32)
			{
				top_from = p.origin;
				top_from_z = rub.absmax_z + 96;
				top_to = p.origin;
				top_to_z = rub.absmin_z - 16;
				traceline (top_from, top_to, FALSE, p);
				target_z = rub.absmax_z + 30;
				if (trace_fraction < 1 && trace_ent == rub)
					target_z = trace_endpos_z + 28;
				if (p.origin_z < target_z)
				{
					setorigin (p, p.origin_x * '1 0 0' + p.origin_y * '0 1 0' + target_z * '0 0 1');
					p.velocity_z = max (p.velocity_z, 160);
					p.flags = p.flags - (p.flags & FL_ONGROUND);
				}
			}
		}
		p = p.bm_player_next;
	}

	v = nextent (world);
	while (v != world)
	{
		if (Bako_IsVehicle (v) && v.solid != SOLID_NOT && !v.bako_roof_hidden)
		{
			if (v.absmax_x > rub.absmin_x - 28 && v.absmin_x < rub.absmax_x + 28
				&& v.absmax_y > rub.absmin_y - 28 && v.absmin_y < rub.absmax_y + 28
				&& v.absmin_z < rub.absmax_z + 28 && v.absmax_z > rub.absmin_z - 32)
			{
				top_from = v.origin;
				top_from_z = rub.absmax_z + 120;
				top_to = v.origin;
				top_to_z = rub.absmin_z - 16;
				traceline (top_from, top_to, FALSE, v);
				target_z = rub.absmax_z + 18;
				if (trace_fraction < 1 && trace_ent == rub)
					target_z = trace_endpos_z + 12;
				if (v.origin_z < target_z)
				{
					setorigin (v, v.origin_x * '1 0 0' + v.origin_y * '0 1 0' + target_z * '0 0 1');
					v.velocity_z = max (v.velocity_z, 140);
					if (v.veh_kind > 0)
					{
						v.veh_vz = max (v.veh_vz, 140);
						v.veh_air = TRUE;
						if (v.veh_driver == world)
							v.veh_coast_until = max (v.veh_coast_until, time + 1.4);
					}
					if (v.veh_driver != world && !bm_wasfreed (v.veh_driver))
						setorigin (v.veh_driver, v.origin + '0 0 20');
					if (v.jb_pilot != world && !bm_wasfreed (v.jb_pilot))
						setorigin (v.jb_pilot, v.origin + '0 0 20');
					if (v.rr_pilot != world && !bm_wasfreed (v.rr_pilot))
						setorigin (v.rr_pilot, v.origin + '0 0 20');
				}
			}
		}
		v = nextent (v);
	}
};

// Push overlapping walking players AND ALL vehicles (incl. parked karts, Winged John & Rocket Rider) smoothly clear before re-solidifying!
void(entity bmod, vector ctr) Bako_NudgePlayersClear =
{
	local entity p, v;
	local vector dir;

	if (!bmod)
		return;
	p = bm_player_head;
	while (p)
	{
		if (p.health > 0 && p.movetype != MOVETYPE_NOCLIP && p.movetype != MOVETYPE_NONE)
		{
			if (p.absmax_x > bmod.absmin_x - 20 && p.absmin_x < bmod.absmax_x + 20
				&& p.absmax_y > bmod.absmin_y - 20 && p.absmin_y < bmod.absmax_y + 20
				&& p.absmax_z > bmod.absmin_z - 16 && p.absmin_z < bmod.absmax_z + 16)
			{
				if (p.origin_z > bmod.absmax_z - 64)
				{
					setorigin (p, p.origin_x * '1 0 0' + p.origin_y * '0 1 0' + (bmod.absmax_z + 30) * '0 0 1');
					p.velocity_z = max (p.velocity_z, 150);
				}
				else
				{
					dir = p.origin - ctr;
					dir_z = 0;
					if (vlen (dir) < 4)
						dir = '1 0 0';
					else
						dir = normalize (dir);
					setorigin (p, p.origin + dir * 72 + '0 0 24');
					p.velocity = dir * 220 + '0 0 180';
				}
				p.flags = p.flags - (p.flags & FL_ONGROUND);
			}
		}
		p = p.bm_player_next;
	}

	// Lift any overlapping vehicles (and their MOVETYPE_NONE drivers/pilots) cleanly above rebuilding structures!
	v = nextent (world);
	while (v != world)
	{
		if (Bako_IsVehicle (v) && v.solid != SOLID_NOT && !v.bako_roof_hidden)
		{
			if (v.absmax_x > bmod.absmin_x - 28 && v.absmin_x < bmod.absmax_x + 28
				&& v.absmax_y > bmod.absmin_y - 28 && v.absmin_y < bmod.absmax_y + 28
				&& v.absmax_z > bmod.absmin_z - 24 && v.absmin_z < bmod.absmax_z + 24)
			{
				setorigin (v, v.origin_x * '1 0 0' + v.origin_y * '0 1 0' + (bmod.absmax_z + 26) * '0 0 1');
				v.velocity_z = max (v.velocity_z, 160);
				if (v.veh_kind > 0)
				{
					v.veh_vz = max (v.veh_vz, 160);
					v.veh_air = TRUE;
					if (v.veh_driver == world)
						v.veh_coast_until = max (v.veh_coast_until, time + 1.4);
				}
				if (v.veh_driver != world && !bm_wasfreed (v.veh_driver))
					setorigin (v.veh_driver, v.origin + '0 0 20');
				if (v.jb_pilot != world && !bm_wasfreed (v.jb_pilot))
					setorigin (v.jb_pilot, v.origin + '0 0 20');
				if (v.rr_pilot != world && !bm_wasfreed (v.rr_pilot))
					setorigin (v.rr_pilot, v.origin + '0 0 20');
			}
		}
		v = nextent (v);
	}
};

// Shatter all intact glass breakables within a radius of a blast or collapsing structure
void(vector org, float radius, entity attacker) Bako_ShatterGlassInRadius =
{
	local entity g, nxt, oself;
	local vector cpt;

	g = bako_glass_head;
	while (g != world)
	{
		nxt = g.bako_glass_next;
		if (!bm_wasfreed (g) && g.solid != SOLID_NOT && !g.waitmin)
		{
			cpt = Bako_ClosestPtAABB (org, g.absmin, g.absmax);
			if (vlen (org - cpt) <= radius)
			{
				oself = self;
				self = g;
				self.activate = attacker;
				funcbreakable_use ();
				self = oself;
			}
		}
		g = nxt;
	}
};

// ============================================================================
// 2. 100% BULLETPROOF ROOFTOP ENTITY HIDER & RESTORER (ZERO FLOATING SKY ITEMS!)
// ============================================================================

float(entity e) Bako_SkipRoofEntity =
{
	local string c;

	if (e == world || e.bako_group > 0)
		return TRUE;
	if (e.veh_driver != world || e.jb_pilot != world || e.rr_pilot != world)
		return TRUE;
	c = e.classname;
	if (c == "player" || c == "worldspawn" || c == "light" || c == "missile" || c == "grenade" || c == "rocket" || c == "spike")
		return TRUE;
	if (c == "bako_boulder" || c == "bako_chunk" || c == "bako_glass_shard" || c == "npc_bako_worker")
		return TRUE;
	if (c == "bako_destruct_ctrl" || c == "bako_snd_emitter" || c == "bc_cam" || c == "camera")
		return TRUE;
	if (c == "dn3fx_relay" || c == "bako_blast_spr" || c == "bm_radar_feed" || c == "ud_fx")
		return TRUE;
	if (c == "robdob" || c == "megaman" || c == "kyle_proj" || c == "milky" || c == "wc_shot" || c == "dookie_shot" || c == "foreloco_proj" || c == "greenjar_proj" || c == "greenguy_mini" || c == "pickle" || c == "netsend_disk")
		return TRUE;
	if (c == "misc_vehicle_johnbird" || c == "misc_vehicle_rocketrider" || c == "misc_mm_tank")
		return TRUE;
	return FALSE;
};

void(float grp, entity e, vector drop_pos) Bako_HideOneRoofEnt =
{
	if (e.bako_roof_hidden)
		return;

	if (e.bako_roof_grp == 0)
	{
		e.bako_roof_grp = grp;
		e.bako_roof_org = e.origin;
		if (grp == BAKO_GRP_FOX)
		{
			e.bako_roof_next = bako_fox_roof_list;
			bako_fox_roof_list = e;
		}
		else if (grp == BAKO_GRP_PADRE)
		{
			e.bako_roof_next = bako_padre_roof_list;
			bako_padre_roof_list = e;
		}
	}

	if (e.classname == "info_player_deathmatch")
	{
		e.bako_roof_hidden = TRUE;
		setorigin (e, drop_pos);
		return;
	}

	if (e.model != "" && e.model != string_null)
		e.bako_roof_mdl = e.model;
	else if (e.mdl != "" && e.mdl != string_null)
		e.bako_roof_mdl = e.mdl;
	e.bako_roof_mins = e.mins;
	e.bako_roof_maxs = e.maxs;
	e.bako_roof_avel = e.avelocity;
	e.bako_roof_solid = e.solid;
	e.bako_roof_mt = e.movetype;
	e.bako_roof_fx = e.effects;
	e.bako_roof_llev = e.light_lev;
	e.bako_roof_pflags = e.pflags;
	e.bako_roof_trail = e.traileffectnum;
	e.bako_roof_think = e.think;
	e.bako_roof_nthink = (e.nextthink > time) ? (e.nextthink - time) : 0;

	e.bako_roof_hidden = TRUE;
	e.solid = SOLID_NOT;
	e.movetype = MOVETYPE_NONE;
	e.avelocity = VEC_ORIGIN;
	e.effects = EF_NODRAW;
	e.light_lev = 0;
	e.pflags = 0;
	e.traileffectnum = 0;
	e.nextthink = 0;
	setmodel (e, "");
	e.modelindex = 0;
	setorigin (e, e.bako_roof_org - '0 0 2400');
};

void(float grp) Bako_HideRoofProps =
{
	local entity e, rlist;
	local vector bmin, bmax, drop_pos;
	local float min_z;

	if (grp == BAKO_GRP_FOX)
	{
		bmin = bako_fox_bmin - '96 96 0';
		bmax = bako_fox_bmax + '96 96 0';
		if (bmin_x > -10720) bmin_x = -10720;
		if (bmax_x < -8880)  bmax_x = -8880;
		if (bmin_y > 2080)   bmin_y = 2080;
		if (bmax_y < 4580)   bmax_y = 4580;
		min_z = 320;
		rlist = bako_fox_rubble_list;
		drop_pos = bako_fox_ctr + '0 0 260';
	}
	else if (grp == BAKO_GRP_PADRE)
	{
		bmin = bako_padre_bmin - '96 96 0';
		bmax = bako_padre_bmax + '96 96 0';
		if (bmin_x > -10500) bmin_x = -10500;
		if (bmax_x < -8940)  bmax_x = -8940;
		if (bmin_y > -6110)  bmin_y = -6110;
		if (bmax_y < -4470)  bmax_y = -4470;
		min_z = 185;
		rlist = bako_padre_rubble_list;
		drop_pos = bako_padre_ctr + '0 0 340';
	}
	else
		return;

	if (rlist != world)
	{
		drop_pos = (rlist.bako_home_min + rlist.bako_home_max) * 0.5;
		drop_pos_z = rlist.bako_home_max_z + 42;
	}

	// Re-hide any already tracked rooftop entities first
	e = (grp == BAKO_GRP_FOX) ? bako_fox_roof_list : bako_padre_roof_list;
	while (e != world)
	{
		if (!bm_wasfreed (e) && !e.bako_roof_hidden && !Bako_SkipRoofEntity (e))
			Bako_HideOneRoofEnt (grp, e, drop_pos);
		e = e.bako_roof_next;
	}

	// One-time scan on collapse inside the exact padded rooftop footprint with roof ceiling (never grabs sky flyers!)
	e = nextent (world);
	while (e != world)
	{
		if (!e.bako_roof_hidden && !Bako_SkipRoofEntity (e))
		{
			if (e.origin_x >= bmin_x && e.origin_x <= bmax_x
				&& e.origin_y >= bmin_y && e.origin_y <= bmax_y
				&& e.origin_z > min_z && e.origin_z <= bmax_z + 180)
			{
				Bako_HideOneRoofEnt (grp, e, drop_pos);
			}
		}
		e = nextent (e);
	}
};

// Enforce invisibility on the captured rooftop list (no periodic full-world nextent() scan!)
void(float grp) Bako_MaintainHiddenRoofProps =
{
	local entity e;

	e = (grp == BAKO_GRP_FOX) ? bako_fox_roof_list : bako_padre_roof_list;
	while (e != world)
	{
		if (!bm_wasfreed (e) && e.bako_roof_hidden && e.classname != "info_player_deathmatch")
		{
			if (e.solid != SOLID_NOT || e.modelindex != 0 || e.effects != EF_NODRAW || e.traileffectnum != 0 || e.nextthink != 0)
			{
				e.solid = SOLID_NOT;
				e.movetype = MOVETYPE_NONE;
				e.effects = EF_NODRAW;
				e.light_lev = 0;
				e.pflags = 0;
				e.traileffectnum = 0;
				e.nextthink = 0;
				setmodel (e, "");
				e.modelindex = 0;
				setorigin (e, e.bako_roof_org - '0 0 2400');
			}
		}
		e = e.bako_roof_next;
	}
};

void(float grp) Bako_RestoreRoofProps =
{
	local entity e;

	if (grp == BAKO_GRP_FOX)
		e = bako_fox_roof_list;
	else if (grp == BAKO_GRP_PADRE)
		e = bako_padre_roof_list;
	else
		return;

	while (e != world)
	{
		if (!bm_wasfreed (e) && e.bako_roof_hidden)
		{
			e.bako_roof_hidden = FALSE;
			if (e.classname == "info_player_deathmatch")
			{
				setorigin (e, e.bako_roof_org);
			}
			else
			{
				e.effects = e.bako_roof_fx;
				e.light_lev = e.bako_roof_llev;
				e.pflags = e.bako_roof_pflags;
				e.traileffectnum = e.bako_roof_trail;
				e.movetype = e.bako_roof_mt;
				e.solid = e.bako_roof_solid;
				e.avelocity = e.bako_roof_avel;
				if (e.bako_roof_mdl != "" && e.bako_roof_mdl != string_null)
					setmodel (e, e.bako_roof_mdl);
				// Restore exact saved trigger/item/kart bbox AFTER setmodel (preserves info_skypad '-40 -40 -26'..'40 40 36'!)
				setsize (e, e.bako_roof_mins, e.bako_roof_maxs);
				setorigin (e, e.bako_roof_org);
				if (e.classname == "info_skypad")
					dprint (strcat ("bako_roof: restored info_skypad mins=", vtos (e.mins), " maxs=", vtos (e.maxs), "\n"));
				if (e.bako_roof_nthink > 0)
				{
					e.think = e.bako_roof_think;
					e.nextthink = time + e.bako_roof_nthink;
				}
				else if (e.bako_roof_think && e.bako_roof_think != SUB_Null)
				{
					e.think = e.bako_roof_think;
					e.nextthink = time + 0.05;
				}
			}
		}
		e = e.bako_roof_next;
	}
};

// ============================================================================
// 3. ROLLING BOULDERS, NON-BURNING MASONRY CHUNKS & CRYSTALLINE GLASS SHARDS
// ============================================================================

string(float idx) Bako_BoulderModel =
{
	local float k;

	k = idx - 4 * floor (idx / 4);
	if (k == 0) return "progs/bako_boulder1.md3";
	if (k == 1) return "progs/bako_boulder2.md3";
	if (k == 2) return "progs/bako_boulder3.md3";
	return "progs/bako_boulder4.md3";
};

string(float idx) Bako_GlassShardModel =
{
	local float k;

	k = idx - 3 * floor (idx / 3);
	if (k == 0) return "progs/bako_glass_shard1.md3";
	if (k == 1) return "progs/bako_glass_shard2.md3";
	return "progs/bako_glass_shard3.md3";
};

void() Bako_BoulderRemove =
{
	if (bako_boulder_count > 0)
		bako_boulder_count = bako_boulder_count - 1;
	remove (self);
};

void() Bako_ChunkRemove =
{
	if (bako_chunk_count > 0)
		bako_chunk_count = bako_chunk_count - 1;
	remove (self);
};

void() Bako_ShardRemove =
{
	if (bako_shard_count > 0)
		bako_shard_count = bako_shard_count - 1;
	remove (self);
};

void(entity b, entity victim) Bako_BounceTarget =
{
	local vector dir, vxy;
	local float spd, kick_h, kick_z;

	if (victim == world || bm_wasfreed (victim))
		return;
	if (time < victim.bako_boulder_hit_t)
		return;

	spd = vlen (b.velocity);
	if (spd < 25)
		return;

	victim.bako_boulder_hit_t = time + 0.45;

	vxy = b.velocity;
	vxy_z = 0;
	dir = victim.origin - b.origin;
	dir_z = 0;
	if (vlen (vxy) > 25)
		dir = normalize (normalize (vxy) * 0.72 + (vlen (dir) > 4 ? normalize (dir) : '1 0 0') * 0.28);
	else if (vlen (dir) > 4)
		dir = normalize (dir);
	else
		dir = '1 0 0';

	if (Bako_IsVehicle (victim))
	{
		kick_h = bound (280, spd * 0.72, 460);
		kick_z = 210;
		victim.velocity = victim.velocity + dir * kick_h + '0 0 1' * kick_z;
		if (victim.veh_kind > 0)
		{
			victim.veh_vz = max (victim.veh_vz, kick_z);
			victim.veh_air = TRUE;
			if (victim.veh_driver == world)
				victim.veh_coast_until = max (victim.veh_coast_until, time + 1.4);
		}
		sound7 (victim, CHAN_AUTO, "vehicles/clang2.wav", 0.90, ATTN_NORM, 94 + random () * 16);
		if (victim.veh_driver != world && victim.veh_driver.ishuman == 1)
			Bako_SafeShake (victim.origin, 900, 0.55, 0);
		if (victim.jb_pilot != world && victim.jb_pilot.ishuman == 1)
			Bako_SafeShake (victim.origin, 900, 0.55, 0);
		if (victim.rr_pilot != world && victim.rr_pilot.ishuman == 1)
			Bako_SafeShake (victim.origin, 900, 0.55, 0);
		dprint (strcat ("bako_boulder: bounced vehicle ", victim.classname, " vz=", ftos (floor (victim.velocity_z)), "\n"));
		b.velocity = b.velocity * 0.70 + '0 0 100';
		return;
	}

	if (victim.health <= 0 || !victim.takedamage)
		return;
	if (victim.movetype == MOVETYPE_NONE || victim.movetype == MOVETYPE_PUSH || victim.movetype == MOVETYPE_NOCLIP)
		return;

	kick_h = bound (460, spd * 0.90, 660);
	kick_z = 380 + random () * 60;
	victim.flags = victim.flags - (victim.flags & FL_ONGROUND);
	victim.velocity = victim.velocity + dir * kick_h + '0 0 1' * kick_z;
	sound7 (victim, CHAN_BODY, "break/rock_impact.wav", 1.0, ATTN_NORM, 84 + random () * 18);
	if (victim.ishuman == 1)
		Bako_SafeShake (victim.origin, 900, 0.55, 0);
	dprint (strcat ("bako_boulder: bounced ", victim.classname, " vz=", ftos (floor (victim.velocity_z)), "\n"));
	if (autocvar_bako_boulder_dmg > 0)
		T_Damage (victim, b, b, autocvar_bako_boulder_dmg);

	b.velocity = b.velocity * 0.72 + '0 0 95';
};

void() Bako_BoulderTouch =
{
	local float spd;

	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		Bako_BoulderRemove ();
		return;
	}
	if (other.classname == "bako_boulder" || other.classname == "bako_chunk" || other.classname == "bako_glass_shard")
		return;

	if ((other.flags & (FL_CLIENT | FL_MONSTER)) || other.classname == "player" || Bako_IsVehicle (other))
	{
		Bako_BounceTarget (self, other);
		return;
	}

	spd = vlen (self.velocity);
	if (spd > 90 && time >= self.bako_boulder_snd_t)
	{
		self.bako_boulder_snd_t = time + 0.24;
		if (random () < 0.5)
			sound7 (self, CHAN_AUTO, "break/rock_impact.wav", bound (0.30, spd / 540, 0.90), ATTN_NORM, 82 + random () * 24);
		else
			sound7 (self, CHAN_AUTO, "break/rock_i1.wav", bound (0.28, spd / 580, 0.82), ATTN_NORM, 80 + random () * 24);
		if (bako_fx_rock_dust > 0)
			pointparticles (bako_fx_rock_dust, self.origin - '0 0 12', '0 0 24', 1);
	}
};

void() Bako_BoulderThink =
{
	local float age, rem, hspd, spd, dxy;
	local vector vxy, delta;
	local entity p, v;

	age = time - self.bako_boulder_born;
	rem = self.bako_boulder_life - age;
	if (rem <= 0 || pointcontents (self.origin) == CONTENT_SKY
		|| (age > 2.5 && self.origin_z > 420 && vlen (self.velocity) < 55))
	{
		Bako_BoulderRemove ();
		return;
	}
	if (rem < 1.2)
		self.alpha = max (0.04, rem / 1.2);

	if (self.bako_boulder_settled)
	{
		if (rem < 1.4)
			self.nextthink = time + 0.08;
		else
			self.nextthink = time + 0.5;
		return;
	}

	spd = vlen (self.velocity);
	vxy = self.velocity;
	vxy_z = 0;
	hspd = vlen (vxy);

	if (hspd > 38)
	{
		self.bako_boulder_rest_t = 0;
		if ((self.flags & FL_ONGROUND) || fabs (self.velocity_z) < 48)
		{
			self.velocity_x = self.velocity_x * 0.986;
			self.velocity_y = self.velocity_y * 0.986;
			self.avelocity_x = 0 - self.velocity_y * 1.95;
			self.avelocity_y = self.velocity_x * 1.95;
			if (time >= self.bako_boulder_dust_t && hspd > 160)
			{
				self.bako_boulder_dust_t = time + 0.30;
				if (bako_fx_rock_dust > 0)
					pointparticles (bako_fx_rock_dust, self.origin - '0 0 10', '0 0 20', 1);
			}
		}
	}
	else if (fabs (self.velocity_z) < 28)
	{
		if (self.bako_boulder_rest_t == 0)
			self.bako_boulder_rest_t = time;
		else if (time - self.bako_boulder_rest_t > 2.0)
		{
			self.bako_boulder_settled = TRUE;
			self.velocity = VEC_ORIGIN;
			self.avelocity = VEC_ORIGIN;
			self.movetype = MOVETYPE_NONE;
			self.solid = SOLID_NOT;
			self.nextthink = time + 0.5;
			return;
		}
	}

	// Fast proximity sweep over active players and driven vehicles (no per-boulder findradius spam!)
	if (spd > 25)
	{
		p = bm_player_head;
		while (p != world)
		{
			if (p.health > 0 && p.movetype != MOVETYPE_NONE && p.movetype != MOVETYPE_NOCLIP)
			{
				delta = p.origin - self.origin;
				if (fabs (delta_z) <= 84)
				{
					delta_z = 0;
					dxy = vlen (delta);
					if (dxy <= 84)
						Bako_BounceTarget (self, p);
				}
			}
			v = p.veh_van;
			if (v != world && !bm_wasfreed (v) && !v.bako_roof_hidden && v.solid != SOLID_NOT)
			{
				delta = v.origin - self.origin;
				if (fabs (delta_z) <= 96)
				{
					delta_z = 0;
					if (vlen (delta) <= 96)
						Bako_BounceTarget (self, v);
				}
			}
			p = p.bm_player_next;
		}
	}

	self.nextthink = time + 0.08;
};

entity(vector org, vector vel, float sc, float life, float idx, float grp) Bako_SpawnBoulder =
{
	local entity d, e, oldest;

	if (bako_boulder_count >= 18)
	{
		oldest = world;
		e = find (world, classname, "bako_boulder");
		while (e != world)
		{
			if (oldest == world || e.bako_boulder_born < oldest.bako_boulder_born)
				oldest = e;
			e = find (e, classname, "bako_boulder");
		}
		if (oldest != world)
		{
			remove (oldest);
			bako_boulder_count = bako_boulder_count - 1;
		}
	}

	d = spawn ();
	d.classname = "bako_boulder";
	d.bako_group = grp;
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_TRIGGER;
	d.bouncefactor = 0.52;
	d.bouncestop = 0.05;
	d.gravity = 0.96;
	d.scale = sc;
	d.alpha = 1.0;
	d.velocity = vel;
	d.angles_x = random () * 360;
	d.angles_y = random () * 360;
	d.angles_z = random () * 360;
	d.avelocity_x = crandom () * 380;
	d.avelocity_y = crandom () * 380;
	d.avelocity_z = crandom () * 300;
	d.bako_boulder_born = time;
	d.bako_boulder_life = life;
	d.bako_boulder_rest_t = 0;
	d.bako_boulder_settled = FALSE;
	d.touch = Bako_BoulderTouch;
	d.think = Bako_BoulderThink;
	d.nextthink = time + 0.05;
	setmodel (d, Bako_BoulderModel (idx));
	setsize (d, '-22 -22 -22', '22 22 22');
	setorigin (d, org);
	bako_boulder_count = bako_boulder_count + 1;
	return d;
};

// Non-burning Tier-2 tumbling dark concrete/masonry chunk (ZERO fire, ZERO rocket smoke!)
void() Bako_ChunkTouch =
{
	local float spd;

	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		Bako_ChunkRemove ();
		return;
	}
	if (other.classname == "bako_chunk" || other.classname == "bako_boulder" || other.classname == "bako_glass_shard")
		return;
	spd = vlen (self.velocity);
	if (spd > 110 && time >= self.bako_boulder_snd_t)
	{
		self.bako_boulder_snd_t = time + 0.25;
		sound7 (self, CHAN_AUTO, "break/rock_i2.wav", bound (0.18, spd / 650, 0.55), ATTN_NORM, 92 + random () * 28);
		if (bako_fx_rock_dust > 0)
			pointparticles (bako_fx_rock_dust, self.origin, '0 0 18', 1);
	}
};

void() Bako_ChunkThink =
{
	local float age, rem;

	age = time - self.bako_boulder_born;
	rem = self.bako_boulder_life - age;
	if (rem <= 0 || pointcontents (self.origin) == CONTENT_SKY
		|| (age > 1.8 && self.origin_z > 400 && vlen (self.velocity) < 55))
	{
		Bako_ChunkRemove ();
		return;
	}
	if (rem < 1.0)
		self.alpha = max (0.04, rem);
	if ((self.flags & FL_ONGROUND) || vlen (self.velocity) < 35)
	{
		self.avelocity = self.avelocity * 0.45;
		if (vlen (self.avelocity) < 20)
			self.avelocity = VEC_ORIGIN;
	}
	else if (age < 1.8 && time >= self.bako_boulder_dust_t)
	{
		self.bako_boulder_dust_t = time + 0.24;
		if (bako_fx_rock_dust > 0)
			pointparticles (bako_fx_rock_dust, self.origin, '0 0 12', 1);
	}
	self.nextthink = time + 0.08;
};

entity(vector org, vector vel, float sc, float life, float idx, float grp) Bako_SpawnMasonryChunk =
{
	local entity d, e, oldest;

	if (bako_chunk_count >= 18)
	{
		oldest = world;
		e = find (world, classname, "bako_chunk");
		while (e != world)
		{
			if (oldest == world || e.bako_boulder_born < oldest.bako_boulder_born)
				oldest = e;
			e = find (e, classname, "bako_chunk");
		}
		if (oldest != world)
		{
			remove (oldest);
			bako_chunk_count = bako_chunk_count - 1;
		}
	}

	d = spawn ();
	d.classname = "bako_chunk";
	d.bako_group = grp;
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_TRIGGER;
	d.bouncefactor = 0.54;
	d.bouncestop = 0.06;
	d.gravity = 0.96;
	d.scale = sc;
	d.alpha = 1.0;
	d.velocity = vel;
	d.angles_x = random () * 360;
	d.angles_y = random () * 360;
	d.angles_z = random () * 360;
	d.avelocity_x = crandom () * 480;
	d.avelocity_y = crandom () * 480;
	d.avelocity_z = crandom () * 420;
	d.bako_boulder_born = time;
	d.bako_boulder_life = life;
	d.touch = Bako_ChunkTouch;
	d.think = Bako_ChunkThink;
	d.nextthink = time + 0.08;
	setmodel (d, Bako_BoulderModel (idx));
	setsize (d, '-10 -10 -10', '10 10 10');
	setorigin (d, org);
	bako_chunk_count = bako_chunk_count + 1;
	return d;
};

// Faceted semi-translucent crystalline glass shard MD3 (alpha=0.56, cool glass tint, ~1.5s clean fade!)
void() Bako_GlassShardTouch =
{
	local float spd;

	if (pointcontents (self.origin) == CONTENT_SKY)
	{
		Bako_ShardRemove ();
		return;
	}
	if (other.classname == "bako_glass_shard" || other.classname == "bako_chunk" || other.classname == "bako_boulder")
		return;
	spd = vlen (self.velocity);
	if (spd > 60 && time >= self.bako_boulder_snd_t)
	{
		self.bako_boulder_snd_t = time + 0.35;
		if (random () < 0.45)
			sound7 (self, CHAN_AUTO, "lan/glass_tink.wav", bound (0.18, spd / 420, 0.55), ATTN_NORM, 92 + random () * 32);
		else if (random () < 0.5)
			sound7 (self, CHAN_AUTO, "break/glass_i1.wav", bound (0.16, spd / 440, 0.48), ATTN_NORM, 95 + random () * 26);
	}
};

void() Bako_GlassShardThink =
{
	local float age, rem;

	age = time - self.bako_boulder_born;
	rem = self.bako_boulder_life - age;
	if (rem <= 0 || pointcontents (self.origin) == CONTENT_SKY
		|| (age > 1.8 && self.origin_z > 400 && vlen (self.velocity) < 55))
	{
		Bako_ShardRemove ();
		return;
	}
	// Smooth fade-out over final 0.55s (~1.5s total dwell -> crisp sidewalk scatter!)
	if (rem < 0.55)
		self.alpha = max (0.02, 0.56 * (rem / 0.55));
	if ((self.flags & FL_ONGROUND) || vlen (self.velocity) < 28)
	{
		self.avelocity = self.avelocity * 0.40;
		if (vlen (self.avelocity) < 18)
			self.avelocity = VEC_ORIGIN;
	}
	self.nextthink = time + 0.08;
};

entity(vector org, vector vel, float sc, float idx) Bako_SpawnGlassShard =
{
	local entity d, e, oldest;

	if (bako_shard_count >= 16)
	{
		oldest = world;
		e = find (world, classname, "bako_glass_shard");
		while (e != world)
		{
			if (oldest == world || e.bako_boulder_born < oldest.bako_boulder_born)
				oldest = e;
			e = find (e, classname, "bako_glass_shard");
		}
		if (oldest != world)
		{
			remove (oldest);
			bako_shard_count = bako_shard_count - 1;
		}
	}

	d = spawn ();
	d.classname = "bako_glass_shard";
	d.movetype = MOVETYPE_BOUNCE;
	d.solid = SOLID_NOT;
	d.effects = EF_FULLBRIGHT;
	d.bouncefactor = 0.44;
	d.bouncestop = 0.05;
	d.gravity = 0.90;
	d.scale = sc;
	d.alpha = 0.56;
	d.colormod = '0.86 0.96 1.04';
	d.velocity = vel;
	d.angles_x = random () * 360;
	d.angles_y = random () * 360;
	d.angles_z = random () * 360;
	d.avelocity_x = crandom () * 580;
	d.avelocity_y = crandom () * 580;
	d.avelocity_z = crandom () * 540;
	d.bako_boulder_born = time;
	d.bako_boulder_life = 1.30 + random () * 0.38;
	d.touch = Bako_GlassShardTouch;
	d.think = Bako_GlassShardThink;
	d.nextthink = time + 0.08;
	setmodel (d, Bako_GlassShardModel (idx));
	setsize (d, '-4 -4 -4', '4 4 4');
	setorigin (d, org);
	bako_shard_count = bako_shard_count + 1;
	return d;
};

void(float grp) Bako_ClearGroupDebris =
{
	local entity e, nxt;

	e = find (world, classname, "bako_boulder");
	while (e != world)
	{
		nxt = find (e, classname, "bako_boulder");
		if (grp == 0 || e.bako_group == grp)
		{
			remove (e);
			if (bako_boulder_count > 0)
				bako_boulder_count = bako_boulder_count - 1;
		}
		e = nxt;
	}
	e = find (world, classname, "bako_chunk");
	while (e != world)
	{
		nxt = find (e, classname, "bako_chunk");
		if (grp == 0 || e.bako_group == grp)
		{
			remove (e);
			if (bako_chunk_count > 0)
				bako_chunk_count = bako_chunk_count - 1;
		}
		e = nxt;
	}
	if (grp == 0)
	{
		e = find (world, classname, "bako_glass_shard");
		while (e != world)
		{
			nxt = find (e, classname, "bako_glass_shard");
			remove (e);
			e = nxt;
		}
		bako_boulder_count = 0;
		bako_chunk_count = 0;
		bako_shard_count = 0;
	}
};

void(vector org, vector out_dir, float cnt, float spd, float boulder_life, float grp) Bako_BurstDebris =
{
	local float i;
	local vector v, jorg;

	for (i = 0; i < cnt; i = i + 1)
	{
		jorg_x = org_x + crandom () * 42;
		jorg_y = org_y + crandom () * 42;
		jorg_z = org_z + crandom () * 26;
		v = out_dir * (spd * (0.68 + random () * 0.58))
			+ ('1 0 0' * crandom () + '0 1 0' * crandom ()) * (spd * 0.52)
			+ '0 0 1' * (140 + random () * (spd * 0.42));
		if (i < 1 && boulder_life > 0)
			Bako_SpawnBoulder (jorg, v, 0.88 + random () * 0.48, boulder_life, floor (random () * 4), grp);
		else
			Bako_SpawnMasonryChunk (jorg, v, 0.58 + random () * 0.44, 5.5 + random () * 2.5, i, grp);
	}
};

// Spawn Padre Hotel's 3 radial waves (24 heavy dark concrete boulders!) down H St & 18th St!
void(float wave_idx) Bako_SpawnPadreBoulderWave =
{
	local float i, n, ang, spd, vz, sc, life, best_d, pd;
	local vector org, dir, vel, bmin, bmax, aim_dir;
	local entity p, near_p;

	bmin = bako_padre_ctr - '320 320 0';
	bmax = bako_padre_ctr + '320 320 0';
	if (bako_padre_rubble_list != world)
	{
		bmin = bako_padre_rubble_list.bako_home_min;
		bmax = bako_padre_rubble_list.bako_home_max;
	}

	// Find closest street-level player/bot within 1600u so 1 boulder per wave rolls right down their street lane!
	near_p = world;
	best_d = 1600;
	p = bm_player_head;
	while (p != world)
	{
		if (p.health > 0 && p.movetype != MOVETYPE_NOCLIP)
		{
			pd = vlen (p.origin - bako_padre_ctr);
			if (pd > 260 && pd < best_d && p.origin_z < bmin_z + 240)
			{
				best_d = pd;
				near_p = p;
			}
		}
		p = p.bm_player_next;
	}

	life = max (35, autocvar_bako_padre_rubble_t);
	n = 5;

	for (i = 0; i < n; i = i + 1)
	{
		if (i == 0 && near_p != world)
		{
			aim_dir = near_p.origin - bako_padre_ctr;
			aim_dir_z = 0;
			if (vlen (aim_dir) > 8)
				dir = normalize (aim_dir);
			else
				dir = '1 0 0';
		}
		else
		{
			if (i < 3)
				ang = (-115 + i * 75 + wave_idx * 14 + crandom () * 10) * 0.01745329;
			else
				ang = (115 + (i - 3) * 65 + wave_idx * 14 + crandom () * 12) * 0.01745329;
			dir_x = Bako_CosRad (ang);
			dir_y = Bako_SinRad (ang);
			dir_z = 0;
		}

		org_x = bako_padre_ctr_x + dir_x * (max (260, (bmax_x - bmin_x) * 0.52) + 24 + random () * 32);
		org_y = bako_padre_ctr_y + dir_y * (max (260, (bmax_y - bmin_y) * 0.52) + 24 + random () * 32);

		// Mix street-skimming rollers (i==0 or odd i) & arcing tumbling boulders (even i>0) so BOTH sidewalk & mid-street players get bounced!
		if (wave_idx >= 2)
			spd = 620 + random () * 380;
		else
			spd = 470 + wave_idx * 60 + random () * 340;
		if (i == 0 || (i - 2 * floor (i / 2) == 1))
		{
			org_z = bmin_z + 36 + random () * 16;
			vz = 48 + random () * 60;
		}
		else
		{
			org_z = bmin_z + 56 + wave_idx * 36 + random () * 60;
			vz = 150 + random () * 125;
		}
		vel = dir * spd + '0 0 1' * vz;
		sc = 1.05 + random () * 0.65;
		Bako_SpawnBoulder (org, vel, sc, life, i + wave_idx, BAKO_GRP_PADRE);
	}
};

// ============================================================================
// 4. COMEDIC CONSTRUCTION CREW FOR FOX THEATER SLOW REBUILD
// ============================================================================

void(entity attacker, float damage) Bako_WorkerPain =
{
	self.bako_worker_panic_t = time + 2.8;
	if (random () < 0.5)
		sound (self, CHAN_VOICE, "random_npcs/randguy_panic.wav", 0.85, ATTN_NORM);
	else
		sound (self, CHAN_VOICE, "random_npcs/afroguy_panic.wav", 0.85, ATTN_NORM);
};

void() Bako_WorkerDie =
{
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	sound (self, CHAN_VOICE, "player/udeath.wav", 0.9, ATTN_NORM);
	ThrowHead ("progs/gib1.mdl", self.health);
	ThrowGib ("progs/gib2.mdl", self.health);
	ThrowGib ("progs/gib3.mdl", self.health);
	remove (self);
};

void() Bako_WorkerThink =
{
	local vector d;
	local float f;

	if (bako_fox_state != BAKO_ST_REBUILD)
	{
		remove (self);
		return;
	}
	self.nextthink = time + 0.1;
	if (time < self.bako_worker_panic_t)
	{
		self.angles_y = self.angles_y + 28;
		walkmove (self.angles_y, 20);
		self.bako_worker_anim = self.bako_worker_anim + 1;
		f = self.bako_worker_anim - 10 * floor (self.bako_worker_anim / 10);
		self.frame = 20 + f;
		return;
	}

	d = bako_fox_ctr - self.origin;
	d_z = 0;
	self.angles_y = vectoyaw (d);
	makevectors ('0 1 0' * self.angles_y);
	self.bako_worker_anim = self.bako_worker_anim + 1;
	f = self.bako_worker_anim - 10 * floor (self.bako_worker_anim / 10);
	self.frame = 30 + f;
	if (time >= self.bako_worker_snd_t)
	{
		self.bako_worker_snd_t = time + 0.95 + random () * 0.85;
		if (bako_fx_rebuild_weld > 0)
			pointparticles (bako_fx_rebuild_weld, self.origin + v_forward * 28 + '0 0 24', '0 0 60', 1);
		if (random () < 0.5)
			sound7 (self, CHAN_BODY, "hammer/hammer_clang.wav", 0.65, ATTN_NORM, 92 + random () * 18);
		else
			sound7 (self, CHAN_BODY, "hammer/hammer_clang2.wav", 0.65, ATTN_NORM, 92 + random () * 18);
	}
};

void() Bako_SpawnFoxCrew =
{
	local float i;
	local entity w;
	local vector pos;

	for (i = 0; i < 3; i = i + 1)
	{
		w = spawn ();
		w.classname = "npc_bako_worker";
		w.bako_worker_slot = i;
		if (i == 0)
		{
			setmodel (w, "progs/npc_randguy.md3");
			w.colormod = '1.8 0.92 0.22';
		}
		else if (i == 1)
		{
			setmodel (w, "progs/npc_afroguy.md3");
			w.colormod = '1.7 1.4 0.25';
		}
		else
		{
			setmodel (w, "progs/npc_fatguy.md3");
			w.colormod = '1.85 0.78 0.18';
		}
		w.solid = SOLID_BBOX;
		w.movetype = MOVETYPE_NONE;
		setsize (w, '-16 -16 -24', '16 16 32');
		w.health = 75;
		w.takedamage = DAMAGE_AIM;
		w.th_pain = Bako_WorkerPain;
		w.th_die = Bako_WorkerDie;

		// Place cleanly on open H St & 20th St street perimeter OUTSIDE bako_fox_rubble + traceline exact floor (ZERO droptofloor failures!)
		if (i == 0)
		{
			pos_x = bako_fox_bmax_x + 150;
			pos_y = bako_fox_bmin_y + 220;
		}
		else if (i == 1)
		{
			pos_x = bako_fox_bmax_x + 150;
			pos_y = bako_fox_ctr_y + 180;
		}
		else
		{
			pos_x = bako_fox_ctr_x + 260;
			pos_y = bako_fox_bmin_y - 150;
		}
		pos_z = bako_fox_bmin_z + 32;
		traceline (pos + '0 0 192', pos - '0 0 192', TRUE, w);
		if (trace_fraction < 1.0)
			pos_z = trace_endpos_z + 25;
		setorigin (w, pos);
		w.think = Bako_WorkerThink;
		w.nextthink = time + 0.15 + i * 0.12;
	}
};

// ============================================================================
// 5. PIECE & RUBBLE RESET / ACTIVATION HELPERS
// ============================================================================

void(entity rlist) Bako_HideRubbleList =
{
	local entity r;

	r = rlist;
	while (r != world)
	{
		r.solid = SOLID_NOT;
		r.movetype = MOVETYPE_NONE;
		setmodel (r, "");
		r.modelindex = 0;
		setorigin (r, r.bako_home_org - '0 0 512');
		r = r.bako_rubble_next;
	}
};

void(entity rlist, float lift_frac, float make_solid) Bako_PositionRubbleList =
{
	local entity r;
	local float drop_z;

	drop_z = 260 * (1.0 - Bako_EaseSmooth (lift_frac));
	r = rlist;
	while (r != world)
	{
		if (make_solid && r.solid == SOLID_BSP)
		{
			r = r.bako_rubble_next;
			continue;
		}
		if (r.model == string_null || r.model == "")
			setmodel (r, r.mdl);
		r.angles = r.bako_home_ang;
		r.movetype = MOVETYPE_PUSH;
		if (make_solid)
		{
			r.solid = SOLID_BSP;
			setorigin (r, r.bako_home_org);
			Bako_LiftPlayersOnto (r);
		}
		else
		{
			r.solid = SOLID_NOT;
			setorigin (r, r.bako_home_org - '0 0 1' * drop_z);
		}
		r = r.bako_rubble_next;
	}
};

void(entity plist, float make_shootable) Bako_ResetPieceListIntact =
{
	local entity e;

	e = plist;
	while (e != world)
	{
		setmodel (e, e.mdl);
		e.alpha = 0;
		e.movetype = MOVETYPE_PUSH;
		e.solid = SOLID_BSP;
		e.angles = e.bako_home_ang;
		setorigin (e, e.bako_home_org);
		e.bako_piece_hit = FALSE;
		e.bako_piece_pop = FALSE;
		e.bako_piece_rb_done = FALSE;
		e.bako_piece_rb_vis = FALSE;
		e.bako_piece_bury_t = 0;
		e.bako_piece_hidden = FALSE;
		e.bako_broken = 0;
		e.bako_break_t0 = 0;
		e.bako_break_dur = 0;
		e.bako_break_bursts = 0;
		e.health = 99999;
		if (make_shootable)
			e.takedamage = DAMAGE_AIM;
		else
			e.takedamage = DAMAGE_NO;
		e = e.bako_piece_next;
	}
};

void(entity plist) Bako_HidePieceList =
{
	local entity e;

	e = plist;
	while (e != world)
	{
		e.solid = SOLID_NOT;
		e.takedamage = DAMAGE_NO;
		e.movetype = MOVETYPE_NONE;
		e.model = string_null;
		e.alpha = 0;
		e.bako_piece_hidden = TRUE;
		e.bako_broken = 2;
		setorigin (e, e.bako_home_org - '0 0 1400');
		e = e.bako_piece_next;
	}
};

// ============================================================================
// 5B. NON-BLINDING MULTI-POINT DEMOLITION EXPLOSIONS & 3-PART PROGRESSIVE BREAKS
// ============================================================================

void(vector org, vector out_dir, float vol, float shake_rad, float shake_str, float grp) Bako_BigExplosion =
{
	local vector dir;
	local float r;

	dir = out_dir;
	if (vlen (dir) < 0.05)
		dir = '0.7 -0.7 0.2';
	else
		dir = normalize (dir);

	if (bako_fx_big_boom > 0 && time >= bako_last_boom_dlight_t)
	{
		bako_last_boom_dlight_t = time + 0.22;
		pointparticles (bako_fx_big_boom, org, dir * 240 + '0 0 55', 1);
		Bako_BurstDebris (org, dir + '0 0 0.25', 2, 420, (grp == BAKO_GRP_PADRE) ? 60 : 0, grp);
	}
	else
	{
		if (bako_fx_charge_pop > 0)
			pointparticles (bako_fx_charge_pop, org, dir * 240 + '0 0 45', 1);
		Bako_BurstDebris (org, dir + '0 0 0.25', 2, 380, 0, grp);
	}
	if (bako_fx_masonry_burst > 0)
		pointparticles (bako_fx_masonry_burst, org, dir * 260 + '0 0 95', 1);

	r = random ();
	if (r < 0.38)
		Bako_SoundAt (org, CHAN_AUTO, "vehicles/car_boom2.wav", vol, 0.14, 82 + random () * 18);
	else if (r < 0.72)
		Bako_SoundAt (org, CHAN_BODY, "weapons/r_exp3.wav", vol * 0.92, 0.16, 86 + random () * 18);
	else
		Bako_SoundAt (org, CHAN_AUTO, "vehicles/car_boom1.wav", vol * 0.95, 0.14, 80 + random () * 16);

	if (shake_str > 0)
		Bako_SafeShake (org, shake_rad, shake_str, 100);
};

float(entity e) Bako_IsSignMainSpan =
{
	if (e == world)
		return FALSE;
	if (e.bako_role == "sign_span" || e.bako_role == "span" || e.bako_role == "arch" || e.bako_role == "main_arch")
		return TRUE;
	if ((e.bako_home_max_x - e.bako_home_min_x) > 500)
		return TRUE;
	return FALSE;
};

float(entity e) Bako_IsPadreEarlyCandidate =
{
	local string r;

	if (e == world || e.bako_broken != 0)
		return FALSE;
	r = e.bako_role;
	if (r == "west_wing" || r == "east_wing" || r == "crown")
		return TRUE;
	if (r == "tier4" && (bako_padre_crown == world || bako_padre_crown.bako_broken > 0))
		return TRUE;
	return FALSE;
};

float(entity e) Bako_IsFoxEarlyCandidate =
{
	local string r;

	if (e == world || e.bako_broken != 0)
		return FALSE;
	r = e.bako_role;
	if (r == "tower_upper" || r == "marquee" || r == "facade_e" || r == "stagehouse")
		return TRUE;
	if (r == "tower_lower" && (bako_fox_twr_hi == world || bako_fox_twr_hi.bako_broken > 0))
		return TRUE;
	return FALSE;
};

entity(entity hit_targ, vector hit_org) Bako_PickPadreBreakPiece =
{
	local entity e, best;
	local float best_d, d;
	local vector pctr;

	if (Bako_IsPadreEarlyCandidate (hit_targ))
		return hit_targ;
	if (hit_targ == bako_padre_t4 && Bako_IsPadreEarlyCandidate (bako_padre_crown))
		return bako_padre_crown;

	best = world;
	best_d = 999999;
	e = bako_padre_pieces;
	while (e != world)
	{
		if (Bako_IsPadreEarlyCandidate (e))
		{
			pctr = (e.bako_home_min + e.bako_home_max) * 0.5;
			d = vlen (pctr - hit_org);
			if (d < best_d)
			{
				best_d = d;
				best = e;
			}
		}
		e = e.bako_piece_next;
	}
	return best;
};

entity(entity hit_targ, vector hit_org) Bako_PickFoxBreakPiece =
{
	local entity e, best;
	local float best_d, d;
	local vector pctr;

	if (hit_targ == bako_fox_clock_ent && Bako_IsFoxEarlyCandidate (bako_fox_twr_hi))
		return bako_fox_twr_hi;
	if (Bako_IsFoxEarlyCandidate (hit_targ))
		return hit_targ;
	if (hit_targ == bako_fox_twr_low && Bako_IsFoxEarlyCandidate (bako_fox_twr_hi))
		return bako_fox_twr_hi;

	best = world;
	best_d = 999999;
	e = bako_fox_pieces;
	while (e != world)
	{
		if (Bako_IsFoxEarlyCandidate (e))
		{
			pctr = (e.bako_home_min + e.bako_home_max) * 0.5;
			d = vlen (pctr - hit_org);
			if (d < best_d)
			{
				best_d = d;
				best = e;
			}
		}
		e = e.bako_piece_next;
	}
	return best;
};

entity(entity hit_targ, vector hit_org) Bako_PickSignBreakPiece =
{
	local entity e, best;
	local float best_d, d;
	local vector pctr;

	if (hit_targ != world && hit_targ.bako_broken == 0 && !Bako_IsSignMainSpan (hit_targ))
		return hit_targ;

	best = world;
	best_d = 999999;
	e = bako_sign_pieces;
	while (e != world)
	{
		if (e.bako_broken == 0 && !Bako_IsSignMainSpan (e))
		{
			pctr = (e.bako_home_min + e.bako_home_max) * 0.5;
			d = vlen (pctr - hit_org);
			if (d < best_d)
			{
				best_d = d;
				best = e;
			}
		}
		e = e.bako_piece_next;
	}
	return best;
};

// Trigger a dramatic hit-localized Stage 1 or Stage 2 structural break on ONE shot section!
void(entity e, float grp, vector hit_org) Bako_BreakPieceEarly =
{
	local vector pctr, rdir, ctr, svel, bpos;
	local float i, is_pad;

	if (e == world || e.bako_broken != 0)
		return;

	e.bako_broken = 1;
	e.bako_break_t0 = time;
	if (grp == BAKO_GRP_SIGN)
		e.bako_break_dur = (e.bako_dur > 0.5) ? bound (1.2, e.bako_dur, 2.2) : 1.65;
	else
		e.bako_break_dur = 2.75;
	e.bako_break_bursts = 0;
	e.bako_piece_hit = FALSE;
	e.bako_piece_pop = TRUE;
	e.bako_piece_bury_t = 0;
	e.bako_piece_fx_t = 0;
	e.solid = SOLID_NOT;
	e.takedamage = DAMAGE_NO;
	e.movetype = MOVETYPE_NONE;

	ctr = bako_fox_ctr;
	is_pad = FALSE;
	if (grp == BAKO_GRP_PADRE)
	{
		ctr = bako_padre_ctr;
		is_pad = TRUE;
	}
	else if (grp == BAKO_GRP_SIGN)
		ctr = bako_sign_ctr;

	pctr = (e.bako_home_min + e.bako_home_max) * 0.5;
	rdir = pctr - ctr;
	rdir_z = 0;
	if (vlen (rdir) < 8) rdir = '0.7 -0.7 0';
	rdir = normalize (rdir);

	// Hide attached roof props / clock immediately so nothing ever floats in midair!
	if (grp == BAKO_GRP_PADRE && e == bako_padre_crown)
		Bako_HideRoofProps (BAKO_GRP_PADRE);
	if (grp == BAKO_GRP_FOX && e == bako_fox_twr_hi && bako_fox_clock_ent != world && bako_fox_clock_ent.solid != SOLID_NOT)
	{
		bako_fox_clock_ent.takedamage = DAMAGE_NO;
		bako_fox_clock_ent.solid = SOLID_NOT;
		bako_fox_clock_ent.model = string_null;
		setorigin (bako_fox_clock_ent, bako_fox_clock_ent.bako_home_org - '0 0 1200');
		for (i = 0; i < 6; i = i + 1)
		{
			svel = ('1 0 0' * (160 + crandom () * 200)) + ('0 1 0' * (-160 + crandom () * 200)) + ('0 0 1' * (80 + random () * 140));
			Bako_SpawnGlassShard (pctr + '48 -48 0', svel, 1.05 + random () * 0.35, i);
		}
		Bako_SoundAt (pctr, CHAN_ITEM, "break/glass_impact.wav", 0.95, 0.16, 100);
	}

	// Dual initial fracture explosions right at the shot seam & piece base!
	bpos = (vlen (hit_org - pctr) < 420) ? ((hit_org + pctr) * 0.5) : pctr;
	Bako_BigExplosion (bpos, rdir, 0.96, 24000, is_pad ? 0.65 : 0.56, grp);
	Bako_BigExplosion (pctr + '0 0 -48', rdir + '0 0 0.2', 0.88, 24000, 0, grp);
	if (grp == BAKO_GRP_SIGN)
	{
		if (bako_fx_sign_sparks > 0)
			pointparticles (bako_fx_sign_sparks, pctr, rdir * 160 + '0 0 90', 3);
		for (i = 0; i < 6; i = i + 1)
		{
			svel = ('1 0 0' * crandom () + '0 1 0' * crandom ()) * 240 + '0 0 140';
			Bako_SpawnGlassShard (pctr, svel, 0.95 + random () * 0.35, i);
		}
		Bako_SoundAt (pctr, CHAN_VOICE, "vehicles/clang2.wav", 0.95, 0.14, 96);
		Bako_SoundAt (pctr, CHAN_BODY, "ltgun/zap.wav", 0.90, 0.18, 108);
	}
	else
	{
		Bako_ShatterGlassInRadius (pctr, 420, world);
	}

	// Padre Stage 1/2 breaks immediately send 4 heavy concrete boulders tumbling down the street!
	if (is_pad)
	{
		for (i = 0; i < 4; i = i + 1)
		{
			svel = rdir * (460 + random () * 280) + ('1 0 0' * crandom () + '0 1 0' * crandom ()) * 180 + '0 0 1' * (80 + random () * 110);
			Bako_SpawnBoulder (pctr + rdir * 120, svel, 1.05 + random () * 0.55, 65, i, BAKO_GRP_PADRE);
		}
	}

	dprint (strcat ("bako_stage_break: grp=", ftos (grp), " role=", e.bako_role, "\n"));
};

// Animate all pieces currently in Stage 1 / Stage 2 early break smoothly into dust & underground!
void(entity plist, float grp, vector ctr, float bmin_z) Bako_TickEarlyPieceList =
{
	local entity e;
	local float dt_b, u, ease, bury_u, drop_eff;
	local vector pos, pctr, rdir, ang_eff, shift_eff;

	e = plist;
	while (e != world)
	{
		if (e.bako_broken == 1)
		{
			dt_b = time - e.bako_break_t0;
			u = Bako_Clamp01 (dt_b / max (0.6, e.bako_break_dur));

			// Compute clean dramatic shear/fall trajectory that buries cleanly below street level!
			if (grp == BAKO_GRP_SIGN)
			{
				if (e.bako_fall_drop > 0)
				{
					ang_eff = e.bako_fall_angles;
					shift_eff = e.bako_fall_shift;
					drop_eff = max (e.bako_fall_drop, (e.bako_home_max_z - bmin_z) - 24);
				}
				else
				{
					ang_eff = (e.bako_home_org_x < ctr_x) ? '28 12 -115' : '-26 -14 -115';
					shift_eff = (e.bako_home_org_x < ctr_x) ? '-54 96 0' : '48 96 0';
					drop_eff = max (280, (e.bako_home_max_z - bmin_z) - 24);
				}
			}
			else if (grp == BAKO_GRP_PADRE)
			{
				ang_eff = e.bako_fall_angles * 1.15;
				shift_eff = e.bako_fall_shift;
				drop_eff = max (e.bako_fall_drop, (e.bako_home_max_z - bmin_z) - 80);
			}
			else
			{
				if (e == bako_fox_twr_hi)
				{
					ang_eff = '42 4 14';
					shift_eff = '110 -80 0';
					drop_eff = (e.bako_home_max_z - bmin_z) - 40;
				}
				else if (e == bako_fox_twr_low)
				{
					ang_eff = e.bako_fall_angles * 0.70;
					shift_eff = '-210 110 0';
					drop_eff = e.bako_fall_drop + 400;
				}
				else
				{
					ang_eff = e.bako_fall_angles;
					shift_eff = e.bako_fall_shift;
					drop_eff = max (e.bako_fall_drop, (e.bako_home_max_z - bmin_z) - 80);
				}
			}

			if (u < 1.0)
			{
				ease = Bako_EaseGravity24 (u);
				e.angles = e.bako_home_ang + ang_eff * ease;
				pos = e.bako_home_org + shift_eff * ease - '0 0 1' * (drop_eff * ease);
				setorigin (e, pos);

				pctr = (e.absmin + e.absmax) * 0.5;
				rdir = pctr - ctr;
				rdir_z = 0;
				if (vlen (rdir) < 8) rdir = '0.7 -0.7 0';
				rdir = normalize (rdir);

				// Staggered mid-fall secondary explosions!
				if (u >= 0.25 && !(e.bako_break_bursts & 1))
				{
					e.bako_break_bursts = e.bako_break_bursts | 1;
					Bako_BigExplosion (pctr + '0 0 -24', rdir, 0.86, 24000, 0.42, grp);
				}
				if (u >= 0.56 && !(e.bako_break_bursts & 2) && grp != BAKO_GRP_SIGN)
				{
					e.bako_break_bursts = e.bako_break_bursts | 2;
					Bako_BigExplosion (pctr + rdir * 40, rdir, 0.88, 24000, 0.46, grp);
				}
				if (u >= 0.70 && time >= e.bako_piece_fx_t)
				{
					e.bako_piece_fx_t = time + 0.48;
					if (grp == BAKO_GRP_FOX && e == bako_fox_twr_hi)
						Bako_VeilFoxTowerUpper (e, ctr);
					else
						Bako_VeilPieceLanding (e, ctr);
				}
			}
			else
			{
				if (!e.bako_piece_hit)
				{
					e.bako_piece_hit = TRUE;
					e.bako_piece_bury_t = time;
					e.bako_piece_hit_pos = e.origin;
					e.bako_piece_hit_ang = e.angles;
					pctr = (e.absmin + e.absmax) * 0.5;
					pctr_z = bmin_z + 32;
					rdir = pctr - ctr;
					rdir_z = 0;
					if (vlen (rdir) < 8) rdir = '0.7 -0.7 0';
					rdir = normalize (rdir);
					if (grp == BAKO_GRP_FOX && e == bako_fox_twr_hi)
						Bako_VeilFoxTowerUpper (e, ctr);
					else
						Bako_VeilPieceLanding (e, ctr);
					Bako_BigExplosion (pctr, rdir, 0.96, 24000, 0.72, grp);
					Bako_SoundAt (pctr, CHAN_BODY, "break/rock_impact.wav", 0.94, 0.14, 80 + random () * 16);
				}

				bury_u = Bako_Clamp01 ((time - e.bako_piece_bury_t) / 0.68);
				setorigin (e, e.bako_piece_hit_pos - '0 0 320' * bury_u);
				if (time >= e.bako_piece_fx_t)
				{
					e.bako_piece_fx_t = time + 0.48;
					if (grp == BAKO_GRP_FOX && e == bako_fox_twr_hi)
						Bako_VeilFoxTowerUpper (e, ctr);
					else
						Bako_VeilPieceLanding (e, ctr);
				}
				if (bury_u >= 1.0)
				{
					e.bako_broken = 2;
					e.bako_piece_hidden = TRUE;
					e.solid = SOLID_NOT;
					e.model = string_null;
					setorigin (e, e.bako_home_org - '0 0 1400');
				}
			}
		}
		e = e.bako_piece_next;
	}
};

// ============================================================================
// 6. LANDMARK STATE TRANSITIONS (FOX, PADRE, BAKERSFIELD SIGN)
// ============================================================================

void() Bako_ResetFoxIntact =
{
	bako_fox_state = BAKO_ST_INTACT;
	bako_fox_stage = 0;
	bako_fox_max_hp = max (10, autocvar_bako_fox_clock_hp);
	if (bako_fox_clock_ent != world && bako_fox_clock_ent.max_health > bako_fox_max_hp)
		bako_fox_max_hp = bako_fox_clock_ent.max_health;
	bako_fox_hp = bako_fox_max_hp;
	bako_fox_rubble_up = FALSE;

	Bako_HideRubbleList (bako_fox_rubble_list);
	Bako_ResetPieceListIntact (bako_fox_pieces, TRUE);

	if (bako_fox_clock_ent != world)
	{
		setmodel (bako_fox_clock_ent, bako_fox_clock_ent.mdl);
		bako_fox_clock_ent.alpha = 0;
		bako_fox_clock_ent.movetype = MOVETYPE_PUSH;
		bako_fox_clock_ent.solid = SOLID_BSP;
		bako_fox_clock_ent.angles = bako_fox_clock_ent.bako_home_ang;
		setorigin (bako_fox_clock_ent, bako_fox_clock_ent.bako_home_org);
		bako_fox_clock_ent.takedamage = DAMAGE_AIM;
		bako_fox_clock_ent.health = 99999;
	}
	Bako_RestoreRoofProps (BAKO_GRP_FOX);
	Bako_RestoreGlassInBox (bako_fox_bmin - '96 96 32', bako_fox_bmax + '96 96 64');
};

void() Bako_TriggerFoxCollapse =
{
	local entity e;
	local vector corg, svel;
	local float max_end, end_t, i;

	if (bako_fox_state != BAKO_ST_INTACT)
		return;

	bako_fox_state = BAKO_ST_COLLAPSE;
	bako_fox_stage = 3;
	bako_fox_phase_t0 = time;
	bako_fox_hp = 0;
	bako_fox_rubble_up = FALSE;
	bako_fox_fx_t = 0;

	Bako_PurgeStrayFires (bako_fox_ctr, 1500);
	Bako_HideRoofProps (BAKO_GRP_FOX);

	corg = bako_fox_ctr + '0 0 820';
	if (bako_fox_clock_ent != world)
	{
		corg = (bako_fox_clock_ent.bako_home_min + bako_fox_clock_ent.bako_home_max) * 0.5;
		bako_fox_clock_ent.takedamage = DAMAGE_NO;
		bako_fox_clock_ent.solid = SOLID_NOT;
		bako_fox_clock_ent.model = string_null;
		setorigin (bako_fox_clock_ent, bako_fox_clock_ent.bako_home_org - '0 0 1200');
	}

	// Rich multi-point Stage 3 initiation blasts across clock/tower & marquee!
	Bako_BigExplosion (corg, '0.75 -0.65 0.25', 1.0, 24000, 0.80, BAKO_GRP_FOX);
	Bako_BigExplosion (bako_fox_ctr + '320 -420 220', '0.7 -0.7 0.2', 0.90, 24000, 0, BAKO_GRP_FOX);
	if (bako_fx_sign_sparks > 0)
		pointparticles (bako_fx_sign_sparks, corg, '140 -140 80', 2);
	if (bako_fx_glass_sparkle > 0)
		pointparticles (bako_fx_glass_sparkle, corg, '180 -180 60', 2);
	for (i = 0; i < 8; i = i + 1)
	{
		svel_x = 180 + crandom () * 240;
		svel_y = -180 + crandom () * 240;
		svel_z = 80 + random () * 180;
		Bako_SpawnGlassShard (corg + '56 -56 -16' + ('1 0 0' * crandom () + '0 1 0' * crandom ()) * 24, svel, 1.10 + random () * 0.40, i);
	}
	Bako_BurstDebris (corg + '56 -56 -16', '0.78 -0.62 0.25', 8, 540, 65, BAKO_GRP_FOX);
	Bako_ShatterGlassInRadius (bako_fox_ctr, 760, world);

	Bako_SoundAt (corg, CHAN_VOICE, "vehicles/car_boom2.wav", 1.0, ATTN_NONE, 96);
	Bako_SoundAt (corg, CHAN_AUTO, "break/glass_impact.wav", 1.0, 0.14, 100);
	Bako_SoundAt (corg, CHAN_BODY, "vehicles/clang2.wav", 0.95, 0.14, 92);
	Bako_SafeShake (corg, 24000, 0.80, 160);
	Bako_SetToast (1, 8.8);

	max_end = 8.4;
	e = bako_fox_pieces;
	while (e != world)
	{
		e.takedamage = DAMAGE_NO;
		if (e.bako_broken == 0)
		{
			e.bako_piece_hit = FALSE;
			e.bako_piece_pop = FALSE;
			e.bako_piece_bury_t = 0;
			e.bako_piece_hidden = FALSE;
			e.bako_piece_fx_t = 0;
			end_t = e.bako_delay + e.bako_dur + 0.85;
			if (end_t > max_end)
				max_end = end_t;
		}
		e = e.bako_piece_next;
	}
	bako_fox_collapse_dur = bound (8.3, max_end + 0.20, 9.2);
};

void() Bako_StartFoxRebuild =
{
	local entity e;

	if (bako_fox_pieces == world && bako_fox_clock_ent == world)
		return;

	Bako_ClearGroupDebris (BAKO_GRP_FOX);
	Bako_PurgeStrayFires (bako_fox_ctr, 1500);

	bako_fox_state = BAKO_ST_REBUILD;
	bako_fox_phase_t0 = time;
	bako_fox_rb_snd_t = 0;
	bako_fox_rb_clank_t = 0;
	bako_fox_clock_rb_vis = FALSE;
	bako_fox_clock_rb_done = FALSE;

	// Snap ALL pieces strictly upright (angles = bako_home_ang) & INVISIBLE underground before rising!
	e = bako_fox_pieces;
	while (e != world)
	{
		e.solid = SOLID_NOT;
		e.takedamage = DAMAGE_NO;
		e.movetype = MOVETYPE_NONE;
		e.bako_broken = 0;
		e.bako_piece_rb_done = FALSE;
		e.bako_piece_rb_vis = FALSE;
		e.model = string_null;
		e.angles = e.bako_home_ang;
		setorigin (e, e.bako_home_org - '0 0 1400');
		e = e.bako_piece_next;
	}
	if (bako_fox_clock_ent != world)
	{
		bako_fox_clock_ent.solid = SOLID_NOT;
		bako_fox_clock_ent.takedamage = DAMAGE_NO;
		bako_fox_clock_ent.movetype = MOVETYPE_NONE;
		bako_fox_clock_ent.model = string_null;
		bako_fox_clock_ent.angles = bako_fox_clock_ent.bako_home_ang;
		setorigin (bako_fox_clock_ent, bako_fox_clock_ent.bako_home_org - '0 0 1400');
	}
	Bako_SpawnFoxCrew ();
};

void() Bako_ResetPadreIntact =
{
	bako_padre_state = BAKO_ST_INTACT;
	bako_padre_stage = 0;
	bako_padre_max_hp = max (100, autocvar_bako_padre_hp);
	bako_padre_hp = bako_padre_max_hp;
	bako_padre_ms = 0;
	bako_padre_rubble_up = FALSE;
	bako_padre_pop_idx = 0;
	bako_padre_wave_bits = 0;

	Bako_HideRubbleList (bako_padre_rubble_list);
	Bako_ResetPieceListIntact (bako_padre_pieces, TRUE);
	Bako_RestoreRoofProps (BAKO_GRP_PADRE);
	Bako_RestoreGlassInBox (bako_padre_bmin - '96 96 32', bako_padre_bmax + '96 96 64');
};

void() Bako_TriggerPadreCollapse =
{
	local entity e, t4, cr;
	local float max_end, end_t;

	if (bako_padre_state != BAKO_ST_INTACT)
		return;

	bako_padre_state = BAKO_ST_COLLAPSE;
	bako_padre_stage = 3;
	bako_padre_phase_t0 = time;
	bako_padre_hp = 0;
	bako_padre_rubble_up = FALSE;
	bako_padre_pop_idx = 0;
	bako_padre_wave_bits = 0;
	bako_padre_fx_t = 0;
	bako_padre_rumble_t = time + 2.55;
	bako_padre_boom_t = time + 2.85;

	Bako_PurgeStrayFires (bako_padre_ctr, 1800);
	Bako_HideRoofProps (BAKO_GRP_PADRE);

	Bako_ShatterGlassInRadius (bako_padre_ctr, 960, world);
	// Crisp structural crack at dt=0 (leaves dynamic headroom so 0.05..2.05s charge pops ring cleanly!)
	Bako_SoundAt (bako_padre_ctr + '0 0 240', CHAN_VOICE, "ambience/woodcreak2a.wav", 0.78, ATTN_NONE, 86);
	Bako_SoundAt (bako_padre_ctr + '0 0 240', CHAN_BODY, "break/rock_impact.wav", 0.65, 0.25, 74);
	Bako_SafeShake (bako_padre_ctr, 24000, 0.68, 120);
	Bako_SetToast (2, 12.2);

	// Cache tier4 & crown refs (crown dynamically rides welded atop tier4's live rotated roof collar if both intact!)
	t4 = bako_padre_t4;
	cr = bako_padre_crown;
	e = bako_padre_pieces;
	while (e != world)
	{
		if (e.bako_role == "tier4") t4 = e;
		if (e.bako_role == "crown") cr = e;
		e = e.bako_piece_next;
	}
	bako_padre_t4 = t4;
	bako_padre_crown = cr;
	if (t4 != world && cr != world && t4.bako_broken == 0 && cr.bako_broken == 0)
	{
		cr.bako_delay = t4.bako_delay;
		cr.bako_dur = t4.bako_dur;
	}

	// Ensure a weighty 11.8..12.6s controlled demolition timeline (~9.5s visible descent after 2.0s charge pops!)
	max_end = 0;
	e = bako_padre_pieces;
	while (e != world)
	{
		if (e.bako_broken == 0)
		{
			end_t = e.bako_delay + e.bako_dur;
			if (end_t > max_end)
				max_end = end_t;
		}
		e = e.bako_piece_next;
	}
	if (max_end > 1.0 && max_end < 10.6)
	{
		e = bako_padre_pieces;
		while (e != world)
		{
			if (e.bako_broken == 0)
				e.bako_dur = e.bako_dur * (10.65 / max_end);
			e = e.bako_piece_next;
		}
	}

	max_end = 11.4;
	e = bako_padre_pieces;
	while (e != world)
	{
		e.takedamage = DAMAGE_NO;
		if (e.bako_broken == 0)
		{
			e.bako_piece_hit = FALSE;
			e.bako_piece_pop = FALSE;
			e.bako_piece_bury_t = 0;
			e.bako_piece_hidden = FALSE;
			e.bako_piece_fx_t = 0;
			end_t = e.bako_delay + e.bako_dur + 0.85;
			if (end_t > max_end)
				max_end = end_t;
		}
		e = e.bako_piece_next;
	}
	bako_padre_collapse_dur = bound (11.8, max_end + 0.35, 12.6);
};

void() Bako_ResetSignIntact =
{
	bako_sign_state = BAKO_ST_INTACT;
	bako_sign_stage = 0;
	bako_sign_max_hp = max (20, autocvar_bako_sign_hp);
	bako_sign_hp = bako_sign_max_hp;
	bako_sign_impacted = FALSE;
	bako_sign_rebound_clank = FALSE;

	Bako_HideRubbleList (bako_sign_rubble_list);
	Bako_ResetPieceListIntact (bako_sign_pieces, TRUE);
};

void() Bako_TriggerSignCollapse =
{
	local entity e, span_e;
	local float max_end, end_t, i;
	local vector wpier, epier, svel;

	if (bako_sign_state != BAKO_ST_INTACT)
		return;

	bako_sign_state = BAKO_ST_COLLAPSE;
	bako_sign_stage = 3;
	bako_sign_phase_t0 = time;
	bako_sign_hp = 0;
	bako_sign_impacted = FALSE;
	bako_sign_rebound_clank = FALSE;
	bako_sign_fx_t = 0;

	// Immediately purge any stray Q1.5 rocket_burn fireballs near the Sign piers!
	Bako_PurgeStrayFires (bako_sign_ctr, 1500);

	// Anchor initial fracture blasts strictly at BOTH Plane-A base piers of the main span (west & east curbs!)
	wpier = bako_sign_ctr + '-460 0 56';
	epier = bako_sign_ctr + '460 0 56';
	span_e = bako_sign_pieces;
	e = bako_sign_pieces;
	while (e != world)
	{
		if (Bako_IsSignMainSpan (e))
			span_e = e;
		e = e.bako_piece_next;
	}
	if (span_e != world)
	{
		wpier_x = span_e.bako_home_min_x + 76;
		wpier_y = (span_e.bako_home_min_y + span_e.bako_home_max_y) * 0.5;
		wpier_z = span_e.bako_home_min_z + 16;
		epier_x = span_e.bako_home_max_x - 76;
		epier_y = wpier_y;
		epier_z = wpier_z;
	}

	Bako_BigExplosion (wpier, '-0.5 0.85 0.25', 0.96, 24000, 0.60, BAKO_GRP_SIGN);
	Bako_BigExplosion (epier, '0.5 0.85 0.25', 0.96, 24000, 0, BAKO_GRP_SIGN);
	if (bako_fx_sign_sparks > 0)
	{
		pointparticles (bako_fx_sign_sparks, wpier + '0 0 36', '-110 80 90', 2);
		pointparticles (bako_fx_sign_sparks, epier + '0 0 36', '110 80 90', 2);
	}
	if (bako_fx_glass_sparkle > 0)
	{
		pointparticles (bako_fx_glass_sparkle, wpier + '0 0 110', '-80 80 60', 1);
		pointparticles (bako_fx_glass_sparkle, epier + '0 0 110', '80 80 60', 1);
	}
	for (i = 0; i < 6; i = i + 1)
	{
		svel = ('1 0 0' * crandom () + '0 1 0' * crandom ()) * 240 + '0 0 140';
		Bako_SpawnGlassShard (((i < 3) ? wpier : epier) + '0 0 130', svel, 0.95 + random () * 0.35, i);
	}

	Bako_SoundAt (bako_sign_ctr + '0 0 80', CHAN_VOICE, "vehicles/clang2.wav", 1.0, ATTN_NONE, 92);
	Bako_SoundAt (bako_sign_ctr + '0 0 80', CHAN_AUTO, "ltgun/zap.wav", 0.95, 0.14, 108);
	Bako_SoundAt (bako_sign_ctr + '0 0 80', CHAN_BODY, "break/glass_impact.wav", 0.95, 0.14, 104);
	Bako_SafeShake (bako_sign_ctr, 24000, 0.60, 110);
	Bako_SetToast (3, 5.2);

	max_end = 4.2;
	e = bako_sign_pieces;
	while (e != world)
	{
		e.takedamage = DAMAGE_NO;
		if (e.bako_broken == 0)
		{
			if (!Bako_IsSignMainSpan (e))
			{
				// Blow off any still-intact tower cap cleanly at Stage 3 start so only sign_span drives main arch impact!
				Bako_BreakPieceEarly (e, BAKO_GRP_SIGN, (e.bako_home_min + e.bako_home_max) * 0.5);
			}
			else
			{
				e.solid = SOLID_NOT;
				e.movetype = MOVETYPE_NONE;
				e.bako_piece_hit = FALSE;
				e.bako_piece_pop = FALSE;
				end_t = e.bako_delay + e.bako_dur;
				if (end_t > max_end)
					max_end = end_t;
			}
		}
		e = e.bako_piece_next;
	}
	bako_sign_collapse_dur = max_end + 0.54;
};

void(float which) Bako_SnapCollapsed =
{
	if ((which == 0 || which == BAKO_GRP_FOX) && (bako_fox_pieces != world || bako_fox_rubble_list != world))
	{
		Bako_HideRoofProps (BAKO_GRP_FOX);
		bako_fox_state = BAKO_ST_RUBBLE;
		bako_fox_phase_t0 = time;
		bako_fox_hp = 0;
		bako_fox_rubble_up = TRUE;
		Bako_HidePieceList (bako_fox_pieces);
		if (bako_fox_clock_ent != world)
		{
			bako_fox_clock_ent.solid = SOLID_NOT;
			bako_fox_clock_ent.takedamage = DAMAGE_NO;
			bako_fox_clock_ent.model = string_null;
		}
		Bako_PositionRubbleList (bako_fox_rubble_list, 1.0, TRUE);
	}
	if ((which == 0 || which == BAKO_GRP_PADRE) && (bako_padre_pieces != world || bako_padre_rubble_list != world))
	{
		Bako_HideRoofProps (BAKO_GRP_PADRE);
		bako_padre_state = BAKO_ST_RUBBLE;
		bako_padre_phase_t0 = time;
		bako_padre_hp = 0;
		bako_padre_rubble_up = TRUE;
		Bako_HidePieceList (bako_padre_pieces);
		Bako_PositionRubbleList (bako_padre_rubble_list, 1.0, TRUE);
	}
	if ((which == 0 || which == BAKO_GRP_SIGN) && (bako_sign_pieces != world || bako_sign_rubble_list != world))
	{
		bako_sign_state = BAKO_ST_RUBBLE;
		bako_sign_phase_t0 = time;
		bako_sign_hp = 0;
		bako_sign_impacted = TRUE;
		Bako_HidePieceList (bako_sign_pieces);
		Bako_PositionRubbleList (bako_sign_rubble_list, 1.0, TRUE);
	}
};

// ============================================================================
// 7. UNIVERSAL WEAPON DAMAGE & AABB CLOSEST-POINT SPLASH ROUTING
// ============================================================================

void(entity targ, vector hit_org, entity inflictor, entity attacker, float damage) BakoDestruct_OnDamage =
{
	local float pct;
	local entity brk;
	local vector puff_org, e_face, s_face;

	if (!targ || damage <= 0)
		return;
	if (inflictor.classname == "teledeath" || inflictor.classname == "teledeath2"
		|| attacker.classname == "teledeath" || attacker.classname == "teledeath2"
		|| damage >= 40000)
		return;

	targ.health = 99999;

	// Material hit sparks / matte dust chips (never blood!)
	if (targ.bako_material == BAKO_MAT_METAL)
	{
		if (bako_fx_sign_sparks > 0)
			pointparticles (bako_fx_sign_sparks, hit_org, '0 0 60', 1);
		if (time >= targ.pain_finished)
		{
			targ.pain_finished = time + 0.14;
			Bako_SoundAt (hit_org, CHAN_BODY, "vehicles/hit_metal1.wav", 0.76, ATTN_NORM, 94 + random () * 18);
		}
	}
	else if (targ.bako_material == BAKO_MAT_GLASS)
	{
		if (bako_fx_glass_sparkle > 0)
			pointparticles (bako_fx_glass_sparkle, hit_org, '0 0 40', 1);
		if (time >= targ.pain_finished)
		{
			targ.pain_finished = time + 0.12;
			Bako_SoundAt (hit_org, CHAN_BODY, "lan/glass_tink.wav", 0.78, ATTN_NORM, 96 + random () * 20);
		}
	}
	else
	{
		if (bako_fx_rock_dust > 0)
			pointparticles (bako_fx_rock_dust, hit_org, '0 0 36', 1);
		if (time >= targ.pain_finished)
		{
			targ.pain_finished = time + 0.16;
			Bako_SoundAt (hit_org, CHAN_BODY, "break/rock_impact.wav", 0.68, ATTN_NORM, 88 + random () * 22);
		}
	}

	// --- 1. FOX THEATER (3-Part Hit-Localized Progressive Break, 450 HP pool) ---
	if (targ.bako_group == BAKO_GRP_FOX)
	{
		if (bako_fox_state != BAKO_ST_INTACT)
			return;
		if (inflictor != world && inflictor != attacker)
		{
			if (bako_fox_last_infl == inflictor && bako_fox_last_t == time)
				return;
			bako_fox_last_infl = inflictor;
			bako_fox_last_t = time;
		}
		bako_fox_hp = bako_fox_hp - damage;
		if (bako_fox_max_hp <= 0)
			bako_fox_max_hp = max (10, autocvar_bako_fox_clock_hp);
		pct = (bako_fox_hp / bako_fox_max_hp) * 100;

		if (bako_fx_glass_sparkle > 0 && damage >= 25)
			pointparticles (bako_fx_glass_sparkle, hit_org, '0 0 40', 1);
		if (damage >= 45 && bako_fx_masonry_burst > 0)
			pointparticles (bako_fx_masonry_burst, hit_org, '0 0 70', 1);

		if (bako_fox_hp > 0 && bako_fox_stage < 1 && pct <= 66.7)
		{
			bako_fox_stage = 1;
			brk = Bako_PickFoxBreakPiece (targ, hit_org);
			if (brk != world)
				Bako_BreakPieceEarly (brk, BAKO_GRP_FOX, hit_org);
			else
				Bako_BigExplosion (hit_org, '0.7 -0.7 0.2', 0.94, 24000, 0.54, BAKO_GRP_FOX);
		}
		if (bako_fox_hp > 0 && bako_fox_stage < 2 && pct <= 33.4)
		{
			bako_fox_stage = 2;
			brk = Bako_PickFoxBreakPiece (targ, hit_org);
			if (brk != world)
				Bako_BreakPieceEarly (brk, BAKO_GRP_FOX, hit_org);
			else
				Bako_BigExplosion (hit_org, '0.7 -0.7 0.2', 0.96, 24000, 0.60, BAKO_GRP_FOX);
		}
		if (bako_fox_hp <= 0)
			Bako_TriggerFoxCollapse ();
		return;
	}

	// --- 2. PADRE HOTEL (3-Part Hit-Localized Progressive Break, Unified 2600 HP pool) ---
	if (targ.bako_group == BAKO_GRP_PADRE)
	{
		if (bako_padre_state != BAKO_ST_INTACT)
			return;
		if (inflictor != world && inflictor != attacker)
		{
			if (bako_padre_last_infl == inflictor && bako_padre_last_t == time)
				return;
			bako_padre_last_infl = inflictor;
			bako_padre_last_t = time;
		}
		bako_padre_hp = bako_padre_hp - damage;
		if (bako_padre_max_hp <= 0)
			bako_padre_max_hp = 2600;
		pct = (bako_padre_hp / bako_padre_max_hp) * 100;

		if (damage >= 55 && bako_fx_masonry_burst > 0)
			pointparticles (bako_fx_masonry_burst, hit_org, '0 0 80', 1);

		// Outer visible East (H St) & South (18th St) facade coordinates for unmistakable progressive wear!
		e_face_x = bako_padre_bmax_x + 12;
		e_face_y = bako_padre_ctr_y - 160;
		e_face_z = bako_padre_bmin_z;
		s_face_x = bako_padre_ctr_x + 140;
		s_face_y = bako_padre_bmin_y - 12;
		s_face_z = bako_padre_bmin_z;

		if (pct <= 75 && !(bako_padre_ms & 1))
		{
			bako_padre_ms = bako_padre_ms | 1;
			Bako_SoundAt (e_face + '0 0 280', CHAN_AUTO, "ambience/woodcreak2a.wav", 0.95, 0.16, 86);
			Bako_SoundAt (e_face + '0 0 280', CHAN_BODY, "break/glass_impact.wav", 0.88, 0.18, 102);
			Bako_SafeShake (e_face + '0 0 280', 3000, 0.36, 0);
			puff_org = e_face + '0 0 300';
			if (bako_fx_window_smoke > 0)
			{
				pointparticles (bako_fx_window_smoke, puff_org, '90 -30 85', 2);
				pointparticles (bako_fx_window_smoke, s_face + '0 0 310', '30 -90 85', 2);
			}
			if (bako_fx_glass_sparkle > 0)
				pointparticles (bako_fx_glass_sparkle, puff_org, '130 -60 40', 2);
			Bako_BurstDebris (puff_org, '0.8 -0.5 0.2', 5, 310, 0, BAKO_GRP_PADRE);
			Bako_SetToast (11, 3.0);
		}
		if (bako_padre_hp > 0 && bako_padre_stage < 1 && pct <= 66.7)
		{
			bako_padre_stage = 1;
			brk = Bako_PickPadreBreakPiece (targ, hit_org);
			if (brk != world)
				Bako_BreakPieceEarly (brk, BAKO_GRP_PADRE, hit_org);
			else
				Bako_BigExplosion (hit_org, '0.8 -0.6 0.2', 0.96, 24000, 0.62, BAKO_GRP_PADRE);
		}
		if (pct <= 50 && !(bako_padre_ms & 2))
		{
			bako_padre_ms = bako_padre_ms | 2;
			Bako_SoundAt (bako_padre_ctr + '0 0 420', CHAN_AUTO, "vehicles/car_boom1.wav", 0.94, 0.15, 90);
			Bako_ShatterGlassInRadius (bako_padre_ctr, 680, attacker);
			Bako_SafeShake (bako_padre_ctr, 3800, 0.50, 0);
			puff_org = e_face + '0 40 560';
			if (bako_fx_window_smoke > 0)
			{
				pointparticles (bako_fx_window_smoke, puff_org, '95 -35 95', 3);
				pointparticles (bako_fx_window_smoke, s_face + '-60 0 540', '20 -95 95', 3);
			}
			if (bako_fx_glass_sparkle > 0)
				pointparticles (bako_fx_glass_sparkle, puff_org, '150 -80 50', 2);
			Bako_BurstDebris (puff_org, '0.8 -0.6 0.2', 7, 360, 0, BAKO_GRP_PADRE);
			Bako_SetToast (12, 3.0);
		}
		if (bako_padre_hp > 0 && bako_padre_stage < 2 && pct <= 33.4)
		{
			bako_padre_stage = 2;
			brk = Bako_PickPadreBreakPiece (targ, hit_org);
			if (brk != world)
				Bako_BreakPieceEarly (brk, BAKO_GRP_PADRE, hit_org);
			else
				Bako_BigExplosion (hit_org, '0.8 -0.6 0.2', 0.98, 24000, 0.68, BAKO_GRP_PADRE);
		}
		if (pct <= 25 && !(bako_padre_ms & 4))
		{
			bako_padre_ms = bako_padre_ms | 4;
			Bako_SoundAt (bako_padre_ctr + '0 0 650', CHAN_AUTO, "vehicles/car_boom2.wav", 0.96, 0.14, 86);
			Bako_SafeShake (bako_padre_ctr, 4800, 0.65, 0);
			puff_org = e_face + '0 -40 700';
			if (bako_fx_window_smoke > 0)
			{
				pointparticles (bako_fx_window_smoke, puff_org, '105 -45 68', 3);
				pointparticles (bako_fx_window_smoke, s_face + '60 0 680', '35 -105 68', 3);
			}
			if (bako_fx_masonry_burst > 0)
				pointparticles (bako_fx_masonry_burst, puff_org, '150 -90 50', 2);
			Bako_BurstDebris (puff_org, '0.85 -0.55 0.2', 9, 420, 35, BAKO_GRP_PADRE);
			Bako_SetToast (13, 3.0);
		}
		if (bako_padre_hp <= 0)
			Bako_TriggerPadreCollapse ();
		return;
	}

	// --- 3. BAKERSFIELD SIGN (3-Part Hit-Localized Progressive Break, Unified 540 HP pool) ---
	if (targ.bako_group == BAKO_GRP_SIGN)
	{
		if (bako_sign_state != BAKO_ST_INTACT)
			return;
		if (inflictor != world && inflictor != attacker)
		{
			if (bako_sign_last_infl == inflictor && bako_sign_last_t == time)
				return;
			bako_sign_last_infl = inflictor;
			bako_sign_last_t = time;
		}
		bako_sign_hp = bako_sign_hp - damage;
		if (bako_sign_max_hp <= 0)
			bako_sign_max_hp = max (20, autocvar_bako_sign_hp);
		pct = (bako_sign_hp / bako_sign_max_hp) * 100;

		if (bako_sign_hp > 0 && bako_sign_stage < 1 && pct <= 66.7)
		{
			bako_sign_stage = 1;
			brk = Bako_PickSignBreakPiece (targ, hit_org);
			if (brk != world)
				Bako_BreakPieceEarly (brk, BAKO_GRP_SIGN, hit_org);
			else
				Bako_BigExplosion (hit_org, '0 1 0.25', 0.94, 24000, 0.52, BAKO_GRP_SIGN);
		}
		if (bako_sign_hp > 0 && bako_sign_stage < 2 && pct <= 33.4)
		{
			bako_sign_stage = 2;
			brk = Bako_PickSignBreakPiece (targ, hit_org);
			if (brk != world)
				Bako_BreakPieceEarly (brk, BAKO_GRP_SIGN, hit_org);
			else
				Bako_BigExplosion (hit_org, '0 1 0.25', 0.96, 24000, 0.56, BAKO_GRP_SIGN);
		}
		if (bako_sign_hp <= 0)
			Bako_TriggerSignCollapse ();
		return;
	}
};

// Called from combat.qc:T_RadiusDamage and eric_cannon.qc:EC_NukeBlastDamage!
void(vector org, float radius, float peak_dmg, entity inflictor, entity attacker, float is_nuke) BakoDestruct_RadiusSplash =
{
	local entity e, best_padre, best_sign, best_fox, nxt;
	local float best_padre_pts, best_sign_pts, best_fox_pts;
	local vector best_padre_pt, best_sign_pt, best_fox_pt, cpt;
	local float dist, pts, eff_rad, mul;

	if (!bako_present && bako_glass_head == world)
		return;
	if (peak_dmg <= 0 || radius <= 0)
		return;

	eff_rad = radius + 48;
	mul = is_nuke ? 1.75 : 1.0;

	best_fox = world;   best_fox_pts = 0;
	best_padre = world; best_padre_pts = 0;
	best_sign = world;  best_sign_pts = 0;

	e = bako_dest_head;
	while (e != world)
	{
		nxt = e.bako_dest_next;
		if (!bm_wasfreed (e) && e.solid != SOLID_NOT && e.takedamage)
		{
			cpt = Bako_ClosestPtAABB (org, e.absmin, e.absmax);
			dist = vlen (org - cpt);
			if (dist < eff_rad)
			{
				pts = peak_dmg * (1.0 - (dist / eff_rad)) * mul;
				if (pts > 1)
				{
					if (e.bako_group == BAKO_GRP_FOX && bako_fox_state == BAKO_ST_INTACT)
					{
						if (pts > best_fox_pts) { best_fox = e; best_fox_pts = pts; best_fox_pt = cpt; }
					}
					else if (e.bako_group == BAKO_GRP_PADRE && bako_padre_state == BAKO_ST_INTACT)
					{
						if (pts > best_padre_pts) { best_padre = e; best_padre_pts = pts; best_padre_pt = cpt; }
					}
					else if (e.bako_group == BAKO_GRP_SIGN && bako_sign_state == BAKO_ST_INTACT)
					{
						if (pts > best_sign_pts) { best_sign = e; best_sign_pts = pts; best_sign_pt = cpt; }
					}
					else if (e.bako_group == BAKO_GRP_GLASS && !e.waitmin)
					{
						T_Damage (e, inflictor, attacker, pts);
					}
				}
			}
		}
		e = nxt;
	}

	if (best_fox != world)
		BakoDestruct_OnDamage (best_fox, best_fox_pt, inflictor, attacker, best_fox_pts);
	if (best_padre != world)
		BakoDestruct_OnDamage (best_padre, best_padre_pt, inflictor, attacker, best_padre_pts);
	if (best_sign != world)
		BakoDestruct_OnDamage (best_sign, best_sign_pt, inflictor, attacker, best_sign_pts);
};

// ============================================================================
// 8. MASTER CONTROLLER THINK - FOX, PADRE & SIGN STATE MACHINES (20 Hz)
// ============================================================================

// Exact bottom-up rebuild schedule for Fox Theater (25s total, full underground emergence, ZERO mid-air pop-ins!)
vector(entity e, float rb_scale) Bako_FoxRebuildWindow =
{
	local string r;
	local float s0, d0, rise;

	r = e.bako_role;
	if (r == "stagehouse")
	{
		s0 = 3.5;  d0 = 6.2;  rise = 980;
	}
	else if (r == "auditorium_roof")
	{
		s0 = 4.6;  d0 = 6.2;  rise = 710;
	}
	else if (r == "facade_s")
	{
		s0 = 10.4; d0 = 4.5;  rise = 710;
	}
	else if (r == "facade_e")
	{
		s0 = 11.2; d0 = 4.3;  rise = 398;
	}
	else if (r == "marquee")
	{
		s0 = 13.0; d0 = 3.6;  rise = 336;
	}
	else if (r == "tower_lower")
	{
		s0 = 16.4; d0 = 4.0;  rise = 640;
	}
	else if (r == "tower_upper")
	{
		// Negative rise = starts +72u ABOVE tower_lower top collar (ZERO red FOX slicing) & alpha-fades in cleanly!
		s0 = 20.4; d0 = 3.0;  rise = -72;
	}
	else
	{
		s0 = 4.0 + bound (0, e.bako_rebuild_order - 1, 6) * 2.4;
		d0 = 4.2;
		rise = 400;
	}
	return (s0 * rb_scale) * '1 0 0' + (d0 * rb_scale) * '0 1 0' + rise * '0 0 1';
};

// Dense localized dust-veil burst directly on a piece's street landing spot BEFORE bury/hide!
void(entity e, vector ctr_ref) Bako_VeilPieceLanding =
{
	local vector pctr, p0, p1, rdir;

	pctr = (e.absmin + e.absmax) * 0.5;
	pctr_z = ctr_ref_z + 28;
	rdir = pctr - ctr_ref;
	rdir_z = 0;
	if (vlen (rdir) < 8) rdir = '0.7 -0.7 0';
	rdir = normalize (rdir);

	if (bako_fx_dust_surge > 0)
	{
		pointparticles (bako_fx_dust_surge, pctr, rdir * 340 + '0 0 36', 1);
		p0 = e.absmin; p0_z = ctr_ref_z + 24;
		p1 = e.absmax; p1_z = ctr_ref_z + 24;
		pointparticles (bako_fx_dust_surge, p0 + (p1 - p0) * 0.50, rdir * 280 + '0 0 42', 1);
	}
	if (bako_fx_collapse_plume > 0)
		pointparticles (bako_fx_collapse_plume, pctr + '0 0 48', rdir * 220 + '0 0 65', 1);
};

// Full-length warm-tan dust curtain along Fox tower_upper's actual tilted axis (belfry base -> mid -> blue dome tip!)
void(entity hi, vector ctr_ref) Bako_VeilFoxTowerUpper =
{
	local vector p0, p1, p2, rdir;

	if (time < bako_fox_veil_t)
		return;
	bako_fox_veil_t = time + 0.34;

	makevectors (hi.angles);
	p0 = hi.origin + v_up * 120;
	p1 = hi.origin + v_up * 320;
	p2 = hi.origin + v_up * 500;
	p0_z = bound (ctr_ref_z + 18, p0_z, ctr_ref_z + 96);
	p1_z = bound (ctr_ref_z + 22, p1_z, ctr_ref_z + 108);
	p2_z = bound (ctr_ref_z + 22, p2_z, ctr_ref_z + 108);

	rdir = p2 - ctr_ref;
	rdir_z = 0;
	if (vlen (rdir) < 8) rdir = '0.85 -0.45 0';
	rdir = normalize (rdir);

	if (bako_fx_dust_surge > 0)
	{
		pointparticles (bako_fx_dust_surge, p1, rdir * 350 + '0 0 46', 1);
		pointparticles (bako_fx_dust_surge, p2, rdir * 390 + '0 0 46', 1);
	}
	if (bako_fx_collapse_plume > 0)
		pointparticles (bako_fx_collapse_plume, p2 + '0 0 36', rdir * 240 + '0 0 68', 1);
};

void() Bako_TickFox =
{
	local float dt, u, ease, bury_u, rb_dur, rb_scale, p_u, p_s, rub_u, rub_start, clk_s, clk_d, clk_u;
	local float u_low, shear, sh2, drop_eff;
	local entity e, low, hi, active_e;
	local vector pos, pctr, rdir, win, weld_pt, lever, collar, fall_dir, ang_eff, shift_eff;

	if (bako_fox_state == BAKO_ST_INTACT)
		return;

	Bako_MaintainHiddenRoofProps (BAKO_GRP_FOX);
	dt = time - bako_fox_phase_t0;

	// --- PHASE 1: COUPLED 2-PIECE CLOCK TOWER TOPPLE + 8.6s DUST-VEILED COLLAPSE ---
	if (bako_fox_state == BAKO_ST_COLLAPSE)
	{
		low = bako_fox_twr_low;
		hi = bako_fox_twr_hi;

		// Pass A: update all pieces EXCEPT tower_upper (which couples dynamically to tower_lower!)
		e = bako_fox_pieces;
		while (e != world)
		{
			if (e != hi && e.bako_broken == 0 && dt >= e.bako_delay && !e.bako_piece_hidden)
			{
				if (!e.bako_piece_pop)
				{
					e.bako_piece_pop = TRUE;
					e.solid = SOLID_NOT;
					e.movetype = MOVETYPE_NONE;
					pctr = (e.bako_home_min + e.bako_home_max) * 0.5;
					rdir = normalize (pctr - bako_fox_ctr + '120 -120 40');
					if (e == low || e.bako_role == "marquee" || e.bako_role == "facade_s" || e.bako_role == "stagehouse")
					{
						Bako_BigExplosion (pctr, rdir, 0.92, 24000, 0.54, BAKO_GRP_FOX);
					}
					else
					{
						if (bako_fx_charge_pop > 0)
							pointparticles (bako_fx_charge_pop, pctr, rdir * 160, 1);
						if (bako_fx_masonry_burst > 0)
							pointparticles (bako_fx_masonry_burst, pctr, rdir * 190 + '0 0 80', 2);
						Bako_SoundAt (pctr, CHAN_AUTO, "vehicles/car_boom1.wav", 0.90, 0.16, 90 + random () * 14);
						Bako_SafeShake (pctr, 24000, 0.52, 0);
					}
					if (e == low || e.bako_role == "marquee")
						Bako_BurstDebris (pctr, '0.72 -0.68 0.25', 6, 520, 65, BAKO_GRP_FOX);
				}

				u = Bako_Clamp01 ((dt - e.bako_delay) / max (0.5, e.bako_dur));
				if (u < 1.0)
				{
					ease = Bako_EaseGravity24 (u);
					if (e == low)
					{
						// Buckle tower_lower deeply inward & down onto SE Fox corner so tower_upper stays atop collar with ZERO FOX slicing & clears 20th St/trees!
						ang_eff = e.bako_fall_angles * 0.70;
						shift_eff = '-235 125 0';
						drop_eff = e.bako_fall_drop + 430;
					}
					else
					{
						ang_eff = e.bako_fall_angles;
						shift_eff = e.bako_fall_shift;
						drop_eff = e.bako_fall_drop;
					}
					e.angles = e.bako_home_ang + ang_eff * ease;
					pos = e.bako_home_org + shift_eff * ease - '0 0 1' * (drop_eff * ease);
					setorigin (e, pos);

					// Pre-veil landing spot as piece plunges into final 18% of its drop!
					if (u >= 0.82 && time >= e.bako_piece_fx_t)
					{
						e.bako_piece_fx_t = time + 0.42;
						Bako_VeilPieceLanding (e, bako_fox_ctr);
					}
					else if (time >= e.bako_piece_fx_t)
					{
						e.bako_piece_fx_t = time + 0.48;
						pctr = (e.absmin + e.absmax) * 0.5;
						rdir = pctr - bako_fox_ctr;
						rdir_z = 0;
						if (vlen (rdir) < 8) rdir = '1 -1 0';
						rdir = normalize (rdir);
						// Avoid long-lived buoyant plumes high in blue sky (>320u) -> ZERO stranded sky puffballs!
						if (pctr_z <= bako_fox_ctr_z + 320)
						{
							if (bako_fx_collapse_plume > 0)
								pointparticles (bako_fx_collapse_plume, pctr, rdir * 210 + '0 0 24', 1);
						}
						else if (bako_fx_rock_dust > 0)
						{
							pointparticles (bako_fx_rock_dust, pctr, rdir * 120 + '0 0 -55', 1);
						}
						if (random () < 0.45 && bako_fx_masonry_burst > 0)
							pointparticles (bako_fx_masonry_burst, pctr, rdir * 220 + '0 0 40', 1);
					}
				}
				else
				{
					if (!e.bako_piece_hit)
					{
						e.bako_piece_hit = TRUE;
						e.bako_piece_bury_t = time;
						e.bako_piece_hit_pos = e.origin;
						e.bako_piece_hit_ang = e.angles;
						Bako_VeilPieceLanding (e, bako_fox_ctr);
						pctr = (e.absmin + e.absmax) * 0.5;
						pctr_z = bako_fox_ctr_z + 28;
						rdir = pctr - bako_fox_ctr;
						rdir_z = 0;
						if (vlen (rdir) < 8) rdir = '0.7 -0.7 0';
						rdir = normalize (rdir);
						if (bako_fx_big_boom > 0 && time >= bako_last_boom_dlight_t)
						{
							bako_last_boom_dlight_t = time + 0.22;
							pointparticles (bako_fx_big_boom, pctr + '0 0 24', rdir * 260 + '0 0 80', 1);
						}
						else if (bako_fx_charge_pop > 0)
							pointparticles (bako_fx_charge_pop, pctr + '0 0 24', rdir * 220 + '0 0 60', 1);
						if (bako_fx_masonry_burst > 0)
							pointparticles (bako_fx_masonry_burst, pctr + '0 0 24', rdir * 260 + '0 0 120', 1);
						Bako_BurstDebris (pctr + '0 0 24', rdir + '0 0 0.25', 3, 560, 75, BAKO_GRP_FOX);
						Bako_SoundAt (pctr, CHAN_AUTO, "vehicles/car_boom2.wav", 0.96, 0.14, 88 + random () * 12);
						Bako_SoundAt (pctr, CHAN_BODY, "break/rock_impact.wav", 0.95, 0.14, 84 + random () * 16);
						Bako_SafeShake (pctr, 24000, 0.92, 220);
					}

					bury_u = Bako_Clamp01 ((time - e.bako_piece_bury_t) / 0.85);
					// Keep heavy dust curtain billowing directly over piece while burying into rubble!
					if (time >= e.bako_piece_fx_t)
					{
						e.bako_piece_fx_t = time + 0.42;
						Bako_VeilPieceLanding (e, bako_fox_ctr);
					}
					setorigin (e, e.bako_piece_hit_pos - '0 0 260' * bury_u);
					e.angles = e.bako_piece_hit_ang + e.bako_fall_angles * (0.05 * bury_u);
					if (bury_u >= 1.0)
					{
						e.bako_piece_hidden = TRUE;
						e.solid = SOLID_NOT;
						e.model = string_null;
						setorigin (e, e.bako_home_org - '0 0 1400');
					}
				}
			}
			e = e.bako_piece_next;
		}

		// Pass B: Dynamically couple tower_upper strictly ON TOP of tower_lower's live rotated collar!
		// Hinges cleanly forward/ahead past u_low=0.48 (ZERO telescoping through red FOX letters!) & buries underground in dust!
		if (hi != world && hi.bako_broken == 0 && !hi.bako_piece_hidden)
		{
			if (low != world && low.bako_broken == 0)
			{
				if (dt >= low.bako_delay)
				{
					if (!hi.bako_piece_pop)
					{
						hi.bako_piece_pop = TRUE;
						hi.solid = SOLID_NOT;
						hi.movetype = MOVETYPE_NONE;
					}
					if (!low.bako_piece_hit)
					{
						u_low = Bako_Clamp01 ((dt - low.bako_delay) / max (0.5, low.bako_dur));
						lever = hi.bako_home_org - low.bako_home_org;
						makevectors (low.angles);
						collar = low.origin + v_forward * lever_x - v_right * lever_y + v_up * lever_z;

						// Strictly atop collar (ZERO downward plunge into tower_lower/FOX!); hinges forward/ahead past u_low=0.48!
						if (u_low <= 0.48)
						{
							hi.angles = low.angles + '3 0 2' * (u_low / 0.48);
							setorigin (hi, collar);
						}
						else
						{
							shear = (u_low - 0.48) / 0.52;
							sh2 = shear * shear;
							fall_dir = v_up;
							fall_dir_z = 0;
							if (vlen (fall_dir) > 0.05) fall_dir = normalize (fall_dir);
							else fall_dir = '0.9 -0.3 0';
							hi.angles = low.angles + '3 0 2' + '16 2 5' * sh2;
							pos = collar + fall_dir * (26 * sh2);
							setorigin (hi, pos);
						}

						if (time >= hi.bako_piece_fx_t)
						{
							if (u_low >= 0.68)
							{
								hi.bako_piece_fx_t = time + 0.34;
								Bako_VeilFoxTowerUpper (hi, bako_fox_ctr);
							}
							else
							{
								// Brief falling stucco dust strictly at the moving fracture collar (ZERO high sky puffball!)
								hi.bako_piece_fx_t = time + 0.48;
								if (bako_fx_rock_dust > 0)
									pointparticles (bako_fx_rock_dust, collar, '70 -50 -95', 1);
								if (u_low >= 0.38 && random () < 0.55 && bako_fx_masonry_burst > 0)
									pointparticles (bako_fx_masonry_burst, collar, '120 -80 -60', 1);
							}
						}
					}
					else
					{
						// Slam & continuous dome-tip dust-veiled bury completely underground BEFORE hide!
						if (!hi.bako_piece_hit)
						{
							hi.bako_piece_hit = TRUE;
							hi.bako_piece_bury_t = time;
							hi.bako_piece_hit_pos = hi.origin;
							hi.bako_piece_hit_ang = hi.angles;
							Bako_VeilFoxTowerUpper (hi, bako_fox_ctr);
							makevectors (hi.angles);
							Bako_BurstDebris (hi.origin + v_up * 320, '0.72 -0.68 0.25', 3, 520, 65, BAKO_GRP_FOX);
						}
						bury_u = Bako_Clamp01 ((time - hi.bako_piece_bury_t) / 0.72);
						setorigin (hi, hi.bako_piece_hit_pos - '0 0 420' * bury_u);
						hi.angles = hi.bako_piece_hit_ang + '8 0 3' * bury_u;
						if (time >= hi.bako_piece_fx_t)
						{
							hi.bako_piece_fx_t = time + 0.34;
							Bako_VeilFoxTowerUpper (hi, bako_fox_ctr);
						}
						if (bury_u >= 1.0)
						{
							hi.bako_piece_hidden = TRUE;
							hi.solid = SOLID_NOT;
							hi.model = string_null;
							setorigin (hi, hi.bako_home_org - '0 0 1400');
						}
					}
				}
			}
		}

		// Rise climbable organic Fox ruin ONLY AFTER tower_upper's blue dome has plunged underground (ZERO dual domes!)
		rub_start = (low != world && low.bako_broken == 0) ? (low.bako_delay + low.bako_dur + 0.50) : (bako_fox_collapse_dur * 0.62);
		if (dt >= rub_start)
		{
			rub_u = Bako_Clamp01 ((dt - rub_start) / 1.00);
			Bako_PositionRubbleList (bako_fox_rubble_list, rub_u, (rub_u >= 0.98));
			if (rub_u >= 0.98 && !bako_fox_rubble_up)
			{
				bako_fox_rubble_up = TRUE;
				if (bako_fox_rubble_list != world)
					Bako_EmitDustRing (bako_fox_ctr, bako_fox_rubble_list.bako_home_min, bako_fox_rubble_list.bako_home_max, 420);
			}
		}

		// Ground-hugging radial street base surge down H St & 20th St during heavy slams
		if (dt >= 3.2 && dt <= bako_fox_collapse_dur - 0.4 && time >= bako_fox_fx_t)
		{
			bako_fox_fx_t = time + 0.90;
			if (bako_fox_rubble_list != world)
				Bako_EmitDustRing (bako_fox_ctr, bako_fox_rubble_list.bako_home_min, bako_fox_rubble_list.bako_home_max, 400);
		}

		if (dt >= bako_fox_collapse_dur)
		{
			Bako_HidePieceList (bako_fox_pieces);
			Bako_PositionRubbleList (bako_fox_rubble_list, 1.0, TRUE);
			bako_fox_state = BAKO_ST_RUBBLE;
			bako_fox_phase_t0 = time;
			Bako_SetToast (4, 4.5);
		}
		return;
	}

	// --- PHASE 2: CLIMBABLE RUBBLE MOUND (dust stops cleanly by dt=1.2s so rubble is crystal clear!) ---
	if (bako_fox_state == BAKO_ST_RUBBLE)
	{
		if (dt < 1.2 && time >= bako_fox_fx_t)
		{
			bako_fox_fx_t = time + 0.70;
			if (bako_fx_rock_dust > 0)
				pointparticles (bako_fx_rock_dust, bako_fox_ctr + '0 0 56', '0 0 28', 1);
		}
		if (autocvar_bako_auto_rebuild && dt >= max (10, autocvar_bako_fox_rubble_t))
			Bako_StartFoxRebuild ();
		return;
	}

	// --- PHASE 3: STRICT UPRIGHT BOTTOM-UP 25s REBUILD (FULL UNDERGROUND RISE + SMOOTH CUPOLA FADE-IN!) ---
	if (bako_fox_state == BAKO_ST_REBUILD)
	{
		rb_dur = max (10, autocvar_bako_fox_rebuild_t);
		rb_scale = rb_dur / 25.0;

		if (dt <= 3.5 * rb_scale)
		{
			// Smoothly sink full 341u Fox rubble mound completely flush underground (-365u) with hydraulic clearing rumble!
			p_s = Bako_EaseSmooth (dt / (3.5 * rb_scale));
			e = bako_fox_rubble_list;
			while (e != world)
			{
				if (e.model == string_null || e.model == "")
					setmodel (e, e.mdl);
				e.solid = SOLID_NOT;
				e.movetype = MOVETYPE_PUSH;
				e.angles = e.bako_home_ang;
				setorigin (e, e.bako_home_org - '0 0 365' * p_s);
				e = e.bako_rubble_next;
			}
			if (time >= bako_fox_rb_snd_t)
			{
				bako_fox_rb_snd_t = time + 0.35;
				if (bako_fx_rock_dust > 0)
				{
					pointparticles (bako_fx_rock_dust, bako_fox_ctr + '140 -120 32', '60 -40 42', 2);
					pointparticles (bako_fx_rock_dust, bako_fox_ctr + '-120 100 32', '-50 40 42', 2);
				}
			}
			if (time >= bako_fox_rb_clank_t)
			{
				bako_fox_rb_clank_t = time + 0.85;
				Bako_SoundAt (bako_fox_ctr + '0 0 80', CHAN_BODY, "break/rock_impact.wav", 0.58, 0.18, 64 + random () * 10);
				Bako_SoundAt (bako_fox_ctr + '0 0 80', CHAN_AUTO, "vehicles/clang1.wav", 0.46, 0.18, 70 + random () * 10);
				Bako_SafeShake (bako_fox_ctr, 3000, 0.20, 0);
			}
		}
		else if (bako_fox_rubble_list != world && bako_fox_rubble_list.model != string_null)
		{
			Bako_HideRubbleList (bako_fox_rubble_list);
		}

		active_e = world;
		e = bako_fox_pieces;
		while (e != world)
		{
			win = Bako_FoxRebuildWindow (e, rb_scale);
			if (dt >= win_x)
			{
				if (!e.bako_piece_rb_vis)
				{
					e.bako_piece_rb_vis = TRUE;
					e.angles = e.bako_home_ang;
					setorigin (e, e.bako_home_org - '0 0 1' * win_z);
					e.alpha = (e == bako_fox_twr_hi) ? 0.02 : 0;
					setmodel (e, e.mdl);
				}
				p_u = Bako_Clamp01 ((dt - win_x) / max (0.4, win_y));
				p_s = Bako_EaseSmooth (p_u);

				if (p_u < 1.0)
				{
					active_e = e;
					e.angles = e.bako_home_ang;
					setorigin (e, e.bako_home_org - '0 0 1' * (win_z * (1.0 - p_s)));
					if (e == bako_fox_twr_hi)
					{
						if (p_u < 0.62)
							e.alpha = bound (0.02, p_u / 0.62, 1.0);
						else
							e.alpha = 0;
					}
				}
				else if (!e.bako_piece_rb_done)
				{
					e.bako_piece_rb_done = TRUE;
					e.angles = e.bako_home_ang;
					e.alpha = 0;
					setorigin (e, e.bako_home_org);
					e.movetype = MOVETYPE_PUSH;
					e.solid = SOLID_BSP;
					Bako_NudgePlayersClear (e, bako_fox_ctr);
					pctr = (e.bako_home_min + e.bako_home_max) * 0.5;
					if (bako_fx_rebuild_weld > 0)
					{
						pointparticles (bako_fx_rebuild_weld, pctr, '80 -80 100', 2);
						pointparticles (bako_fx_rebuild_weld, e.bako_home_org + '0 0 40', '90 -90 85', 2);
					}
					Bako_SoundAt (pctr, CHAN_AUTO, "hammer/hammer_clang.wav", 0.92, 0.16, 94 + random () * 14);
				}
			}
			e = e.bako_piece_next;
		}

		// Stage 4b (23.4 .. 24.6s): Clock faces smoothly rise & spark-lock into belfry with bell chime!
		clk_s = 23.4 * rb_scale;
		clk_d = 1.2 * rb_scale;
		if (bako_fox_clock_ent != world && dt >= clk_s)
		{
			if (!bako_fox_clock_rb_vis)
			{
				bako_fox_clock_rb_vis = TRUE;
				bako_fox_clock_ent.angles = bako_fox_clock_ent.bako_home_ang;
				bako_fox_clock_ent.alpha = 0.04;
				setmodel (bako_fox_clock_ent, bako_fox_clock_ent.mdl);
			}
			clk_u = Bako_Clamp01 ((dt - clk_s) / max (0.3, clk_d));
			p_s = Bako_EaseSmooth (clk_u);
			setorigin (bako_fox_clock_ent, bako_fox_clock_ent.bako_home_org - '0 0 48' * (1.0 - p_s));
			if (clk_u < 0.45)
				bako_fox_clock_ent.alpha = bound (0.04, clk_u / 0.45, 1.0);
			else
				bako_fox_clock_ent.alpha = 0;
			if (clk_u >= 1.0 && !bako_fox_clock_rb_done)
			{
				bako_fox_clock_rb_done = TRUE;
				bako_fox_clock_ent.alpha = 0;
				setorigin (bako_fox_clock_ent, bako_fox_clock_ent.bako_home_org);
				pctr = (bako_fox_clock_ent.bako_home_min + bako_fox_clock_ent.bako_home_max) * 0.5;
				if (bako_fx_rebuild_weld > 0)
					pointparticles (bako_fx_rebuild_weld, pctr, '120 -120 90', 3);
				if (bako_fx_sign_sparks > 0)
					pointparticles (bako_fx_sign_sparks, pctr, '110 -110 80', 2);
				Bako_SoundAt (pctr, CHAN_VOICE, "bikes/bell_ring.wav", 1.0, ATTN_NONE, 100);
				Bako_SoundAt (pctr, CHAN_AUTO, "misc/medkey.wav", 0.90, ATTN_NONE, 104);
			}
		}

		// Continuous golden welding sparks along EVERY currently rising piece (marquee, facades, tower_lower, tower_upper!)
		if (dt >= 3.4 * rb_scale && time >= bako_fox_rb_snd_t)
		{
			bako_fox_rb_snd_t = time + 0.45;
			e = bako_fox_pieces;
			while (e != world)
			{
				if (e.bako_piece_rb_vis && !e.bako_piece_rb_done)
				{
					// Bias spark position toward the visible SE street face (max_x / min_y) so sparks pop cleanly!
					weld_pt_x = e.absmin_x + (0.45 + random () * 0.55) * max (32, e.absmax_x - e.absmin_x);
					weld_pt_y = e.absmin_y + (random () * 0.55) * max (32, e.absmax_y - e.absmin_y);
					weld_pt_z = max (bako_fox_ctr_z + 24, e.absmin_z + (0.15 + random () * 0.55) * max (32, e.absmax_z - e.absmin_z));
					if (bako_fx_rebuild_weld > 0)
						pointparticles (bako_fx_rebuild_weld, weld_pt, '95 -95 95', 1);
					if (bako_fx_rock_dust > 0)
						pointparticles (bako_fx_rock_dust, weld_pt - '0 0 20', '45 -45 38', 1);
					// Golden collar-seam weld sparks while cupola gently lowers & fades in above FOX!
					if (e == bako_fox_twr_hi && bako_fx_rebuild_weld > 0)
						pointparticles (bako_fx_rebuild_weld, e.bako_home_org + '48 -48 12', '110 -110 85', 1);
				}
				e = e.bako_piece_next;
			}
		}
		if (dt >= 3.4 * rb_scale && time >= bako_fox_rb_clank_t)
		{
			bako_fox_rb_clank_t = time + 0.85 + random () * 0.45;
			pctr = (active_e != world) ? ((active_e.absmin + active_e.absmax) * 0.5) : (bako_fox_ctr + '0 0 240');
			if (random () < 0.35)
				Bako_SoundAt (pctr, CHAN_AUTO, "hammer/hammer_clang.wav", 0.82, 0.16, 94 + random () * 16);
			else if (random () < 0.70)
				Bako_SoundAt (pctr, CHAN_AUTO, "hammer/hammer_clang2.wav", 0.80, 0.16, 90 + random () * 18);
			else
				Bako_SoundAt (pctr, CHAN_AUTO, "misc/spark.wav", 0.78, 0.16, 96 + random () * 16);
		}

		if (dt >= rb_dur)
		{
			Bako_ResetFoxIntact ();
			Bako_SetToast (7, 4.0);
		}
	}
};

// Central & SE-front warm-tan matte dust curtain across Padre footprint (closes twin-column center gap!)
void(float heavy) Bako_EmitPadreCenterVeil =
{
	local vector base;

	if (time < bako_padre_veil_t)
		return;
	bako_padre_veil_t = time + 0.55;

	base = bako_padre_ctr;
	base_z = bako_padre_bmin_z + 24;

	if (bako_fx_dust_surge > 0)
	{
		pointparticles (bako_fx_dust_surge, base + '0 0 18', '180 -180 48', 1);
		pointparticles (bako_fx_dust_surge, base + '180 -160 12', '340 -260 44', 1);
		if (heavy)
			pointparticles (bako_fx_dust_surge, base + '-110 80 18', '-220 180 48', 1);
	}
	if (bako_fx_collapse_plume > 0)
		pointparticles (bako_fx_collapse_plume, base + '90 -90 64', '160 -160 58', 1);
};

void() Bako_TickPadre =
{
	local float dt, u, ease, bury_u, pop_t, rub_u, rb_dur, span_t, start_t, p_u, p_s, rate, f_bay;
	local float roof_cap_z, drop_eff, min_drop, prog, rpick, rvol;
	local entity e, t4, cr;
	local vector pos, pctr, pop_org, rdir, vpos, lever, collar;

	// Escalating persistent dark-grey rising window smoke vents right on visible outer East & South facades!
	if (bako_padre_state == BAKO_ST_INTACT)
	{
		if (bako_padre_ms != 0 && time >= bako_padre_smoke_t)
		{
			rate = 0.38;
			if (bako_padre_ms & 4) rate = 0.20;
			else if (bako_padre_ms & 2) rate = 0.28;
			bako_padre_smoke_t = time + rate;

			// 2F visible East (H St) window smoke vent (active from 75% down)
			vpos_x = bako_padre_bmax_x + 14;
			vpos_y = bako_padre_bmin_y + 180 + random () * 720;
			vpos_z = bako_padre_bmin_z + 280 + random () * 70;
			if (bako_fx_window_smoke > 0)
				pointparticles (bako_fx_window_smoke, vpos, '85 -25 65', 1);

			// 4F visible South (18th St) window smoke vent (active from 50% down)
			if (bako_padre_ms & 2)
			{
				vpos_x = bako_padre_bmin_x + 220 + random () * 820;
				vpos_y = bako_padre_bmin_y - 14;
				vpos_z = bako_padre_bmin_z + 500 + random () * 70;
				if (bako_fx_window_smoke > 0)
					pointparticles (bako_fx_window_smoke, vpos, '25 -85 68', 1);
			}

			// 6F upper smoke vents + shedding mortar chips (strictly <= 755u, well below roof/crown!)
			if (bako_padre_ms & 4)
			{
				vpos_x = bako_padre_bmax_x + 14;
				vpos_y = bako_padre_bmin_y + 140 + random () * 680;
				vpos_z = bako_padre_bmin_z + 670 + random () * 65;
				if (bako_fx_window_smoke > 0)
					pointparticles (bako_fx_window_smoke, vpos, '95 -35 62', 2);
				if (random () < 0.40 && bako_fx_masonry_burst > 0)
					pointparticles (bako_fx_masonry_burst, vpos - '0 0 60', '110 -70 20', 1);
			}
		}
		return;
	}

	Bako_MaintainHiddenRoofProps (BAKO_GRP_PADRE);
	dt = time - bako_padre_phase_t0;

	// --- PHASE 1: 12s CONTROLLED DEMOLITION INWARD V-COLLAPSE ---
	if (bako_padre_state == BAKO_ST_COLLAPSE)
	{
		t4 = bako_padre_t4;
		cr = bako_padre_crown;
		// Live roof Z cap: ALL Padre collapse smoke/explosions stay strictly below the live descending roof!
		roof_cap_z = bako_padre_bmin_z + 220;
		if (t4 != world && t4.bako_broken == 0 && !t4.bako_piece_hidden)
			roof_cap_z = max (bako_padre_bmin_z + 180, t4.origin_z + 120);
		else
		{
			e = bako_padre_pieces;
			while (e != world)
			{
				if (e.bako_broken == 0 && !e.bako_piece_hidden && e.absmax_z > roof_cap_z)
					roof_cap_z = e.absmax_z;
				e = e.bako_piece_next;
			}
		}

		// Beat 1 (0.05 .. 2.05s): 10 crisp, non-clipping 1F-3F charge pops marching along outer East & South bays!
		pop_t = 0.05 + bako_padre_pop_idx * 0.20;
		if (bako_padre_pop_idx < 10 && dt >= pop_t)
		{
			if (bako_padre_pop_idx < 5)
			{
				f_bay = bako_padre_pop_idx / 4.0;
				pop_org_x = bako_padre_bmax_x + 18;
				pop_org_y = bako_padre_bmin_y + 90 + f_bay * max (200, (bako_padre_bmax_y - bako_padre_bmin_y) - 240);
				rdir = '1 -0.25 0';
			}
			else
			{
				f_bay = (bako_padre_pop_idx - 5) / 4.0;
				pop_org_x = bako_padre_bmax_x - 80 - f_bay * max (200, (bako_padre_bmax_x - bako_padre_bmin_x) - 220);
				pop_org_y = bako_padre_bmin_y - 18;
				rdir = '0.25 -1 0';
			}
			rdir = normalize (rdir);
			pop_org_z = bako_padre_bmin_z + 92 + (bako_padre_pop_idx - 3 * floor (bako_padre_pop_idx / 3)) * 105;
			pop_org_z = min (pop_org_z, max (bako_padre_bmin_z + 92, roof_cap_z - 90));
			bako_padre_pop_idx = bako_padre_pop_idx + 1;

			if (bako_fx_big_boom > 0 && !(bako_padre_pop_idx & 1))
				pointparticles (bako_fx_big_boom, pop_org, rdir * 290 + '0 0 42', 1);
			if (bako_fx_charge_pop > 0)
				pointparticles (bako_fx_charge_pop, pop_org, rdir * 290 + '0 0 28', 2);
			if (bako_fx_masonry_burst > 0)
				pointparticles (bako_fx_masonry_burst, pop_org, rdir * 280 + '0 0 85', 1);
			if (bako_fx_glass_sparkle > 0)
				pointparticles (bako_fx_glass_sparkle, pop_org, rdir * 220 + '0 0 55', 1);
			Bako_SpawnMasonryChunk (pop_org, rdir * 340 + '0 0 140', 0.65 + random () * 0.35, 10.0, bako_padre_pop_idx, BAKO_GRP_PADRE);
			Bako_SpawnGlassShard (pop_org, rdir * 260 + '0 0 120', 1.00 + random () * 0.35, bako_padre_pop_idx);
			Bako_SoundAt (pop_org, CHAN_AUTO, "weapons/r_exp3.wav", 0.72, 0.22, 92 + random () * 18);
			Bako_SafeShake (pop_org, 24000, 0.42, 0);
		}

		// Mid-collapse multi-point demolition blasts along descending outer East & South faces (strictly below roof_cap_z!)
		if (dt >= 2.8 && dt <= 9.8 && time >= bako_padre_boom_t)
		{
			bako_padre_boom_t = time + 1.25 + random () * 0.30;
			if (random () < 0.5)
			{
				pop_org_x = bako_padre_bmax_x + 18;
				pop_org_y = bako_padre_bmin_y + 120 + random () * max (100, (bako_padre_bmax_y - bako_padre_bmin_y) - 240);
				rdir = '1 -0.2 0.1';
			}
			else
			{
				pop_org_x = bako_padre_bmin_x + 140 + random () * max (100, (bako_padre_bmax_x - bako_padre_bmin_x) - 260);
				pop_org_y = bako_padre_bmin_y - 18;
				rdir = '0.2 -1 0.1';
			}
			pop_org_z = bound (bako_padre_bmin_z + 64, bako_padre_bmin_z + 110 + random () * max (40, roof_cap_z - bako_padre_bmin_z - 210), max (bako_padre_bmin_z + 96, roof_cap_z - 90));
			Bako_BigExplosion (pop_org, rdir, 0.90, 24000, 0.56, BAKO_GRP_PADRE);
		}

		// Continuous mid-collapse structural concrete-crushing rumble ticker (ZERO 2-second dead-air dropout!)
		if (dt >= 2.55 && dt <= bako_padre_collapse_dur - 0.75 && time >= bako_padre_rumble_t)
		{
			bako_padre_rumble_t = time + 1.00 + random () * 0.24;
			prog = Bako_Clamp01 ((dt - 2.5) / max (1.0, bako_padre_collapse_dur - 3.5));
			rvol = 0.62 + 0.30 * prog;
			rpick = floor (random () * 4);
			if (rpick < 1)
				Bako_SoundAt (bako_padre_ctr + '0 0 160', CHAN_BODY, "break/rock_impact.wav", rvol, 0.16, 68 + random () * 14);
			else if (rpick < 2)
				Bako_SoundAt (bako_padre_ctr + '0 0 160', CHAN_AUTO, "vehicles/car_boom1.wav", rvol * 0.92, 0.16, 72 + random () * 12);
			else if (rpick < 3)
				Bako_SoundAt (bako_padre_ctr + '0 0 160', CHAN_ITEM, "vehicles/clang2.wav", rvol * 0.86, 0.18, 68 + random () * 14);
			else
				Bako_SoundAt (bako_padre_ctr + '0 0 160', CHAN_AUTO, "weapons/explodedist.wav", rvol * 0.88, 0.14, 80 + random () * 12);
			Bako_SafeShake (bako_padre_ctr, 24000, 0.38 + 0.28 * prog, 0);
		}

		// Beat 2A (1.8 .. 11.8s): Multi-tier inward V-collapse (all pieces EXCEPT crown, which couples to tier4!)
		// Guaranteed full underground plunge for EVERY piece BEFORE hide -> ZERO pop-swaps!
		e = bako_padre_pieces;
		while (e != world)
		{
			if (e != cr && e.bako_broken == 0 && dt >= e.bako_delay && !e.bako_piece_hidden)
			{
				if (!e.bako_piece_pop)
				{
					e.bako_piece_pop = TRUE;
					e.solid = SOLID_NOT;
					e.movetype = MOVETYPE_NONE;
					pctr = (e.bako_home_min + e.bako_home_max) * 0.5;
					pctr_z = min (pctr_z, max (bako_padre_bmin_z + 80, roof_cap_z - 90));
					rdir = pctr - bako_padre_ctr;
					rdir_z = 0;
					if (vlen (rdir) < 8) rdir = '0.7 -0.7 0';
					rdir = normalize (rdir);
					if (bako_fx_charge_pop > 0)
						pointparticles (bako_fx_charge_pop, pctr, rdir * 220 + '0 0 24', 1);
					if (bako_fx_collapse_plume > 0)
						pointparticles (bako_fx_collapse_plume, pctr, rdir * 300 + '0 0 14', 2);
					Bako_SoundAt (pctr, CHAN_AUTO, "vehicles/car_boom1.wav", 0.68, 0.22, 84 + random () * 14);
					Bako_SafeShake (pctr, 24000, 0.48, 0);
				}

				// Ensure every piece reaches deep into the rubble by u=1.0 and 100% underground by bury_u=1.0!
				if (e == t4)
					drop_eff = max (e.bako_fall_drop + 320, (e.bako_home_max_z - bako_padre_bmin_z) + 120);
				else
				{
					min_drop = (e.bako_home_max_z - bako_padre_bmin_z) - 90;
					drop_eff = max (e.bako_fall_drop, min_drop);
				}

				u = Bako_Clamp01 ((dt - e.bako_delay) / max (0.6, e.bako_dur));
				if (u < 1.0)
				{
					ease = Bako_EaseGravity24 (u);
					e.angles = e.bako_home_ang + e.bako_fall_angles * ease;
					pos = e.bako_home_org + e.bako_fall_shift * ease - '0 0 1' * (drop_eff * ease);
					setorigin (e, pos);

					// Horizontal upper floor-seam piston dust jets strictly clamped below live descending roofline!
					if (time >= e.bako_piece_fx_t)
					{
						e.bako_piece_fx_t = time + 0.48;
						pctr = (e.absmin + e.absmax) * 0.5;
						if (random () < 0.5)
						{
							vpos_x = bako_padre_bmax_x + 12;
							vpos_y = bako_padre_bmin_y + 120 + random () * max (100, (bako_padre_bmax_y - bako_padre_bmin_y) - 240);
							rdir = '1 -0.15 0';
						}
						else
						{
							vpos_x = bako_padre_bmin_x + 140 + random () * max (100, (bako_padre_bmax_x - bako_padre_bmin_x) - 260);
							vpos_y = bako_padre_bmin_y - 12;
							rdir = '0.15 -1 0';
						}
						vpos_z = bound (bako_padre_bmin_z + 48, pctr_z, max (bako_padre_bmin_z + 64, roof_cap_z - 100));
						rdir = normalize (rdir);
						if (bako_fx_collapse_plume > 0)
							pointparticles (bako_fx_collapse_plume, vpos, rdir * 380 + '0 0 4', 1);
						if (random () < 0.40 && bako_fx_masonry_burst > 0)
							pointparticles (bako_fx_masonry_burst, vpos, rdir * 270 + '0 0 55', 1);
						if (random () < 0.20)
							Bako_SpawnMasonryChunk (vpos, rdir * 330 + '0 0 95', 0.62 + random () * 0.42, 5.5, floor (random () * 4), BAKO_GRP_PADRE);
					}
				}
				else
				{
					if (!e.bako_piece_hit)
					{
						e.bako_piece_hit = TRUE;
						e.bako_piece_bury_t = time;
						e.bako_piece_hit_pos = e.origin;
						e.bako_piece_hit_ang = e.angles;
						Bako_VeilPieceLanding (e, bako_padre_ctr);
						Bako_EmitPadreCenterVeil (TRUE);
						pctr = (e.absmin + e.absmax) * 0.5;
						pctr_z = bako_padre_ctr_z + 32;
						rdir = pctr - bako_padre_ctr;
						rdir_z = 0;
						if (vlen (rdir) < 8) rdir = '0.7 -0.7 0';
						rdir = normalize (rdir);
						if (bako_fx_masonry_burst > 0)
							pointparticles (bako_fx_masonry_burst, pctr + '0 0 32', rdir * 280 + '0 0 95', 1);
						Bako_SoundAt (pctr, CHAN_AUTO, "vehicles/car_boom2.wav", 0.94, 0.12, 82 + random () * 14);
						Bako_SoundAt (pctr, CHAN_BODY, "break/rock_impact.wav", 0.92, 0.14, 80 + random () * 16);
						Bako_SafeShake (pctr, 24000, 0.86, 220);
					}

					bury_u = Bako_Clamp01 ((time - e.bako_piece_bury_t) / 0.85);
					if (time >= e.bako_piece_fx_t)
					{
						e.bako_piece_fx_t = time + 0.48;
						Bako_VeilPieceLanding (e, bako_padre_ctr);
					}
					setorigin (e, e.bako_piece_hit_pos - '0 0 340' * bury_u);
					if (bury_u >= 1.0)
					{
						e.bako_piece_hidden = TRUE;
						e.solid = SOLID_NOT;
						e.model = string_null;
						setorigin (e, e.bako_home_org - '0 0 1400');
					}
				}
			}
			e = e.bako_piece_next;
		}

		// Beat 2B: Dynamically couple Padre crown strictly ON TOP of tier4's live rotated roof collar!
		// Crown NEVER slips through tier4's roof slab (ZERO hollow black interior gap) and sinks underground WITH tier4!
		if (cr != world && cr.bako_broken == 0 && !cr.bako_piece_hidden)
		{
			if (t4 != world && t4.bako_broken == 0)
			{
				if (t4.bako_piece_hidden)
				{
					cr.bako_piece_hidden = TRUE;
					cr.solid = SOLID_NOT;
					cr.model = string_null;
					setorigin (cr, cr.bako_home_org - '0 0 1400');
				}
				else if (dt >= t4.bako_delay)
				{
					if (!cr.bako_piece_pop)
					{
						cr.bako_piece_pop = TRUE;
						cr.solid = SOLID_NOT;
						cr.movetype = MOVETYPE_NONE;
					}
					lever = cr.bako_home_org - t4.bako_home_org;
					makevectors (t4.angles);
					collar = t4.origin + v_forward * lever_x - v_right * lever_y + v_up * lever_z;
					cr.angles = t4.angles;
					setorigin (cr, collar);
				}
			}
		}

		// 3 staggered radial boulder waves (24 heavy dark concrete boulders!) with Wave 3 RIGHT AT P3 TOUCHDOWN!
		if (dt >= 4.8 && !(bako_padre_wave_bits & 1))
		{
			bako_padre_wave_bits = bako_padre_wave_bits | 1;
			Bako_SpawnPadreBoulderWave (0);
		}
		if (dt >= 7.8 && !(bako_padre_wave_bits & 2))
		{
			bako_padre_wave_bits = bako_padre_wave_bits | 2;
			Bako_SpawnPadreBoulderWave (1);
			Bako_SafeShake (bako_padre_ctr, 24000, 0.90, 240);
		}
		if (dt >= 10.6 && !(bako_padre_wave_bits & 4))
		{
			bako_padre_wave_bits = bako_padre_wave_bits | 4;
			Bako_SpawnPadreBoulderWave (2);
			Bako_EmitPadreCenterVeil (TRUE);
			Bako_BigExplosion (bako_padre_ctr + '260 -120 72', '0.85 -0.45 0.25', 1.0, 24000, 0, BAKO_GRP_PADRE);
			Bako_BigExplosion (bako_padre_ctr + '-120 -260 72', '-0.45 -0.85 0.25', 0.98, 24000, 0, BAKO_GRP_PADRE);
			Bako_SoundAt (bako_padre_ctr + '0 0 120', CHAN_VOICE, "vehicles/car_boom2.wav", 1.0, ATTN_NONE, 84);
			Bako_SoundAt (bako_padre_ctr + '0 0 120', CHAN_BODY, "weapons/explodedist.wav", 0.96, ATTN_NONE, 86);
			Bako_SafeShake (bako_padre_ctr, 24000, 0.98, 300);
		}

		// Wide ground-hugging radial street base surge (+25% reach down H St & 18th St!) + continuous center veil!
		if (dt >= 4.2 && time >= bako_padre_fx_t)
		{
			bako_padre_fx_t = time + 0.85;
			if (bako_padre_rubble_list != world)
				Bako_EmitDustRing (bako_padre_ctr, bako_padre_rubble_list.bako_home_min, bako_padre_rubble_list.bako_home_max, 570);
			else
				Bako_EmitDustRing (bako_padre_ctr, bako_padre_ctr - '360 360 0', bako_padre_ctr + '360 360 0', 570);
			if (dt >= 5.0)
				Bako_EmitPadreCenterVeil (dt >= 8.0);
		}

		// Rise climbable organic 2-story rubble strictly inside peak matte base surge
		if (dt >= bako_padre_collapse_dur * 0.70)
		{
			rub_u = Bako_Clamp01 ((dt - bako_padre_collapse_dur * 0.70) / 1.75);
			Bako_PositionRubbleList (bako_padre_rubble_list, rub_u, (rub_u >= 0.98));
			bako_padre_rubble_up = (rub_u >= 0.98);
		}

		if (dt >= bako_padre_collapse_dur)
		{
			Bako_HidePieceList (bako_padre_pieces);
			Bako_PositionRubbleList (bako_padre_rubble_list, 1.0, TRUE);
			// Final ground-hugging touchdown base surge + center veil so warm tan dust rolls & lingers 8-10s!
			if (bako_padre_rubble_list != world)
				Bako_EmitDustRing (bako_padre_ctr, bako_padre_rubble_list.bako_home_min, bako_padre_rubble_list.bako_home_max, 580);
			Bako_EmitPadreCenterVeil (TRUE);
			bako_padre_state = BAKO_ST_RUBBLE;
			bako_padre_phase_t0 = time;
			Bako_SetToast (5, 4.5);
		}
		return;
	}

	// --- PHASE 2: CLIMBABLE 2-STORY RUBBLE MOUND (soft street-perimeter settling wisps for 2.2s, zero summit hotspot!) ---
	if (bako_padre_state == BAKO_ST_RUBBLE)
	{
		if (dt < 2.2 && time >= bako_padre_fx_t)
		{
			bako_padre_fx_t = time + 1.0;
			if (bako_padre_rubble_list != world)
				Bako_EmitDustRing (bako_padre_ctr, bako_padre_rubble_list.bako_home_min, bako_padre_rubble_list.bako_home_max, 360);
		}
		if (autocvar_bako_auto_rebuild && dt >= max (10, autocvar_bako_padre_rubble_t))
		{
			Bako_ClearGroupDebris (BAKO_GRP_PADRE);
			bako_padre_state = BAKO_ST_REBUILD;
			bako_padre_phase_t0 = time;
			bako_padre_rb_snd_t = 0;
			e = bako_padre_pieces;
			while (e != world)
			{
				e.solid = SOLID_NOT;
				e.takedamage = DAMAGE_NO;
				e.movetype = MOVETYPE_NONE;
				e.bako_broken = 0;
				e.bako_piece_rb_done = FALSE;
				e.bako_piece_rb_vis = FALSE;
				e.model = string_null;
				e.angles = e.bako_home_ang;
				setorigin (e, e.bako_home_org - '0 0 1400');
				e = e.bako_piece_next;
			}
		}
		return;
	}

	// --- PHASE 3: OPTIONAL STAGED REBUILD (28s, strict visibility order) ---
	if (bako_padre_state == BAKO_ST_REBUILD)
	{
		rb_dur = 28.0;
		if (dt <= 3.2)
			Bako_PositionRubbleList (bako_padre_rubble_list, 1.0 - (dt / 3.2), FALSE);
		else if (bako_padre_rubble_list != world && bako_padre_rubble_list.model != string_null)
			Bako_HideRubbleList (bako_padre_rubble_list);

		span_t = rb_dur - 4.0;
		e = bako_padre_pieces;
		while (e != world)
		{
			start_t = 3.2 + bound (0, (e.bako_rebuild_order - 1) / max (1, bako_padre_piece_cnt), 0.85) * (span_t * 0.65);
			p_u = Bako_Clamp01 ((dt - start_t) / (span_t * 0.34));
			p_s = Bako_EaseSmooth (p_u);
			if (dt >= start_t)
			{
				if (!e.bako_piece_rb_vis)
				{
					e.bako_piece_rb_vis = TRUE;
					e.angles = e.bako_home_ang;
					setmodel (e, e.mdl);
				}
				e.angles = e.bako_home_ang;
				setorigin (e, e.bako_home_org - '0 0 1' * (280 * (1.0 - p_s)));
				if (p_u >= 1.0 && !e.bako_piece_rb_done)
				{
					e.bako_piece_rb_done = TRUE;
					setorigin (e, e.bako_home_org);
					e.movetype = MOVETYPE_PUSH;
					e.solid = SOLID_BSP;
					Bako_NudgePlayersClear (e, bako_padre_ctr);
					Bako_SoundAt (e.bako_home_org, CHAN_AUTO, "hammer/hammer_clang.wav", 0.85, 0.18, 92 + random () * 14);
				}
			}
			e = e.bako_piece_next;
		}
		if (time >= bako_padre_rb_snd_t)
		{
			bako_padre_rb_snd_t = time + 0.45;
			pctr_x = bako_padre_ctr_x + crandom () * 280;
			pctr_y = bako_padre_ctr_y + crandom () * 280;
			pctr_z = bako_padre_ctr_z + 80 + Bako_Clamp01 (dt / rb_dur) * 960;
			if (bako_fx_rebuild_weld > 0)
				pointparticles (bako_fx_rebuild_weld, pctr, '0 0 90', 1);
		}
		if (dt >= rb_dur)
		{
			Bako_ResetPadreIntact ();
			Bako_SoundAt (bako_padre_ctr + '0 0 240', CHAN_VOICE, "bikes/bell_ring.wav", 0.9, ATTN_NONE, 96);
			Bako_SetToast (8, 4.0);
		}
	}
};

// Emit dense warm beige-tan dust veil covering BOTH fallen Sign towers (west & east) AND the 80-ft center span!
void(vector p_west, vector p_east, float spd) Bako_EmitSignFullWidthDust =
{
	Bako_EmitLineDustSurge (p_west, p_east, '0 1 0', 12, spd);
	if (bako_fx_dust_surge > 0)
	{
		// Extra dedicated dust billows right around the foreground West tower AND East tower footprints!
		pointparticles (bako_fx_dust_surge, p_west + '24 -70 22', '-180 -140 36', 2);
		pointparticles (bako_fx_dust_surge, p_west + '24 65 22', '-190 160 36', 2);
		pointparticles (bako_fx_dust_surge, p_west + '-45 0 26', '-260 40 32', 2);
		pointparticles (bako_fx_dust_surge, p_east + '-24 -70 22', '180 -140 36', 2);
		pointparticles (bako_fx_dust_surge, p_east + '-24 65 22', '190 160 36', 2);
		pointparticles (bako_fx_dust_surge, p_east + '45 0 26', '260 40 32', 2);
	}
};

void() Bako_TickSign =
{
	local float dt, impact_t, u, ease, bounce_u, ang_mul, hop_z, rb_dur, p_s, i;
	local entity e;
	local vector pos, slam_pt, p_west, p_east, sp_pt, svel;

	if (bako_sign_state == BAKO_ST_INTACT)
		return;

	dt = time - bako_sign_phase_t0;

	// --- PHASE 1: ACCELERATING TOPPLE + IMMEDIATE 0.52s ELASTIC BOUNCE + DUAL-TOWER WARM TAN DUST ---
	if (bako_sign_state == BAKO_ST_COLLAPSE)
	{
		e = bako_sign_pieces;
		while (e != world)
		{
			if (e.bako_broken == 0 && Bako_IsSignMainSpan (e) && dt >= e.bako_delay)
			{
				impact_t = e.bako_delay + max (0.8, e.bako_dur);
				if (dt < impact_t)
				{
					u = Bako_Clamp01 ((dt - e.bako_delay) / max (0.8, e.bako_dur));
					ease = Bako_EaseGravity24 (u);
					e.angles = e.bako_home_ang + e.bako_fall_angles * ease;
					pos = e.bako_home_org + e.bako_fall_shift * ease - '0 0 1' * (e.bako_fall_drop * ease);
					setorigin (e, pos);

					// Crackling blue-gold neon arcs along both pylons & arch lettering while toppling!
					if (time >= bako_sign_fx_t)
					{
						bako_sign_fx_t = time + 0.16;
						sp_pt_x = e.bako_home_min_x + random () * max (64, e.bako_home_max_x - e.bako_home_min_x);
						sp_pt_y = e.origin_y + 180 * ease;
						sp_pt_z = e.origin_z + 240 * (1.0 - ease * 0.78);
						if (bako_fx_sign_sparks > 0)
							pointparticles (bako_fx_sign_sparks, sp_pt, '0 60 70', 1);
						if (random () < 0.35)
							Bako_SoundAt (sp_pt, CHAN_AUTO, "custom/spark5.wav", 0.72, 0.22, 95 + random () * 24);
						else if (random () < 0.25)
							Bako_SoundAt (sp_pt, CHAN_AUTO, "lan/glass_tink.wav", 0.68, 0.22, 92 + random () * 26);
					}
				}
				else
				{
					p_west = e.bako_home_min;
					p_east = e.bako_home_max;
					p_west_y = bako_sign_ctr_y + 195;
					p_east_y = p_west_y;
					p_west_z = bako_sign_ctr_z + 18;
					p_east_z = p_west_z;
					if (bako_sign_rubble_list != world)
					{
						p_west_x = bako_sign_rubble_list.bako_home_min_x + 36;
						p_east_x = bako_sign_rubble_list.bako_home_max_x - 36;
						p_west_y = (bako_sign_rubble_list.bako_home_min_y + bako_sign_rubble_list.bako_home_max_y) * 0.5;
						p_east_y = p_west_y;
						p_west_z = bako_sign_rubble_list.bako_home_min_z + 18;
						p_east_z = p_west_z;
					}
					slam_pt = (p_west + p_east) * 0.5;

					if (!bako_sign_impacted)
					{
						bako_sign_impacted = TRUE;
						Bako_PurgeStrayFires (bako_sign_ctr, 1500);
						// Full-width 80-ft warm beige-tan street base surge + triple impact explosions!
						Bako_EmitSignFullWidthDust (p_west, p_east, 360);
						Bako_BigExplosion (p_west + '36 0 24', '-0.45 0.85 0.25', 0.96, 24000, 0, BAKO_GRP_SIGN);
						Bako_BigExplosion (p_east + '-36 0 24', '0.45 0.85 0.25', 0.96, 24000, 0, BAKO_GRP_SIGN);
						Bako_BigExplosion (slam_pt + '0 0 28', '0 0.9 0.35', 1.0, 24000, 0, BAKO_GRP_SIGN);
						for (i = 0; i < 6; i = i + 1)
						{
							sp_pt = p_west + (p_east - p_west) * (i / 5.0) + '0 0 22';
							if (bako_fx_sign_sparks > 0)
								pointparticles (bako_fx_sign_sparks, sp_pt, '0 80 120', 2);
							if (bako_fx_glass_sparkle > 0)
								pointparticles (bako_fx_glass_sparkle, sp_pt, '0 90 95', 2);
						}
						// Generous non-burning concrete/stucco chunks & glinting neon glass shards!
						Bako_BurstDebris (p_west + '36 0 26', '-0.45 0.88 0.25', 8, 390, 0, BAKO_GRP_SIGN);
						Bako_BurstDebris (p_east + '-36 0 26', '0.45 0.88 0.25', 8, 390, 0, BAKO_GRP_SIGN);
						Bako_BurstDebris (slam_pt + '0 0 26', '0 1 0.25', 5, 390, max (30, autocvar_bako_sign_rubble_t), BAKO_GRP_SIGN);
						for (i = 0; i < 14; i = i + 1)
						{
							sp_pt = p_west + (p_east - p_west) * (i / 13.0) + '0 0 26';
							svel = ('1 0 0' * crandom () * 220) + ('0 1 0' * (140 + random () * 180)) + ('0 0 1' * (110 + random () * 160));
							Bako_SpawnGlassShard (sp_pt, svel, 0.90 + random () * 0.38, i);
						}

						Bako_SoundAt (slam_pt, CHAN_VOICE, "break/metal_impact.wav", 1.0, ATTN_NONE, 88);
						Bako_SoundAt (slam_pt, CHAN_AUTO, "vehicles/clang2.wav", 1.0, ATTN_NONE, 86);
						Bako_SoundAt (slam_pt, CHAN_BODY, "break/glass_impact.wav", 1.0, 0.14, 104);
						Bako_SoundAt (slam_pt, CHAN_ITEM, "ltgun/zap.wav", 0.92, 0.16, 110);
						Bako_SafeShake (slam_pt, 24000, 0.88, 180);
					}

					// Immediate crisp 0.52s damped elastic street rebound (-88 -> -80 -> -88 -> -85.5 -> -88 deg)!
					bounce_u = Bako_Clamp01 ((dt - impact_t) / 0.52);
					if (bounce_u < 0.65)
					{
						p_s = Bako_SinRad ((bounce_u / 0.65) * 3.1415926);
						ang_mul = 1.0 - 0.091 * p_s;
						hop_z = 14.0 * p_s;
					}
					else
					{
						if (!bako_sign_rebound_clank)
						{
							bako_sign_rebound_clank = TRUE;
							// Second dense dual-tower + full-span warm tan dust veil right before the exact-pose swap!
							Bako_EmitSignFullWidthDust (p_west, p_east, 310);
							Bako_SoundAt (slam_pt, CHAN_AUTO, "vehicles/clang1.wav", 0.90, 0.16, 94);
							Bako_SafeShake (slam_pt, 24000, 0.52, 0);
						}
						p_s = Bako_SinRad (((bounce_u - 0.65) / 0.35) * 3.1415926);
						ang_mul = 1.0 - 0.028 * p_s;
						hop_z = 4.0 * p_s;
					}
					e.angles = e.bako_home_ang + e.bako_fall_angles * ang_mul;
					pos = e.bako_home_org + e.bako_fall_shift - '0 0 1' * (e.bako_fall_drop * ang_mul - hop_z);
					setorigin (e, pos);
				}
			}
			e = e.bako_piece_next;
		}

		if (dt >= bako_sign_collapse_dur)
		{
			Bako_HidePieceList (bako_sign_pieces);
			Bako_PositionRubbleList (bako_sign_rubble_list, 1.0, TRUE);
			bako_sign_state = BAKO_ST_RUBBLE;
			bako_sign_phase_t0 = time;
			Bako_SetToast (6, 4.5);
		}
		return;
	}

	// --- PHASE 2: CLIMBABLE / KART-RAMPABLE FALLEN SIGN (120s) ---
	if (bako_sign_state == BAKO_ST_RUBBLE)
	{
		if (autocvar_bako_auto_rebuild && dt >= max (10, autocvar_bako_sign_rubble_t))
		{
			Bako_ClearGroupDebris (BAKO_GRP_SIGN);
			bako_sign_state = BAKO_ST_REBUILD;
			bako_sign_phase_t0 = time;
			Bako_HideRubbleList (bako_sign_rubble_list);
			e = bako_sign_pieces;
			while (e != world)
			{
				e.solid = SOLID_NOT;
				e.movetype = MOVETYPE_NONE;
				e.bako_broken = 0;
				e.bako_piece_hidden = FALSE;
				if (Bako_IsSignMainSpan (e))
				{
					setmodel (e, e.mdl);
					e.angles = e.bako_home_ang + e.bako_fall_angles;
					setorigin (e, e.bako_home_org + e.bako_fall_shift - '0 0 1' * e.bako_fall_drop);
				}
				else
				{
					e.model = string_null;
					e.angles = e.bako_home_ang;
					setorigin (e, e.bako_home_org + '0 0 120');
				}
				e = e.bako_piece_next;
			}
		}
		return;
	}

	// --- PHASE 3: 10s CRANE HOIST BACK UPRIGHT (span hoists 0..7.5s, tower caps seat cleanly 6.5..10s!) ---
	if (bako_sign_state == BAKO_ST_REBUILD)
	{
		rb_dur = 10.0;
		e = bako_sign_pieces;
		while (e != world)
		{
			if (Bako_IsSignMainSpan (e))
			{
				p_s = Bako_EaseSmooth (Bako_Clamp01 (dt / 7.5));
				e.angles = e.bako_home_ang + e.bako_fall_angles * (1.0 - p_s);
				setorigin (e, e.bako_home_org + (e.bako_fall_shift - '0 0 1' * e.bako_fall_drop) * (1.0 - p_s));
			}
			else if (dt >= 6.5)
			{
				if (e.model == string_null)
					setmodel (e, e.mdl);
				p_s = Bako_EaseSmooth (Bako_Clamp01 ((dt - 6.5) / 3.2));
				e.angles = e.bako_home_ang;
				setorigin (e, e.bako_home_org + '0 0 96' * (1.0 - p_s));
			}
			e = e.bako_piece_next;
		}
		if (time >= bako_sign_fx_t)
		{
			bako_sign_fx_t = time + 0.45;
			if (bako_fx_rebuild_weld > 0)
				pointparticles (bako_fx_rebuild_weld, bako_sign_ctr + '0 0 72', '0 0 80', 1);
		}
		if (dt >= rb_dur)
		{
			Bako_ResetSignIntact ();
			Bako_SoundAt (bako_sign_ctr + '0 0 80', CHAN_VOICE, "bikes/bell_ring.wav", 0.9, ATTN_NONE, 102);
			Bako_SetToast (9, 4.0);
		}
	}
};

// ============================================================================
// 9. SHATTERABLE GLASS (20 CRYSTALLINE TRANSLUCENT SHARDS + COOL SPARKLE + 120s RESPAWN)
// ============================================================================

void(entity g) BakoDestruct_RegisterGlass =
{
	if (!g)
		return;
	BakoDestruct_Precache ();
	g.bako_group = BAKO_GRP_GLASS;
	g.bako_material = BAKO_MAT_GLASS;
	g.bako_home_org = g.origin;
	g.bako_home_min = g.absmin;
	g.bako_home_max = g.absmax;
	g.bako_glass_hp = g.health;
	if (g.bako_glass_hp <= 0)
		g.bako_glass_hp = 15;
	if (g.bako_glass_wait <= 0)
		g.bako_glass_wait = 120;
	if (g.mdl == "" || g.mdl == string_null)
		g.mdl = g.model;

	g.bako_dest_next = bako_dest_head;
	bako_dest_head = g;
	g.bako_glass_next = bako_glass_head;
	bako_glass_head = g;
};

void(entity g) BakoDestruct_OnGlassBreak =
{
	local vector pmin, pmax, pctr, span, out_dir, side_v, sorg, svel;
	local float i, n_shards, spd;

	if (!g || g.style != BTYPE_GLASS)
		return;

	if (g.bako_glass_wait > 0)
	{
		if (g.bako_glass_respawn_t <= 0)
			bako_broken_glass_cnt = bako_broken_glass_cnt + 1;
		g.bako_glass_respawn_t = time + g.bako_glass_wait;
	}

	g.count = 0;
	g.solid = SOLID_NOT;

	pmin = g.bako_home_min;
	pmax = g.bako_home_max;
	if (pmin == VEC_ORIGIN && pmax == VEC_ORIGIN)
	{
		pmin = g.absmin;
		pmax = g.absmax;
	}
	pctr = (pmin + pmax) * 0.5;
	span = pmax - pmin;

	if (g.activate != world)
	{
		out_dir = pctr - g.activate.origin;
		out_dir_z = out_dir_z * 0.35;
		if (vlen (out_dir) > 4)
			out_dir = normalize (out_dir);
		else
			out_dir = '0 1 0';
	}
	else
	{
		if (span_x <= span_y && span_x <= span_z)
			out_dir = '1 0 0';
		else if (span_y <= span_z)
			out_dir = '0 1 0';
		else
			out_dir = '0 0 1';
	}
	side_v_x = 0 - out_dir_y;
	side_v_y = out_dir_x;
	side_v_z = 0;
	if (vlen (side_v) < 0.1)
		side_v = '1 0 0';
	else
		side_v = normalize (side_v);

	// Pure cool silver-white / pale-cyan crystalline glass sparkle mist!
	if (bako_fx_glass_sparkle > 0)
	{
		pointparticles (bako_fx_glass_sparkle, pctr, out_dir * 210 + '0 0 36', 2);
		pointparticles (bako_fx_glass_sparkle, pctr - out_dir * 12, (VEC_ORIGIN - out_dir) * 140 + '0 0 32', 1);
	}

	// Spray 8 faceted semi-translucent crystalline shards (180-380 u/s, smooth ~1.5s fade-out)
	n_shards = 8;
	for (i = 0; i < n_shards; i = i + 1)
	{
		sorg_x = pmin_x + (0.12 + random () * 0.76) * max (4, span_x);
		sorg_y = pmin_y + (0.12 + random () * 0.76) * max (4, span_y);
		sorg_z = pmin_z + (0.12 + random () * 0.76) * max (4, span_z);
		spd = 180 + random () * 200;
		if (i < 6)
		{
			sorg = sorg + out_dir * 6;
			svel = out_dir * spd + side_v * (crandom () * 165) + '0 0 1' * (55 + random () * 140);
		}
		else
		{
			sorg = sorg - out_dir * 6;
			svel = (VEC_ORIGIN - out_dir) * (spd * 0.72) + side_v * (crandom () * 175) + '0 0 1' * (70 + random () * 135);
		}
		Bako_SpawnGlassShard (sorg, svel, 0.82 + random () * 0.46, i);
	}
};

float(entity g, entity other_ent) BakoDestruct_GlassTouchCheck =
{
	if (!g || g.style != BTYPE_GLASS || g.waitmin)
		return FALSE;
	if (other_ent == world)
		return FALSE;
	if (other_ent.veh_kind > 0)
		return TRUE;
	if (other_ent.classname == "player" && other_ent.health > 0 && vlen (other_ent.velocity) > 220)
		return TRUE;
	return FALSE;
};

void(entity g) Bako_RestoreGlassPane =
{
	local entity p;
	local vector gctr;

	if (!g || bm_wasfreed (g))
		return;

	// Never respawn glass inside Padre or Fox footprints while collapsed/rubble/rebuilding!
	gctr = (g.bako_home_min + g.bako_home_max) * 0.5;
	if (bako_padre_state != BAKO_ST_INTACT && bako_padre_bmax != VEC_ORIGIN)
	{
		if (gctr_x >= bako_padre_bmin_x - 96 && gctr_x <= bako_padre_bmax_x + 96
			&& gctr_y >= bako_padre_bmin_y - 96 && gctr_y <= bako_padre_bmax_y + 96
			&& gctr_z >= bako_padre_bmin_z - 32 && gctr_z <= bako_padre_bmax_z + 64)
		{
			g.bako_glass_respawn_t = time + 5.0;
			return;
		}
	}
	if (bako_fox_state != BAKO_ST_INTACT && bako_fox_bmax != VEC_ORIGIN)
	{
		if (gctr_x >= bako_fox_bmin_x - 96 && gctr_x <= bako_fox_bmax_x + 96
			&& gctr_y >= bako_fox_bmin_y - 96 && gctr_y <= bako_fox_bmax_y + 96
			&& gctr_z >= bako_fox_bmin_z - 32 && gctr_z <= bako_fox_bmax_z + 64)
		{
			g.bako_glass_respawn_t = time + 5.0;
			return;
		}
	}

	p = bm_player_head;
	while (p)
	{
		if (p.health > 0)
		{
			if (p.absmax_x > g.bako_home_min_x - 8 && p.absmin_x < g.bako_home_max_x + 8
				&& p.absmax_y > g.bako_home_min_y - 8 && p.absmin_y < g.bako_home_max_y + 8
				&& p.absmax_z > g.bako_home_min_z - 8 && p.absmin_z < g.bako_home_max_z + 8)
			{
				g.bako_glass_respawn_t = time + 2.0;
				return;
			}
		}
		p = p.bm_player_next;
	}

	if (g.bako_glass_respawn_t > 0 && bako_broken_glass_cnt > 0)
		bako_broken_glass_cnt = bako_broken_glass_cnt - 1;
	g.bako_glass_respawn_t = 0;
	g.waitmin = FALSE;
	g.health = g.bako_glass_hp;
	g.count = g.height;
	g.solid = SOLID_BSP;
	g.movetype = MOVETYPE_PUSH;
	setmodel (g, g.mdl);
	setorigin (g, g.bako_home_org);
	setsize (g, g.mins, g.maxs);
	g.takedamage = DAMAGE_AIM;
	g.use = funcbreakable_use;
};

void() Bako_TickGlass =
{
	local entity g, p, v, oself;
	local vector vmin, vmax;

	if (bako_glass_head == world)
		return;

	// Only scan glass respawn timers at 2 Hz and ONLY while at least one pane is broken!
	if (bako_broken_glass_cnt > 0 && time >= bako_glass_resp_t)
	{
		bako_glass_resp_t = time + 0.50;
		g = bako_glass_head;
		while (g != world)
		{
			if (!bm_wasfreed (g))
			{
				if (g.waitmin && g.bako_glass_respawn_t > 0 && time >= g.bako_glass_respawn_t)
					Bako_RestoreGlassPane (g);
			}
			g = g.bako_glass_next;
		}
	}

	if (time < bako_kart_glass_t)
		return;
	bako_kart_glass_t = time + 0.05;

	// Walk active players' driven vehicles O(players) instead of nextent(world) over 1500+ edicts!
	p = bm_player_head;
	while (p != world)
	{
		v = p.veh_van;
		if (v != world && !bm_wasfreed (v) && v.veh_kind > 0 && v.veh_driver == p && vlen (v.velocity) > 80)
		{
			vmin = v.origin + '-58 -58 -8';
			vmax = v.origin + '58 58 64';
			g = bako_glass_head;
			while (g != world)
			{
				if (!bm_wasfreed (g) && !g.waitmin && g.solid != SOLID_NOT)
				{
					if (!(vmax_x < g.absmin_x || vmin_x > g.absmax_x || vmax_y < g.absmin_y || vmin_y > g.absmax_y || vmax_z < g.absmin_z || vmin_z > g.absmax_z))
					{
						oself = self;
						self = g;
						self.activate = v.veh_driver;
						funcbreakable_use ();
						self = oself;
					}
				}
				g = g.bako_glass_next;
			}
		}
		p = p.bm_player_next;
	}
};

void(vector bmin, vector bmax) Bako_RestoreGlassInBox =
{
	local entity g;
	local vector gctr;

	if (bmax == VEC_ORIGIN)
		return;
	g = bako_glass_head;
	while (g != world)
	{
		if (!bm_wasfreed (g) && g.waitmin)
		{
			gctr = (g.bako_home_min + g.bako_home_max) * 0.5;
			if (gctr_x >= bmin_x && gctr_x <= bmax_x
				&& gctr_y >= bmin_y && gctr_y <= bmax_y
				&& gctr_z >= bmin_z && gctr_z <= bmax_z)
				Bako_RestoreGlassPane (g);
		}
		g = g.bako_glass_next;
	}
};

void() Bako_ResetAllGlass =
{
	local entity g;

	g = bako_glass_head;
	while (g != world)
	{
		if (!bm_wasfreed (g) && g.waitmin)
			Bako_RestoreGlassPane (g);
		g = g.bako_glass_next;
	}
	bako_broken_glass_cnt = 0;
};

// ============================================================================
// 10. CONTROLLER LOOP, CORNER HUD STATS & DETERMINISTIC CAPTURE COMMANDS
// ============================================================================

void() Bako_CtrlThink =
{
	self.nextthink = time + 0.05;
	Bako_TickEarlyPieceList (bako_fox_pieces, BAKO_GRP_FOX, bako_fox_ctr, bako_fox_bmin_z);
	Bako_TickEarlyPieceList (bako_padre_pieces, BAKO_GRP_PADRE, bako_padre_ctr, bako_padre_bmin_z);
	Bako_TickEarlyPieceList (bako_sign_pieces, BAKO_GRP_SIGN, bako_sign_ctr, bako_sign_ctr_z);
	Bako_TickFox ();
	Bako_TickPadre ();
	Bako_TickSign ();
};

void() Bako_EnsureCtrl =
{
	bako_present = TRUE;
	if (bako_ctrl != world)
		return;
	bako_ctrl = spawn ();
	bako_ctrl.classname = "bako_destruct_ctrl";
	bako_ctrl.movetype = MOVETYPE_NONE;
	bako_ctrl.solid = SOLID_NOT;
	bako_ctrl.think = Bako_CtrlThink;
	bako_ctrl.nextthink = time + 0.1;
};

// Called EVERY server frame from world.qc:StartFrame -> silky 60 Hz smooth seismic oscillator + glass ticks!
void() BakoDestruct_Frame =
{
	if (bako_present)
		Bako_TickSmoothShake ();
	if (bako_glass_head != world)
		Bako_TickGlass ();
};

void(entity p) BakoDestruct_UpdatePlayerStats =
{
	local float pct, ev, rb_dur, rb_pct;

	if (!bako_present)
	{
		p.bako_st_padre_pct = 101;
		p.bako_st_event = 0;
		return;
	}

	if (bako_padre_pieces == world)
		pct = 101;
	else if (bako_padre_state == BAKO_ST_INTACT)
	{
		if (bako_padre_hp >= bako_padre_max_hp - 1)
			pct = 101;
		else
			pct = bound (1, ceil ((bako_padre_hp / max (1, bako_padre_max_hp)) * 100), 99);
	}
	else if (bako_padre_state == BAKO_ST_COLLAPSE)
		pct = 0;
	else
		pct = 101;
	p.bako_st_padre_pct = pct;

	ev = 0;
	if (bako_padre_state == BAKO_ST_COLLAPSE)
		ev = 2;
	else if (bako_fox_state == BAKO_ST_COLLAPSE)
		ev = 1;
	else if (bako_sign_state == BAKO_ST_COLLAPSE)
		ev = 3;
	else if (bako_fox_state == BAKO_ST_REBUILD)
	{
		rb_dur = max (10, autocvar_bako_fox_rebuild_t);
		rb_pct = bound (0, floor (((time - bako_fox_phase_t0) / rb_dur) * 100), 100);
		ev = 100 + rb_pct;
	}
	else if (bako_toast_code > 0 && time < bako_toast_end)
		ev = bako_toast_code;
	p.bako_st_event = ev;
};

void() Bako_ResetAll =
{
	local entity p;

	bako_toast_code = 0;
	bako_toast_end = 0;
	bako_eq_amp = 0;
	bako_padre_veil_t = 0;
	bako_fox_veil_t = 0;
	bako_last_boom_dlight_t = 0;
	p = bm_player_head;
	while (p)
	{
		p.bako_shake_cur = VEC_ORIGIN;
		p.punchangle = VEC_ORIGIN;
		p = p.bm_player_next;
	}
	Bako_ClearGroupDebris (0);
	Bako_PurgeStrayFires (VEC_ORIGIN, 0);
	if (bako_fox_pieces != world || bako_fox_clock_ent != world)
		Bako_ResetFoxIntact ();
	if (bako_padre_pieces != world)
		Bako_ResetPadreIntact ();
	if (bako_sign_pieces != world)
		Bako_ResetSignIntact ();
	Bako_ResetAllGlass ();
};

void(entity p) Bako_PrintStatus =
{
	local string s;

	s = strcat ("bako_destruct: fox_st=", ftos (bako_fox_state), " fox_stg=", ftos (bako_fox_stage), " fox_hp=", ftos (floor (bako_fox_hp)));
	s = strcat (s, " | padre_st=", ftos (bako_padre_state), " padre_stg=", ftos (bako_padre_stage), " padre_hp=", ftos (floor (bako_padre_hp)));
	s = strcat (s, " | sign_st=", ftos (bako_sign_state), " sign_stg=", ftos (bako_sign_stage), " sign_hp=", ftos (floor (bako_sign_hp)));
	s = strcat (s, " | boulders=", ftos (bako_boulder_count), " shards=", ftos (bako_shard_count));
	s = strcat (s, " | p=", vtos (p.origin), " mt=", ftos (p.movetype), " vz=", ftos (floor (p.velocity_z)), "\n");
	sprint (p, s);
	dprint (s);
};

entity(entity plist, string want_role) Bako_FindPieceByRole =
{
	local entity e;

	e = plist;
	while (e != world)
	{
		if (e.bako_broken == 0 && e.bako_role == want_role)
			return e;
		e = e.bako_piece_next;
	}
	return world;
};

float(entity p, float n) BakoDestruct_ClientCmd =
{
	local string verb, arg, role_arg;
	local float dmg, rad;
	local entity targ;
	local vector hpt;

	if (n < 1 || strtolower (argv (0)) != "bako_cmd")
		return FALSE;

	if (!autocvar_sv_cheats && deathmatch)
	{
		sprint (p, "bako_cmd requires sv_cheats 1\n");
		return TRUE;
	}

	verb = "status";
	arg = "";
	role_arg = "";
	if (n >= 2)
		verb = strtolower (argv (1));
	if (n >= 3)
		arg = strtolower (argv (2));
	if (n >= 4)
		role_arg = strtolower (argv (3));

	if (verb == "trigger_fox")
	{
		if (bako_fox_state != BAKO_ST_INTACT)
			Bako_ResetFoxIntact ();
		Bako_TriggerFoxCollapse ();
		dprint ("bako_cmd: trigger_fox\n");
	}
	else if (verb == "trigger_padre")
	{
		if (bako_padre_state != BAKO_ST_INTACT)
			Bako_ResetPadreIntact ();
		Bako_TriggerPadreCollapse ();
		dprint ("bako_cmd: trigger_padre\n");
	}
	else if (verb == "trigger_sign")
	{
		if (bako_sign_state != BAKO_ST_INTACT)
			Bako_ResetSignIntact ();
		Bako_TriggerSignCollapse ();
		dprint ("bako_cmd: trigger_sign\n");
	}
	else if (verb == "fast_rebuild_fox")
	{
		Bako_SnapCollapsed (BAKO_GRP_FOX);
		Bako_StartFoxRebuild ();
		dprint ("bako_cmd: fast_rebuild_fox\n");
	}
	else if (verb == "reset_all")
	{
		Bako_ResetAll ();
		dprint ("bako_cmd: reset_all\n");
	}
	else if (verb == "state_collapsed")
	{
		if (arg == "fox")
			Bako_SnapCollapsed (BAKO_GRP_FOX);
		else if (arg == "padre")
			Bako_SnapCollapsed (BAKO_GRP_PADRE);
		else if (arg == "sign")
			Bako_SnapCollapsed (BAKO_GRP_SIGN);
		else
			Bako_SnapCollapsed (0);
		dprint (strcat ("bako_cmd: state_collapsed ", arg, "\n"));
	}
	else if (verb == "damage_fox")
	{
		dmg = 165;
		if (n >= 3)
			dmg = stof (argv (2));
		targ = world;
		if (role_arg != "")
			targ = Bako_FindPieceByRole (bako_fox_pieces, role_arg);
		if (targ == world)
			targ = (bako_fox_clock_ent != world && bako_fox_clock_ent.solid != SOLID_NOT) ? bako_fox_clock_ent : bako_fox_pieces;
		if (targ != world)
		{
			hpt = (targ.bako_home_min + targ.bako_home_max) * 0.5;
			BakoDestruct_OnDamage (targ, hpt, p, p, dmg);
		}
		dprint (strcat ("bako_cmd: damage_fox ", ftos (dmg), " role=", role_arg, "\n"));
	}
	else if (verb == "damage_padre")
	{
		dmg = 900;
		if (n >= 3)
			dmg = stof (argv (2));
		targ = world;
		if (role_arg != "")
			targ = Bako_FindPieceByRole (bako_padre_pieces, role_arg);
		if (targ == world)
			targ = bako_padre_pieces;
		if (targ != world)
		{
			hpt = (targ.bako_home_min + targ.bako_home_max) * 0.5;
			BakoDestruct_OnDamage (targ, hpt, p, p, dmg);
		}
		dprint (strcat ("bako_cmd: damage_padre ", ftos (dmg), " role=", role_arg, "\n"));
	}
	else if (verb == "damage_sign")
	{
		dmg = 195;
		if (n >= 3)
			dmg = stof (argv (2));
		targ = world;
		if (role_arg != "")
			targ = Bako_FindPieceByRole (bako_sign_pieces, role_arg);
		if (targ == world)
			targ = bako_sign_pieces;
		if (targ != world)
		{
			hpt = (targ.bako_home_min + targ.bako_home_max) * 0.5;
			BakoDestruct_OnDamage (targ, hpt, p, p, dmg);
		}
		dprint (strcat ("bako_cmd: damage_sign ", ftos (dmg), " role=", role_arg, "\n"));
	}
	else if (verb == "shatter_glass")
	{
		rad = 650;
		if (n >= 3)
			rad = stof (argv (2));
		if (rad <= 0)
			rad = 650;
		Bako_ShatterGlassInRadius (p.origin, rad, p);
		dprint (strcat ("bako_cmd: shatter_glass rad=", ftos (rad), "\n"));
	}
	else if (verb == "warp" && n >= 5 && autocvar_sv_cheats)
	{
		setorigin (p, stof (argv (2)) * '1 0 0' + stof (argv (3)) * '0 1 0' + stof (argv (4)) * '0 0 1');
		p.velocity = VEC_ORIGIN;
		p.flags = p.flags - (p.flags & FL_ONGROUND);
		dprint (strcat ("bako_cmd: warp ", vtos (p.origin), "\n"));
	}
	else
	{
		Bako_PrintStatus (p);
	}
	return TRUE;
};

void() BakoDestruct_Impulse =
{
	if (!bako_present)
		return;
	if (self.impulse < 150 || self.impulse > 155)
		return;
	if (!autocvar_sv_cheats && deathmatch)
		return;

	if (self.impulse == 150)
	{
		if (bako_fox_state != BAKO_ST_INTACT) Bako_ResetFoxIntact ();
		Bako_TriggerFoxCollapse ();
	}
	else if (self.impulse == 151)
	{
		if (bako_padre_state != BAKO_ST_INTACT) Bako_ResetPadreIntact ();
		Bako_TriggerPadreCollapse ();
	}
	else if (self.impulse == 152)
	{
		if (bako_sign_state != BAKO_ST_INTACT) Bako_ResetSignIntact ();
		Bako_TriggerSignCollapse ();
	}
	else if (self.impulse == 153)
	{
		Bako_SnapCollapsed (BAKO_GRP_FOX);
		Bako_StartFoxRebuild ();
	}
	else if (self.impulse == 154)
	{
		Bako_ResetAll ();
	}
	else if (self.impulse == 155)
	{
		Bako_SnapCollapsed (0);
	}
	self.impulse = 0;
};

// ============================================================================
// 11. MAP ENTITY SPAWN FUNCTIONS
// ============================================================================

void(entity attacker, float damage) bako_part_nopain = { self.health = 99999; };
void() bako_part_nodie = { self.health = 99999; };

void(vector mn, vector mx, float grp) Bako_AccumBounds =
{
	if (grp == BAKO_GRP_FOX)
	{
		if (bako_fox_bmin == VEC_ORIGIN && bako_fox_bmax == VEC_ORIGIN)
		{
			bako_fox_bmin = mn;
			bako_fox_bmax = mx;
		}
		else
		{
			if (mn_x < bako_fox_bmin_x) bako_fox_bmin_x = mn_x;
			if (mn_y < bako_fox_bmin_y) bako_fox_bmin_y = mn_y;
			if (mn_z < bako_fox_bmin_z) bako_fox_bmin_z = mn_z;
			if (mx_x > bako_fox_bmax_x) bako_fox_bmax_x = mx_x;
			if (mx_y > bako_fox_bmax_y) bako_fox_bmax_y = mx_y;
			if (mx_z > bako_fox_bmax_z) bako_fox_bmax_z = mx_z;
		}
	}
	else if (grp == BAKO_GRP_PADRE)
	{
		if (bako_padre_bmin == VEC_ORIGIN && bako_padre_bmax == VEC_ORIGIN)
		{
			bako_padre_bmin = mn;
			bako_padre_bmax = mx;
		}
		else
		{
			if (mn_x < bako_padre_bmin_x) bako_padre_bmin_x = mn_x;
			if (mn_y < bako_padre_bmin_y) bako_padre_bmin_y = mn_y;
			if (mn_z < bako_padre_bmin_z) bako_padre_bmin_z = mn_z;
			if (mx_x > bako_padre_bmax_x) bako_padre_bmax_x = mx_x;
			if (mx_y > bako_padre_bmax_y) bako_padre_bmax_y = mx_y;
			if (mx_z > bako_padre_bmax_z) bako_padre_bmax_z = mx_z;
		}
	}
};

void(entity e, float grp, float mat, float shootable) Bako_InitPieceCommon =
{
	BakoDestruct_Precache ();
	Bako_EnsureCtrl ();

	e.bako_group = grp;
	e.bako_material = mat;
	e.solid = SOLID_BSP;
	e.movetype = MOVETYPE_PUSH;
	setmodel (e, e.model);
	e.mdl = e.model;
	e.bako_home_org = e.origin;
	e.bako_home_ang = e.angles;
	setorigin (e, e.bako_home_org);
	e.bako_home_min = e.absmin;
	e.bako_home_max = e.absmax;
	e.health = 99999;
	e.th_pain = bako_part_nopain;
	e.th_die = bako_part_nodie;
	Bako_AccumBounds (e.bako_home_min, e.bako_home_max, grp);

	if (shootable)
	{
		e.takedamage = DAMAGE_AIM;
		e.bako_dest_next = bako_dest_head;
		bako_dest_head = e;
	}
	else
	{
		e.takedamage = DAMAGE_NO;
	}
};

void(entity e, float grp) Bako_InitRubbleCommon =
{
	BakoDestruct_Precache ();
	Bako_EnsureCtrl ();

	e.bako_group = grp;
	e.bako_material = BAKO_MAT_MASONRY;
	e.movetype = MOVETYPE_NONE;
	e.solid = SOLID_NOT;
	setmodel (e, e.model);
	e.mdl = e.model;
	e.bako_home_org = e.origin;
	e.bako_home_ang = e.angles;
	setorigin (e, e.bako_home_org);
	e.bako_home_min = e.absmin;
	e.bako_home_max = e.absmax;
	Bako_AccumBounds (e.bako_home_min, e.bako_home_max, grp);
	e.model = string_null;
	setorigin (e, e.bako_home_org - '0 0 512');
};

// --- Fox Theater ---

void() bako_fox_clock =
{
	local float hp;

	hp = max (self.health, autocvar_bako_fox_clock_hp);
	if (hp <= 0)
		hp = 450;
	self.max_health = hp;
	Bako_InitPieceCommon (self, BAKO_GRP_FOX, BAKO_MAT_GLASS, TRUE);
	bako_fox_clock_ent = self;
	bako_fox_max_hp = hp;
	bako_fox_hp = hp;
	bako_fox_state = BAKO_ST_INTACT;
	if (bako_fox_ctr == VEC_ORIGIN)
	{
		bako_fox_ctr = (self.bako_home_min + self.bako_home_max) * 0.5;
		bako_fox_ctr_z = 0;
	}
};

void() bako_fox_piece =
{
	Bako_InitPieceCommon (self, BAKO_GRP_FOX, BAKO_MAT_MASONRY, TRUE);
	if (self.bako_dur <= 0)
		self.bako_dur = 4.2;
	if (self.bako_fall_angles == VEC_ORIGIN && self.bako_fall_drop == 0)
		self.bako_fall_drop = 260;

	if (self.bako_role == "tower_lower")
		bako_fox_twr_low = self;
	else if (self.bako_role == "tower_upper")
		bako_fox_twr_hi = self;

	bako_fox_piece_cnt = bako_fox_piece_cnt + 1;
	if (self.bako_rebuild_order <= 0)
		self.bako_rebuild_order = bound (1, 1 + floor (max (0, self.bako_home_min_z) / 160), 8);

	self.bako_piece_next = bako_fox_pieces;
	bako_fox_pieces = self;
	bako_fox_state = BAKO_ST_INTACT;
	if (bako_fox_ctr == VEC_ORIGIN)
	{
		bako_fox_ctr = (self.bako_home_min + self.bako_home_max) * 0.5;
		bako_fox_ctr_z = self.bako_home_min_z;
	}
};

void() bako_fox_rubble =
{
	Bako_InitRubbleCommon (self, BAKO_GRP_FOX);
	self.bako_rubble_next = bako_fox_rubble_list;
	bako_fox_rubble_list = self;
	bako_fox_ctr = (self.bako_home_min + self.bako_home_max) * 0.5;
	bako_fox_ctr_z = self.bako_home_min_z;
};

// --- Padre Hotel ---

void() bako_padre_piece =
{
	Bako_InitPieceCommon (self, BAKO_GRP_PADRE, BAKO_MAT_MASONRY, TRUE);
	if (self.bako_dur <= 0)
		self.bako_dur = 5.0;
	if (self.bako_fall_angles == VEC_ORIGIN && self.bako_fall_drop == 0)
		self.bako_fall_drop = 480;

	if (self.bako_role == "tier4")
		bako_padre_t4 = self;
	else if (self.bako_role == "crown")
		bako_padre_crown = self;

	bako_padre_piece_cnt = bako_padre_piece_cnt + 1;
	if (self.bako_rebuild_order <= 0)
		self.bako_rebuild_order = bound (1, 1 + floor (max (0, self.bako_home_min_z) / 180), 8);

	self.bako_piece_next = bako_padre_pieces;
	bako_padre_pieces = self;
	bako_padre_max_hp = max (100, autocvar_bako_padre_hp);
	bako_padre_hp = bako_padre_max_hp;
	bako_padre_state = BAKO_ST_INTACT;
	if (bako_padre_ctr == VEC_ORIGIN)
	{
		bako_padre_ctr = (self.bako_home_min + self.bako_home_max) * 0.5;
		bako_padre_ctr_z = self.bako_home_min_z;
	}
};

void() bako_padre_rubble =
{
	Bako_InitRubbleCommon (self, BAKO_GRP_PADRE);
	self.bako_rubble_next = bako_padre_rubble_list;
	bako_padre_rubble_list = self;
	bako_padre_ctr = (self.bako_home_min + self.bako_home_max) * 0.5;
	bako_padre_ctr_z = self.bako_home_min_z;
};

// --- Bakersfield Sign ---

void() bako_sign_piece =
{
	Bako_InitPieceCommon (self, BAKO_GRP_SIGN, BAKO_MAT_METAL, TRUE);
	if (self.bako_dur <= 0)
		self.bako_dur = 3.6;
	if (self.bako_fall_angles == VEC_ORIGIN)
		self.bako_fall_angles = '0 0 -88';

	bako_sign_piece_cnt = bako_sign_piece_cnt + 1;
	self.bako_piece_next = bako_sign_pieces;
	bako_sign_pieces = self;
	bako_sign_max_hp = max (20, autocvar_bako_sign_hp);
	bako_sign_hp = bako_sign_max_hp;
	bako_sign_state = BAKO_ST_INTACT;
	if (bako_sign_ctr == VEC_ORIGIN || Bako_IsSignMainSpan (self))
	{
		bako_sign_ctr = (self.bako_home_min + self.bako_home_max) * 0.5;
		bako_sign_ctr_z = self.bako_home_min_z;
	}
};

void() bako_sign_rubble =
{
	Bako_InitRubbleCommon (self, BAKO_GRP_SIGN);
	self.bako_rubble_next = bako_sign_rubble_list;
	bako_sign_rubble_list = self;
	if (bako_sign_ctr == VEC_ORIGIN)
	{
		bako_sign_ctr = (self.bako_home_min + self.bako_home_max) * 0.5;
		bako_sign_ctr_z = self.bako_home_min_z;
	}
};

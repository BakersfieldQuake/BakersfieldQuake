#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
SKY LAUNCH PADS (skypad.qc)

High-arc cross-map launch pads (`info_skypad`) that throw players sky-high across downtown
from landmark to landmark along an exact ballistic parabola (`pos1` = landing player origin,
`height` = apex z in map units, `message` = destination name).

Raises `sv_maxvelocity` to 6500 so high cross-map velocities (~3800 u/s horizontal, ~2200 u/s
vertical) are never axis-clamped on either server or client prediction.
================
*/

// the launch needs a higher speed cap than stock; the value from before is kept in bm_maxvel_saved so that BM_Precache
// can put it back on the next map (it used to stay 6500 for the rest of the session, for every map)
void() SkyPad_RaiseMaxVel =
{
	if (cvar ("sv_maxvelocity") >= 6500)
		return;
	registercvar ("bm_maxvel_saved", "0");
	if (cvar ("bm_maxvel_saved") <= 0)
		cvar_set ("bm_maxvel_saved", cvar_string ("sv_maxvelocity"));
	cvar_set ("sv_maxvelocity", "6500");
};

void() SkyPad_Precache =
{
	if (skypad_precached)
		return;
	skypad_precached = TRUE;
	precache_model ("progs/turrbase.mdl");
	precache_model ("progs/ltg_aura.md3");
	precache_model ("progs/aura.md3");
	precache_model ("progs/laser.md3");
	precache_model ("progs/s_dotmed_yell.spr");
	precache_sound ("skypad/launch.wav");
	precache_sound ("weapons/turrset.wav");
};

vector(vector org, vector dst, float apex_z) SkyPad_CalcVel =
{
	local float g, top, vz, tf;
	local vector v;

	g = cvar ("sv_gravity");
	if (g <= 10)
		g = 800;
	top = apex_z;
	if (top < org_z + 256)
		top = org_z + 256;
	if (top < dst_z + 256)
		top = dst_z + 256;
	vz = sqrt (2 * g * (top - org_z));
	tf = (vz / g) + sqrt (2 * (top - dst_z) / g);
	if (tf < 0.2)
		tf = 0.2;
	v_x = (dst_x - org_x) / tf;
	v_y = (dst_y - org_y) / tf;
	v_z = vz;
	return v;
};

// Landing anti-camp shockwave when touching down from a cross-map SkyPad launch!
void() SkyPad_LandWave =
{
	local entity e;
	local vector d;

	pointparticles (particleeffectnum ("TE_TELEPORT"), self.origin - '0 0 18', '0 0 0', 1);
	e = findradius (self.origin, 175);
	while (e != world)
	{
		if (e != self && e.takedamage && e.health > 0 && e.solid == SOLID_SLIDEBOX)
		{
			d = e.origin - self.origin;
			d_z = 0;
			if (vlen (d) < 1)
				d = '1 0 0';
			else
				d = normalize (d);
			e.flags = e.flags - (e.flags & FL_ONGROUND);
			e.velocity = e.velocity + d * 380 + '0 0 220';
			T_Damage (e, self, self, 25);
		}
		e = e.chain;
	}
};

void() SkyPad_Touch =
{
	local vector v;

	if (other.classname != "player")
		return;
	if (other.health <= 0 || other.deadflag != 0)
		return;
	if ((other.movetype != MOVETYPE_WALK && (other.ishuman == 1 || other.movetype != MOVETYPE_NONE)) || Veh_Driving (other) || Veh_Riding (other))
		return;
	if (time < other.skypad_cool_t)
		return;

	SkyPad_RaiseMaxVel ();
	if (other.ishuman == 1 && !other.skypad_vel_sent)
	{
		other.skypad_vel_sent = TRUE;
		stuffcmd (other, "sv_maxvelocity 6500\n");
	}

	other.skypad_cool_t = time + 0.65;
	other.skypad_safe_t = time + 10.0;
	other.flags = other.flags - (other.flags & FL_ONGROUND);
	setorigin (other, other.origin + '0 0 2');

	v = SkyPad_CalcVel (other.origin, self.pos1, self.height);
	other.velocity = v;
	other.jump_flag = 0;

	sound7 (other, CHAN_AUTO, "skypad/launch.wav", 0.78, ATTN_NORM, SNDSPD * (0.96 + random () * 0.08));
	pointparticles (particleeffectnum ("TE_TELEPORT"), self.origin + '0 0 12', '0 0 0', 1);

	if (self.message != "" && other.ishuman == 1)
		sprint (other, strcat ("Sky Pad -> ", self.message, "\n"));
};

void(vector org, vector v_nom) SkyPad_SpawnVisuals =
{
	local entity base, ring, dome, beam, core;
	local float flz;
	local vector dir, p;

	flz = org_z - 26;		// org is resting player origin + 2u (floor + 26u)
	dir = normalize (v_nom);
	p_x = org_x;
	p_y = org_y;

	// 1. Metallic emitter ring base on the sidewalk
	base = spawn ();
	base.classname = "skypad_fx";
	base.movetype = MOVETYPE_NONE;
	base.solid = SOLID_NOT;
	setmodel (base, "progs/turrbase.mdl");
	setsize (base, '0 0 0', '0 0 0');
	base.scale = 1.65;
	base.angles_y = vectoyaw (dir);
	base.effects = EF_FULLBRIGHT;
	base.colormod = '1.25 1.32 1.45';
	p_z = flz + 0.5;
	setorigin (base, p);

	// 2. Animated electric energy ring flush on the pavement
	ring = spawn ();
	ring.classname = "skypad_fx";
	ring.movetype = MOVETYPE_NONE;
	ring.solid = SOLID_NOT;
	setmodel (ring, "progs/ltg_aura.md3");
	setsize (ring, '0 0 0', '0 0 0');
	ring.angles = vectoangles ('0 0 1');
	ring.scale = 1.45;
	ring.effects = EF_FULLBRIGHT | EF_ADDITIVE;
	ring.colormod = '0.30 0.95 1.00';
	ring.alpha = 0.92;
	p_z = flz + 3;
	setorigin (ring, p);

	// 3. Spinning translucent energy vortex dome
	dome = spawn ();
	dome.classname = "skypad_fx";
	dome.movetype = MOVETYPE_NOCLIP;
	dome.solid = SOLID_NOT;
	setmodel (dome, "progs/aura.md3");
	setsize (dome, '0 0 0', '0 0 0');
	dome.scale = 1.15;
	dome.effects = EF_FULLBRIGHT | EF_ADDITIVE;
	dome.colormod = '0.25 0.85 1.00';
	dome.alpha = 0.48;
	dome.avelocity = '0 105 0';
	p_z = flz + 24;
	setorigin (dome, p);

	// 4. Directional trajectory beam pointing along the launch arc
	beam = spawn ();
	beam.classname = "skypad_fx";
	beam.movetype = MOVETYPE_NONE;
	beam.solid = SOLID_NOT;
	setmodel (beam, "progs/laser.md3");
	setsize (beam, '0 0 0', '0 0 0');
	beam.angles = vectoangles (dir);
	beam.scale = 0.85;
	beam.effects = EF_FULLBRIGHT | EF_ADDITIVE;
	beam.colormod = '1.00 0.82 0.25';
	beam.alpha = 0.85;
	p_z = flz + 18;
	setorigin (beam, p);

	// 5. Glowing core sprite casting warm-gold street glow without lightmap rebake
	core = spawn ();
	core.classname = "skypad_fx";
	core.movetype = MOVETYPE_NONE;
	core.solid = SOLID_NOT;
	setmodel (core, "progs/s_dotmed_yell.spr");
	setsize (core, '0 0 0', '0 0 0');
	core.effects = EF_FULLBRIGHT | EF_ADDITIVE;
	core.scale = 1.8;
	core.alpha = 0.85;
	core.pflags = PFLAGS_FULLDYNAMIC | PFLAGS_NOSHADOW | PFLAGS_CORONA;
	core.light_lev = 180;
	core.color = '1 0 0';		// matches palette 251 glow_color without shadow cubemap pass
	p_z = flz + 18;
	setorigin (core, p);
};

void() info_skypad =
{
	local vector v_nom;

	SkyPad_Precache ();
	skypad_present = TRUE;
	SkyPad_RaiseMaxVel ();

	if (!self.height)
		self.height = 2900;

	self.solid = SOLID_TRIGGER;
	self.movetype = MOVETYPE_NONE;
	setorigin (self, self.origin);
	setsize (self, '-40 -40 -26', '40 40 36');
	self.touch = SkyPad_Touch;

	v_nom = SkyPad_CalcVel (self.origin, self.pos1, self.height);
	SkyPad_SpawnVisuals (self.origin, v_nom);
};

void() SkyPad_Report =
{
	local entity e;
	local float n;
	local vector v;

	n = 0;
	e = find (world, classname, "info_skypad");
	while (e)
	{
		n = n + 1;
		v = SkyPad_CalcVel (e.origin, e.pos1, e.height);
		bprint ("skypad #", ftos (n), " -> ", e.message, " org=", vtos (e.origin));
		bprint (" dst=", vtos (e.pos1), " apex=", ftos (e.height), " vel=", vtos (v), "\n");
		e = find (e, classname, "info_skypad");
	}
	bprint ("skypad total=", ftos (n), " sv_maxvelocity=", ftos (cvar ("sv_maxvelocity")), "\n");
};

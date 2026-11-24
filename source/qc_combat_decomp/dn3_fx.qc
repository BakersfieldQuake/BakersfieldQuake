// dn3_fx.qc — Server-side emitter and sound router for DN3DooM blood, gore, fire, and explosion FX.
// Relays lightweight transient ENT_DN3FX SendEntity events to CSQC (0.14s auto-remove, zero persistent server edicts).

void() DN3FX_Precache =
{
	registercvar("bm_dn3fx", "1");

	precache_sound("dn3fx/hflesh.ogg");
	precache_sound("dn3fx/organic1.ogg");
	precache_sound("dn3fx/organic2.ogg");
	precache_sound("dn3fx/dsslop.wav");
	precache_sound("dn3fx/bombexpl.wav");
	precache_sound("dn3fx/fire09.ogg");
	precache_sound("dn3fx/bulithit.ogg");
	precache_sound("dn3fx/ricoche1.wav");
	precache_sound("dn3fx/ricoche2.wav");
	precache_sound("dn3fx/ricoche3.wav");
	precache_sound("dn3fx/ricoche4.wav");
};

float(entity to, float sendFlags) dn3fx_sendtocsqc =
{
	local float sc_byte;

	WriteByte(MSG_ENTITY, ENT_DN3FX);
	WriteByte(MSG_ENTITY, sendFlags);
	if (sendFlags & 1)
	{
		WriteByte(MSG_ENTITY, self.style);
		WriteCoord(MSG_ENTITY, self.origin_x);
		WriteCoord(MSG_ENTITY, self.origin_y);
		WriteCoord(MSG_ENTITY, self.origin_z);
		WriteCoord(MSG_ENTITY, self.velocity_x);
		WriteCoord(MSG_ENTITY, self.velocity_y);
		WriteCoord(MSG_ENTITY, self.velocity_z);
		sc_byte = rint(self.scale * 32.0);
		if (sc_byte < 4)
			sc_byte = 4;
		if (sc_byte > 255)
			sc_byte = 255;
		WriteByte(MSG_ENTITY, sc_byte);
	}
	return TRUE;
};

void(float kind, vector org, vector dir, float sc) DN3FX_Emit =
{
	local entity relay;

	if (!autocvar_bm_dn3fx)
		return;

	relay = spawn();
	relay.classname = "dn3fx_relay";
	relay.style = kind;
	relay.scale = sc;
	relay.velocity = dir;
	setmodel(relay, "progs/s_smoke.spr");
	relay.alpha = 0.001;
	setsize(relay, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(relay, org);
	relay.SendEntity = dn3fx_sendtocsqc;
	relay.think = SUB_Remove;
	relay.nextthink = time + 0.14;
};

void(entity targ, vector org, vector vel, float damage) DN3FX_OnBlood =
{
	local float sc, r;
	local entity snd_ent;

	if (!autocvar_bm_dn3fx)
		return;

	if (targ != world)
	{
		if (targ.lan_kind || targ.dodge_finished >= time || targ.classname == "func_breakable" || targ.classname == "npc_beach_uncle" || targ.classname == "monster_jim" || targ.classname == "ShalrathMissile")
			return;
		if (time < targ.dn3fx_blood_t)
			return;
		targ.dn3fx_blood_t = time + 0.02;
	}

	sc = 0.92 + damage / 24.0;
	if (sc < 0.90)
		sc = 0.90;
	if (sc > 1.75)
		sc = 1.75;

	DN3FX_Emit(DN3FX_BLOOD_HIT, org, vel, sc);

	snd_ent = (targ != world) ? targ : self;
	if (snd_ent != world && time >= snd_ent.dn3fx_hit_snd_t)
	{
		snd_ent.dn3fx_hit_snd_t = time + 0.07;
		r = random();
		if (r < 0.34)
			sound7(snd_ent, CHAN_AUTO, "dn3fx/hflesh.ogg", 0.75, ATTN_NORM, SNDSPD);
		else if (r < 0.67)
			sound7(snd_ent, CHAN_AUTO, "dn3fx/organic1.ogg", 0.75, ATTN_NORM, SNDSPD);
		else
			sound7(snd_ent, CHAN_AUTO, "dn3fx/organic2.ogg", 0.75, ATTN_NORM, SNDSPD);
	}
};

void(entity targ) DN3FX_OnGib =
{
	if (!autocvar_bm_dn3fx || targ == world)
		return;

	DN3FX_Emit(DN3FX_GIB_BURST, targ.origin, '0 0 1', 1.0);
	sound7(targ, CHAN_AUTO, "dn3fx/dsslop.wav", 0.90, ATTN_NORM, SNDSPD);
};

void(entity src, vector org, float sc) DN3FX_OnExplode =
{
	local float pc;

	if (!autocvar_bm_dn3fx)
		return;

	pc = pointcontents(org);
	if (pc == CONTENT_WATER || pc == CONTENT_SLIME)
		return;

	DN3FX_Emit(DN3FX_EXPLODE, org, '0 0 1', sc);
	if (src != world)
	{
		sound7(src, CHAN_AUTO, "dn3fx/bombexpl.wav", 0.72, ATTN_NORM, SNDSPD);
		sound7(src, CHAN_AUTO, "dn3fx/fire09.ogg", 0.42, ATTN_IDLE, SNDSPD);
	}
};

void(vector org, vector dir, float sc, float with_sound) DN3FX_OnFire =
{
	if (!autocvar_bm_dn3fx)
		return;

	DN3FX_Emit(DN3FX_FIRE_BURST, org, dir, sc);
	if (with_sound)
		pointsound(org, "dn3fx/fire09.ogg", 0.60, ATTN_IDLE);
};

void(vector org, vector norm) DN3FX_OnWallImpact =
{
	local float r;

	if (!autocvar_bm_dn3fx)
		return;

	if (time >= dn3fx_wall_puff_t)
	{
		dn3fx_wall_puff_t = time + 0.04;
		DN3FX_Emit(DN3FX_BULLET_PUFF, org, norm, 1.0);
	}

	if (time >= dn3fx_wall_snd_t)
	{
		dn3fx_wall_snd_t = time + 0.08;
		r = random();
		if (r < 0.55)
			pointsound(org, "dn3fx/bulithit.ogg", 0.55, ATTN_NORM);
		else if (r < 0.67)
			pointsound(org, "dn3fx/ricoche1.wav", 0.50, ATTN_NORM);
		else if (r < 0.78)
			pointsound(org, "dn3fx/ricoche2.wav", 0.50, ATTN_NORM);
		else if (r < 0.89)
			pointsound(org, "dn3fx/ricoche3.wav", 0.50, ATTN_NORM);
		else
			pointsound(org, "dn3fx/ricoche4.wav", 0.50, ATTN_NORM);
	}
};

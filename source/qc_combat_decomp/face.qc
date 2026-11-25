//Decompiled code. Please respect the original copyright.

void(float how_far) FacePainTeleport =
{
	local vector spot;
	local vector vec;

	spot = self.origin + (randomvec() * how_far);
	vec = normalize((spot - self.origin));
	traceline(self.origin, spot, TRUE, self);
	spot = trace_endpos - (vec * 13);
	if (PM_InWall(self, spot))
	{
		return;
	}
	if (!PM_TraceCheck(self, spot))
	{
		return;
	}
	traceline(spot, self.enemy.origin, FALSE, self);
	if ((trace_fraction < 1))
	{
		if ((trace_ent != self.enemy))
		{
			return;
		}
	}
	setorigin(self, spot);
	self.angles_y = vectoyaw((self.enemy.origin - spot));
};

void() FacePain =
{
	if ((self.pain_finished > time))
	{
		return;
	}
	self.pain_finished = (time + 0.5);
	sound(self, CHAN_VOICE, "face/face_pain.wav", 1, ATTN_NORM);
	FacePainTeleport(66);
};

void() FaceDeath =
{
	pointparticles(particleeffectnum(/*13606i*/"Afrit_death_explode"), self.origin, VEC_ORIGIN, 1);
	sound(self, CHAN_WEAPON, "weapons/r_exp3.wav", 1, ATTN_NORM);
	remove(self);
};

void() FaceTouch =
{
	if (other.takedamage)
	{
		if ((other.classname != "player"))
		{
			FacePainTeleport(70);
			return;
		}
		T_Damage(other, self, self.owner, 10);
		sound(self, CHAN_WEAPON, "face/face_touch.wav", 1, ATTN_NORM);
		remove(self);
	}
	if ((autocvar_evil_faces_monster_behaviour == 0))
	{
		if (!((((other.model == "progs/spike.mdl") || (other.model == "progs/s_spike.mdl")) || (other.model == "progs/grenade.mdl")) || (other.model == "progs/missile.mdl")))
		{
			pointparticles(particleeffectnum(/*13606i*/"Afrit_death_explode"), self.origin, VEC_ORIGIN, 1);
			sound(self, CHAN_WEAPON, "face/face_touch.wav", 1, ATTN_NORM);
			remove(self);
		}
	}
};

void() FaceHoming =
{
	local vector dir;
	local vector offang;
	local vector vec;

	if ((self.enemy.health < 1))
	{
		remove(self);
	}
	if ((vlen(((self.enemy.origin + '0 0 16') - self.origin)) <= 70))
	{
		traceline((self.enemy.origin + '0 0 16'), self.origin, FALSE, self);
		if ((trace_fraction == 1))
		{
			self.movetype = MOVETYPE_FLYMISSILE;
		}
	}
	if ((self.origin == self.old_origin))
	{
		sound(self, CHAN_WEAPON, "face/face_touch.wav", 1, ATTN_NORM);
		T_RadiusDamage(self, self, 30, self);
		remove(self);
	}
	self.old_origin = self.origin;
	dir = normalize(((self.enemy.origin + '0 0 16') - self.origin));
	offang = vectoangles(((self.enemy.origin + '0 0 14') - self.origin));
	makevectors(offang);
	vec = normalize(v_forward);
	self.angles = vectoangles(vec);
	self.frame = (self.frame + 1);
	if (autocvar_evil_faces_model_type)
	{
		if ((self.frame >= 44))
		{
			self.frame = 0;
		}
	}
	else
	{
		if ((self.frame >= 19))
		{
			self.frame = 0;
		}
	}
	self.velocity = (dir * 200);
	self.nextthink = (time + 0.15);
	self.think = FaceHoming;
};

void() face_main =
{
	local vector dir;

	dir = normalize(((self.enemy.origin + '0 0 10') - self.origin));
	if ((autocvar_evil_faces_monster_behaviour == 0))
	{
		self.movetype = MOVETYPE_FLYMISSILE;
	}
	setsize(self, '-9 -9 -9', '9 9 9');
	self.velocity = (dir * 150);
	self.nextthink = (time + 0.05);
	self.think = FaceHoming;
};

void(vector face_spawn_pos, vector face_spawn_vel, float starter) spawn_face =
{
	if (((autocvar_quadreplacer == 0) || (random() < 0.35)))
	{
		return;
	}
	newmis = spawn();
	if ((starter == 1))
	{
		newmis.enemy = self;
	}
	else
	{
		newmis.enemy = self.owner;
	}
	newmis.movetype = MOVETYPE_NOCLIP;
	newmis.solid = SOLID_BBOX;
	newmis.velocity = (face_spawn_vel * 7);
	newmis.angles = vectoangles(newmis.velocity);
	newmis.scale = autocvar_evil_faces_monster_scale;
	newmis.glow_color = 75;
	newmis.glow_size = 666;
	newmis.touch = FaceTouch;
	newmis.classname = "face";
	SkyPad_RegisterExtra (newmis);
	if ((random() < 0.7))
	{
		setmodel(newmis, "progs/face1.mdl");
		newmis.frame = 14;
	}
	else
	{
		setmodel(newmis, "progs/face.mdl");
		newmis.frame = 0;
	}
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	newmis.think = face_main;
	newmis.nextthink = (time + 0.7);
	newmis.health = autocvar_evil_faces_monster_health;
	newmis.takedamage = DAMAGE_AIM;
	setorigin(newmis, face_spawn_pos);
	newmis.traileffectnum = particleeffectnum(/*13771i*/"TR_FACE");
	newmis.th_pain = FacePain;
	newmis.th_die = FaceDeath;
	face_psycho = time + 1;
	sound(newmis, CHAN_WEAPON, "face/face.wav", 1, ATTN_NORM);
};

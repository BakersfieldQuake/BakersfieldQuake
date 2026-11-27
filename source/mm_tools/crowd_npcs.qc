#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
crowd_npcs.qc — the street crowd on the map "fox": ordinary people who stroll around, can be shot, and come back.

Who walks the street (kind numbers, crowd_kind forces one):
   1 Daniel (CCC)      2 4 AM Dad        3 Bryan            4 David Ojeda
   5/6/7 Pregnant Runner 1/2/3           8 QuakeGuy         9 Rubber Finger
  10 JessKart         11 Wheelman (dance sprite)
  12 Gurney Patient   13 COMBAT Badge Tech   14 Black Blazer Guy   15 Mustard Four Loko Guy
  16 Blue Tee Berserker   17 Red Fedora Heavy   18 Quilted Jacket Brawler   (crowd_sprites/build_crowd_sprites.py: 8 of the 16
     angles of the 512 px HD sheets, 12 walk + 10 run frames each, progs/crowd_c1..c7.spr32; loaded on fox only)
  19 Random Guy       20 Afro Guy       21 Random Lady     22 Really Big Fat Guy   (the 3D people of random_npcs.qc)

They never shoot and never start anything. They wander within npc_radius of the spot they spawned on, pause now and
then, and can be killed (gibs). A killed one is back at its spot after crowd_respawn seconds, as a new random person.
When one is shot there is a crowd_mad chance (1/3) that it gets mad, once per "episode" (a new roll only 4 seconds after
the last one, so a nailgun does not roll 10 times a second). A mad one either chases the shooter and pokes them for a
few points of damage (crowd_angry of the time) or runs away from them. The rest just yelp and keep strolling.

Server cvars:  crowd_on 1  crowd_count 14  crowd_mad 0.34  crowd_angry 0.5  crowd_dmg 3  crowd_hp 100
               crowd_respawn 20  crowd_kind 0  crowd_speed 1
Cheat impulse 56 (sv_cheats 1): list every crowd member (kind, mood, health, spot) to the console.
*/

var float	autocvar_crowd_on	= 1;
var float	autocvar_crowd_count	= 18;
var float	autocvar_crowd_mad	= 0.34;
var float	autocvar_crowd_angry	= 0.5;
var float	autocvar_crowd_dmg	= 3;
var float	autocvar_crowd_hp	= 100;
var float	autocvar_crowd_respawn	= 20;
var float	autocvar_crowd_kind	= 0;
var float	autocvar_crowd_speed	= 1;

.float	cn_kind;
.float	cn_mood;		// 0 = calm, 1 = running away, 2 = angry (chasing)
.float	cn_mood_end;
.float	cn_move;		// what the sprite shows: 0 = standing, 1 = walking, 2 = running
.float	cn_phase;		// own offset into the run cycle so a crowd does not step in unison
.float	cn_phase_end;
.float	cn_next_hit;
.float	cn_roll_t;
.float	cn_voice_t;
.float	cn_ftime;
.float	cn_fbase;
.float	cn_fstep;
.entity	cn_enemy;

float	crowd_done;
float	crowd_n;
float	crowd_seq;
float	crowd_lineno;
float	crowd_last1;
float	crowd_last2;
float	CN_KINDS		= 22;
float	CN_FIRST_MD3	= 19;		// kinds below are sprites, from here the 3D people
float	CN_FIRST_HD		= 12;		// 12..18: the HD sprites (progs/crowd_cN.spr32)

void() CN_Think;
void() CN_Die;
void(entity attacker, float take) CN_Pain;

string(float k) CN_Model =
{
	if (k == 1)		return "progs/daniel.spr32";
	if (k == 2)		return "progs/daniel_dad.spr32";
	if (k == 3)		return "progs/bryan.spr32";
	if (k == 4)		return "progs/david.spr32";
	if (k == 5)		return "progs/preg_1.spr32";
	if (k == 6)		return "progs/preg_2.spr32";
	if (k == 7)		return "progs/preg_3.spr32";
	if (k == 8)		return "progs/fr_quakeguy.spr32";
	if (k == 9)		return "progs/fr_finger.spr32";
	if (k == 10)	return "progs/jesskart.spr32";
	if (k == 11)	return "progs/wheelman_dance.spr32";
	if (k >= 12 && k <= 18)
		return strcat ("progs/crowd_c", ftos (k - 11), ".spr32");
	if (k == 19)	return "progs/npc_randguy.md3";
	if (k == 20)	return "progs/npc_afroguy.md3";
	if (k == 21)	return "progs/npc_randlady.md3";
	return "progs/npc_fatguy.md3";
};

// the same picture scales mbox.qc uses (each is about a player tall); crowd_c1..c7 scales come from crowd_sprites_info.json
float(float k) CN_Scale =
{
	if (k == 1)		return 0.6935;
	if (k == 2)		return 0.5126;
	if (k == 3)		return 0.8265;
	if (k == 4)		return 0.6935;
	if (k >= 5 && k <= 7)	return 0.4800;
	if (k == 8)		return 0.4211;
	if (k == 9)		return 0.4301;
	if (k == 10)	return 0.4938;
	if (k == 11)	return 0.8645;
	if (k == 12)	return 0.7328;		// the tight-cropped crowd sprites: 52 units tall (crowd_sprites_info.json)
	if (k == 13)	return 0.6306;
	if (k == 14)	return 0.6294;
	if (k == 15)	return 0.6306;
	if (k == 16)	return 0.6326;
	if (k == 17)	return 0.6306;
	if (k == 18)	return 0.6437;
	return 1;
};

// what a mad one yells: running away, and charging (a clip that exists for the character, else the stock player yelp)
string(float k) CN_FleeSound =
{
	if (k == 1)		return "daniel/sorry_table.wav";
	if (k == 2)		return "daniel/dad_4am.wav";
	if (k == 3)		return "bryan/noway.wav";
	if (k == 4)		return "david/sprint_rush.wav";
	if (k == 8)		return "funny/quakeahh.wav";
	if (k == 9)		return "mbox/drv_boing_hop.wav";
	if (k == 10)	return "friends/no.wav";
	if (k == 11)	return "friends/gowewd.wav";
	if (k == 19)	return "random_npcs/randguy_panic.wav";
	if (k == 20)	return "random_npcs/afroguy_panic.wav";
	if (k == 21)	return "random_npcs/lady_panic.wav";
	if (k == 22)	return "random_npcs/fatguy_panic.wav";
	return "player/pain4.wav";
};

string(float k) CN_AngrySound =
{
	if (k == 1)		return "daniel/shaaa_scream.wav";
	if (k == 2)		return "daniel/dad_4am.wav";
	if (k == 3)		return "bryan/whirl.wav";
	if (k == 4)		return "david/money_bag.wav";
	if (k == 8)		return "funny/quakeahh.wav";
	if (k == 9)		return "mbox/drv_boing_hop.wav";
	if (k == 10)	return "friends/no.wav";
	if (k == 11)	return "friends/no.wav";
	if (k == 19)	return "random_npcs/randguy_funny.wav";
	if (k == 20)	return "random_npcs/afroguy_funny.wav";
	if (k == 21)	return "random_npcs/lady_funny.wav";
	if (k == 22)	return "random_npcs/fatguy_funny.wav";
	return "player/pain5.wav";
};

// worldspawn (BM_Precache): everything a crowd member can say or be
float	crowd_precached;
void() Crowd_Precache =
{
	local float k;
	local string s;

	if (crowd_precached)
		return;
	crowd_precached = TRUE;
	k = 1;
	while (k <= CN_KINDS)
	{
		if (k < CN_FIRST_HD || k >= CN_FIRST_MD3 || world.model == "maps/fox.bsp" || world.model == "maps/downtown.bsp" || world.model == "maps/downtownsmall.bsp" || world.model == "maps/bakersfielddowntown.bsp" || world.model == "maps/bakersfieldish.bsp")		// 60 MB of HD sprites: fox + downtown
			precache_model (CN_Model (k));
		s = CN_FleeSound (k);
		precache_sound (s);
		s = CN_AngrySound (k);
		precache_sound (s);
		k = k + 1;
	}
	precache_model ("progs/gib1.mdl");
	precache_model ("progs/gib2.mdl");
	precache_model ("progs/gib3.mdl");
	precache_sound ("player/udeath.wav");
	precache_sound ("player/pain1.wav");
	precache_sound ("player/pain2.wav");
	precache_sound ("player/pain3.wav");
	precache_sound ("player/pain4.wav");
	precache_sound ("player/pain5.wav");
	precache_sound ("weapons/ax1.wav");
};

// start of the 8-dir x 4-frame falling death block appended to each sprite
float(float k) CN_DeathBase =
{
	if (k == 1)		return 232;
	if (k == 2)		return 56;
	if (k == 3)		return 168;
	if (k == 4)		return 232;
	if (k == 11)	return 368;
	if (k >= 12 && k <= 18)	return 96;
	return 56;
};

// the picture a sprite shows each viewer: its side facing them (8 views)
float() CN_Customize =
{
	local float rel, d, k, n, fps, dx, dy;
	local vector vorg;

	if (other.ishuman != 1)
		return FALSE;
	vorg = (other.clientcamera != world) ? other.clientcamera.origin : other.origin;
	dx = vorg_x - self.origin_x;
	if (dx > 2000 || dx < -2000)
		return FALSE;
	dy = vorg_y - self.origin_y;
	if (dy > 2000 || dy < -2000)
		return FALSE;

	if (self.cn_ftime != time || !self.cn_fstep)
	{
		self.cn_ftime = time;
		if (self.npc_dead)
		{
			k = floor (self.npc_dstep * 0.67);
			if (k < 0)
				k = 0;
			if (k > 3)
				k = 3;
			self.cn_fbase = CN_DeathBase (self.cn_kind) + k;
			self.cn_fstep = 4;
		}
		else if (self.cn_move == 0)
		{
			self.cn_fbase = 0;
			if (self.cn_kind == 11)
				self.cn_fstep = 5;		// wheelman_dance.spr32 run_stuck: 0 + d * 5 + k, no standing frames
			else
				self.cn_fstep = 1;
		}
		else if (self.cn_kind >= CN_FIRST_HD)
		{
			// crowd_c1..c7: 8 + d * 6 + k walking (6 fps), 56 + d * 5 + k running (7.5 fps)
			if (self.cn_move == 1)
			{
				k = floor (time * 6 + self.cn_phase);
				k = k - 6 * floor (k / 6);
				self.cn_fbase = 8 + k;
				self.cn_fstep = 6;
			}
			else
			{
				k = floor (time * 7.5 + self.cn_phase);
				k = k - 5 * floor (k / 5);
				self.cn_fbase = 56 + k;
				self.cn_fstep = 5;
			}
		}
		else
		{
			if (self.cn_kind == 11)
				n = 5;
			else if (self.cn_kind == 1 || self.cn_kind == 4)
				n = 4;		// daniel.spr32 / david.spr32: 8 + d * 4 + k
			else
				n = 6;		// 8 + d * 6 + k
			fps = 8;
			if (self.cn_move == 2)
				fps = 16;
			fps = fps * (n / 6);
			k = floor (time * fps + self.cn_phase);
			k = k - n * floor (k / n);
			if (self.cn_kind == 11)
				self.cn_fbase = k;
			else
				self.cn_fbase = 8 + k;
			self.cn_fstep = n;
		}
	}
	rel = vectoyaw (other.origin - self.origin) - self.angles_y;
	d = floor (rel / 45 + 0.5) & 7;
	self.frame = self.cn_fbase + d * self.cn_fstep;
	return TRUE;
};

float() CN_CustomizeKeep =
{
	return TRUE;
};

float() CN_HdOk =
{
	return (world.model == "maps/fox.bsp" || world.model == "maps/downtown.bsp" || world.model == "maps/downtownsmall.bsp" || world.model == "maps/bakersfielddowntown.bsp" || world.model == "maps/bakersfieldish.bsp");
};

float(float idx) CN_MapSafeKind =
{
	local float k, n;

	if (CN_HdOk ())
	{
		k = 1 + idx - CN_KINDS * floor (idx / CN_KINDS);
		return k;
	}
	n = CN_KINDS - (CN_FIRST_MD3 - CN_FIRST_HD);
	k = 1 + idx - n * floor (idx / n);
	if (k >= CN_FIRST_HD)
		k = k + (CN_FIRST_MD3 - CN_FIRST_HD);
	return k;
};

float() CN_RandomKind =
{
	local float k, hd_ok, tries;

	hd_ok = CN_HdOk ();
	if (autocvar_crowd_kind >= 1 && autocvar_crowd_kind <= CN_KINDS)
	{
		k = floor (autocvar_crowd_kind);
		if (!hd_ok && k >= CN_FIRST_HD && k < CN_FIRST_MD3)
			k = CN_MapSafeKind (k - 1);
		return k;
	}
	if (autocvar_crowd_kind < 0)
	{
		// -1: one of each precached kind in turn (1, 2, 3 ...), to look at them all
		crowd_seq = crowd_seq + 1;
		return CN_MapSafeKind (crowd_seq - 1);
	}
	tries = 0;
	k = 1;		// the loop always sets it; this only quiets the compiler (F302)
	while (tries < 4)
	{
		if (hd_ok)
		{
			k = 1 + floor (random () * CN_KINDS);
			if (k > CN_KINDS)
				k = CN_KINDS;
		}
		else
		{
			k = 1 + floor (random () * 15);
			if (k > 15)
				k = 15;
			if (k >= CN_FIRST_HD)
				k = k + (CN_FIRST_MD3 - CN_FIRST_HD);
		}
		tries = tries + 1;
		if (k != crowd_last1 && k != crowd_last2)
			tries = 10;
	}
	crowd_last2 = crowd_last1;
	crowd_last1 = k;
	return k;
};

// make self this person (also used when a killed one comes back as somebody else)
void(float k) CN_Setup =
{
	setmodel (self, CN_Model (k));
	self.cn_kind = k;
	self.colormod = '1 1 1';
	self.effects = 0;
	self.skin = 0;
	self.cn_mood = 0;
	self.cn_enemy = world;
	self.cn_move = 1;
	self.cn_phase = random () * 6;
	self.cn_roll_t = 0;
	self.cn_next_hit = 0;
	self.alpha = 1;
	self.npc_dead = FALSE;
	self.npc_dstep = 0;
	if (k < CN_FIRST_MD3)
	{
		self.scale = CN_Scale (k);
		self.customizeentityforclient = CN_Customize;
		setsize (self, '-16 -16 0', '16 16 54');		// origin at the feet
	}
	else
	{
		self.scale = 1;
		self.customizeentityforclient = CN_CustomizeKeep;
		if (k == 19)
			self.skin = floor (random () * 6);
		else if (k == 21)
			self.skin = floor (random () * 3);
		setsize (self, '-16 -16 -24', '16 16 32');		// the Quake player box, origin in the middle
		self.frame = 8;
	}
	self.health = autocvar_crowd_hp;
	if (k == 22)
		self.health = self.health * 1.5;
	self.max_health = self.health;
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.takedamage = DAMAGE_AIM;
	self.cn_phase_end = time + 1 + random () * 3;
};

// npc_home is where the spot is, at the height of a player's origin; sprites stand on the floor under it
void() CN_Place =
{
	if (self.cn_kind < CN_FIRST_MD3)
		setorigin (self, self.npc_home - '0 0 16');
	else
		setorigin (self, self.npc_home + '0 0 8');
	droptofloor ();
};

void(string snd) CN_Say =
{
	if (NPC_IsVoiceMuted(self) || time < self.cn_voice_t)
		return;
	self.cn_voice_t = time + 1.5;
	sound (self, CHAN_VOICE, snd, 1, ATTN_NORM);
};

void() CN_Calm =
{
	self.cn_mood = 0;
	self.cn_enemy = world;
	self.colormod = '1 1 1';
	self.cn_phase_end = time + 1 + random () * 2;
};

void() CN_Respawn =
{
	local entity p;

	// not on top of a player standing at the spot
	p = findradius (self.npc_home, 100);
	while (p)
	{
		if (p.classname == "player" && p.health > 0)
		{
			self.think = CN_Respawn;
			self.nextthink = time + 2;
			return;
		}
		p = p.chain;
	}
	CN_Setup (CN_RandomKind ());
	CN_Place ();
	self.think = CN_Think;
	self.nextthink = time + 0.1;
};

void() CN_DeathStep =
{
	local float i;

	self.npc_dstep = self.npc_dstep + 1;
	if (self.npc_dstep <= 5)
	{
		if (self.cn_kind >= CN_FIRST_MD3)
			self.frame = 44 + self.npc_dstep;
		self.think = CN_DeathStep;
		self.nextthink = time + 0.075;
		return;
	}
	if (self.npc_dstep == 6)
	{
		if (self.cn_kind >= CN_FIRST_MD3)
			self.frame = 49;
		self.think = CN_DeathStep;
		self.nextthink = time + 2.2;
		return;
	}
	if (self.npc_dstep <= 13)
	{
		self.alpha = 1.0 - (self.npc_dstep - 6) * 0.13;
		self.think = CN_DeathStep;
		self.nextthink = time + 0.07;
		return;
	}
	setmodel (self, "");
	self.alpha = 1;
	self.think = CN_Respawn;
	i = autocvar_crowd_respawn - 3.1;
	if (i < 1)
		i = 1;
	self.nextthink = time + i;
};

void() CN_Die =
{
	local float i;

	if (self.npc_dead)
		return;
	self.npc_dead = TRUE;
	self.npc_dstep = 0;
	self.solid = SOLID_NOT;
	self.takedamage = DAMAGE_NO;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';
	self.colormod = '1 1 1';
	self.effects = 0;

	if (NPC_ShouldGib (self))
	{
		BM_NPCGibBurst (-70, 3);
		setmodel (self, "");
		self.think = CN_Respawn;
		i = autocvar_crowd_respawn;
		if (i < 1)
			i = 1;
		self.nextthink = time + i;
		return;
	}

	if (!NPC_IsVoiceMuted(self))
		sound (self, CHAN_VOICE, CN_FleeSound (self.cn_kind), 1, ATTN_NORM);
	self.alpha = 1;
	if (self.cn_kind >= CN_FIRST_MD3)
		self.frame = 44;
	self.think = CN_DeathStep;
	self.nextthink = time + 0.075;
};

void(entity attacker, float take) CN_Pain =
{
	local float r;

	if (self.health <= 0 || self.npc_dead)
		return;
	if (attacker.classname != "player")
		return;
	if (self.cn_mood != 0)
	{
		self.cn_enemy = attacker;		// already mad: whoever hits it now is who it deals with
		return;
	}
	if (!NPC_IsVoiceMuted(self) && time >= self.cn_voice_t)
	{
		self.cn_voice_t = time + 1;
		r = 1 + floor (random () * 3);
		if (r == 1)
			sound (self, CHAN_VOICE, "player/pain1.wav", 0.8, ATTN_NORM);
		else if (r == 2)
			sound (self, CHAN_VOICE, "player/pain2.wav", 0.8, ATTN_NORM);
		else
			sound (self, CHAN_VOICE, "player/pain3.wav", 0.8, ATTN_NORM);
	}
	if (time < self.cn_roll_t)
		return;
	self.cn_roll_t = time + 4;		// one roll per episode, not one per bullet
	if (random () >= autocvar_crowd_mad)
		return;
	self.cn_enemy = attacker;
	self.cn_voice_t = 0;
	if (random () < autocvar_crowd_angry)
	{
		self.cn_mood = 2;
		self.cn_mood_end = time + 10;
		self.colormod = '1.6 0.55 0.55';
		CN_Say (CN_AngrySound (self.cn_kind));
	}
	else
	{
		self.cn_mood = 1;
		self.cn_mood_end = time + 6;
		CN_Say (CN_FleeSound (self.cn_kind));
	}
};

void() CN_Think =
{
	local float want, diff, step, dist, dmg;
	local vector dv;
	local entity e;

	self.think = CN_Think;
	self.nextthink = time + 0.05;
	if (self.health <= 0)
	{
		CN_Die ();
		return;
	}

	step = 0;
	self.cn_move = 0;
	if (self.cn_mood != 0)
	{
		e = self.cn_enemy;
		if (time >= self.cn_mood_end || e == world || e.health <= 0 || vlen (e.origin - self.origin) > 1100)
			CN_Calm ();
	}

	if (self.cn_mood == 2)
	{
		// chase the shooter and poke them (a little slower than a running player)
		e = self.cn_enemy;
		dv = e.origin - self.origin;
		dv_z = 0;
		dist = vlen (dv);
		want = vectoyaw (dv);
		if (dist < 46 && fabs (e.origin_z - self.origin_z) < 72)		// dv_z is zeroed above: without the height test a member one floor below (or under a jetpack) still landed hits
		{
			if (time >= self.cn_next_hit)
			{
				self.cn_next_hit = time + 1.1;
				dmg = autocvar_crowd_dmg + floor (random () * 2);
				sound (self, CHAN_WEAPON, "weapons/ax1.wav", 0.8, ATTN_NORM);
				T_Damage (e, self, self, dmg);
			}
		}
		else
		{
			step = 9.5;
			self.cn_move = 2;
		}
	}
	else if (self.cn_mood == 1)
	{
		// run from the shooter
		e = self.cn_enemy;
		dv = self.origin - e.origin;
		dv_z = 0;
		want = vectoyaw (dv);
		step = 14;
		self.cn_move = 2;
	}
	else
	{
		// stroll: pause now and then, stay near the spot
		if (time >= self.cn_phase_end)
		{
			if (random () < 0.3)
			{
				self.npc_state = 0;		// stand a moment
				self.cn_phase_end = time + 1.5 + random () * 2.5;
			}
			else
			{
				self.npc_state = 1;		// walk on, a bit off the old heading
				self.cn_phase_end = time + 3 + random () * 4;
				self.angles_y = self.angles_y + (random () - 0.5) * 70;
			}
		}
		if (self.npc_state == 1)
		{
			self.cn_move = 1;
			step = 3.4;
			if (self.cn_kind == 22)
				step = 2.8;
			if (self.npc_radius > 0 && vlen (self.origin - self.npc_home) > self.npc_radius)
				want = vectoyaw (self.npc_home - self.origin) + (random () - 0.5) * 36;
			else
				want = self.angles_y + (random () - 0.5) * 14;
		}
		else
			want = self.angles_y;
	}

	if (self.cn_kind >= CN_FIRST_MD3)
	{
		// the 3D people: 0..7 idle, 8..19 walk, 20..29 run
		if (self.cn_move == 0)
			self.frame = floor (time * 10 + self.cn_phase) - 8 * floor ((time * 10 + self.cn_phase) / 8);
		else if (self.cn_move == 1)
			self.frame = 8 + floor (time * 12 + self.cn_phase) - 12 * floor ((time * 12 + self.cn_phase) / 12);
		else
			self.frame = 20 + floor (time * 15 + self.cn_phase) - 10 * floor ((time * 15 + self.cn_phase) / 10);
	}
	if (step <= 0)
		return;

	diff = want - self.angles_y;
	while (diff > 180)
		diff = diff - 360;
	while (diff < -180)
		diff = diff + 360;
	self.angles_y = self.angles_y + diff * 0.3;
	step = step * autocvar_crowd_speed;

	if (!walkmove (self.angles_y, step))
	{
		// steer around walls, props, parked cars
		if (!walkmove (self.angles_y + 45, step * 0.8))
		{
			if (!walkmove (self.angles_y - 45, step * 0.8))
			{
				self.angles_y = self.angles_y + 115 + random () * 90;
				while (self.angles_y >= 360)
					self.angles_y = self.angles_y - 360;
				walkmove (self.angles_y, step * 0.7);
			}
			else
				self.angles_y = self.angles_y - 35;
		}
		else
			self.angles_y = self.angles_y + 35;
	}
};

void(vector spot, float radius) Crowd_Spawn =
{
	local entity e, oself;

	if (crowd_n >= autocvar_crowd_count)
		return;
	crowd_n = crowd_n + 1;
	e = spawn ();
	e.classname = "npc_crowd";
	e.npc_home = spot;
	e.npc_radius = radius;
	e.angles_y = random () * 360;
	oself = self;
	self = e;
	e.th_pain = CN_Pain;
	e.th_die = CN_Die;
	CN_Setup (CN_RandomKind ());
	CN_Place ();
	self.npc_state = 1;
	self.think = CN_Think;
	self.nextthink = time + 0.1 + random () * 0.3;
	self = oself;
};

void() CN_MapStart =
{
	if (!autocvar_crowd_on || crowd_n >= autocvar_crowd_count)
	{
		remove (self);
		return;
	}
	crowd_n = crowd_n + 1;
	self.th_pain = CN_Pain;
	self.th_die = CN_Die;
	CN_Setup (CN_RandomKind ());
	CN_Place ();
	self.npc_state = 1;
	self.think = CN_Think;
	self.nextthink = time + 0.1 + random () * 0.3;
};

// Map-placed street crowd entity (e.g. downtown hotspots): origin = player-height home spot, npc_radius = wander radius
void() npc_crowd =
{
	if (BM_NoMapNPC ())		// no map NPCs unless bm_npcs 1 (2026-11-26)
	{
		remove (self);
		return;
	}
	Crowd_Precache ();		// a map that places a crowd member loads the sprites; other maps do not (see BM_Precache)
	self.classname = "npc_crowd";
	self.npc_home = self.origin;
	if (self.npc_radius <= 0)
		self.npc_radius = 380;
	self.angles_y = self.angles_y + (random () - 0.5) * 45;
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.think = CN_MapStart;
	self.nextthink = 1.0 + random () * 0.25;
};

// z is the height of a player's origin on the sidewalk (the deathmatch spawns of fox.bsp are on it)
void() Crowd_SpawnFox =
{
	// 20th & H, the postcard corner where a player starts: a few right there
	Crowd_Spawn ('-2000 720 30', 420);
	Crowd_Spawn ('-2000 930 30', 420);		// (not -2230 900: a John Bird vehicle stands there)
	Crowd_Spawn ('-2050 1040 30', 420);
	// down H Street and across the blocks
	Crowd_Spawn ('-2136 2568 30', 450);
	Crowd_Spawn ('-2208 -2856 30', 450);
	Crowd_Spawn ('-2208 4920 30', 450);
	Crowd_Spawn ('1968 936 30', 450);
	Crowd_Spawn ('-3504 984 30', 350);
	Crowd_Spawn ('-4776 -2976 30', 450);
	Crowd_Spawn ('-2208 -6984 30', 450);
	// inside the Fox: main lobby and the orchestra aisles
	Crowd_Spawn ('-3312 1596 34', 220);
	Crowd_Spawn ('-3426 2424 46', 200);
	Crowd_Spawn ('-3150 2424 46', 200);
	Crowd_Spawn ('1968 -2904 30', 450);
};

// every frame from BM_StartFrame: one second into the map (the map's own entities exist) the crowd is spawned
void() Crowd_Tick =
{
	if (crowd_done || time < 1)
		return;
	crowd_done = TRUE;
	if (!autocvar_crowd_on || !autocvar_bm_npcs)		// bm_npcs 0: no crowd (2026-11-26)
		return;
	if (mapname == "fox")
		Crowd_SpawnFox ();
};

// impulse 56 (cheat): who is where
void() Crowd_Report =
{
	local entity e;
	local string s;

	e = find (world, classname, "npc_crowd");
	while (e)
	{
		s = strcat ("crowd kind ", ftos (e.cn_kind), " mood ", ftos (e.cn_mood));
		s = strcat (s, " hp ", ftos (e.health), " dead ", ftos (e.npc_dead));
		s = strcat (s, " at ", ftos (floor (e.origin_x)), " ", ftos (floor (e.origin_y)), " ", ftos (floor (e.origin_z)), "\n");
		sprint (self, s);
		e = find (e, classname, "npc_crowd");
	}
	sprint (self, strcat ("crowd cvars: kind ", ftos (autocvar_crowd_kind), " seq ", ftos (crowd_seq), " respawn ", ftos (autocvar_crowd_respawn), "\n"));
};

// impulse 57 / 58 (cheat): you hit the nearest crowd member for 25 / 500 (the same T_Damage a bullet goes through)
void(float dmg) Crowd_Poke =
{
	local entity e, best;
	local float d, bd;

	bd = 1500;
	best = world;		// QC locals keep their last value: with nobody in range this hit whoever was poked last time
	e = find (world, classname, "npc_crowd");
	while (e)
	{
		d = vlen (e.origin - self.origin);
		if (e.takedamage && d < bd)
		{
			bd = d;
			best = e;
		}
		e = find (e, classname, "npc_crowd");
	}
	if (best)
		T_Damage (best, self, self, dmg);
};

// impulse 59 (cheat): the whole crowd lines up facing you, 300 units ahead, to look at everybody (spots move with them);
// the first call as kinds 1..14, the next 15..22 and 1..6, and so on
void() Crowd_Line =
{
	local entity e, me;
	local float i;
	local vector flat;

	flat = '0 0 0';
	flat_y = self.v_angle_y;
	makevectors (flat);
	i = 0;
	crowd_lineno = crowd_lineno + 1;
	e = find (world, classname, "npc_crowd");
	while (e)
	{
		if (!e.npc_dead)
		{
			e.npc_home = self.origin + v_forward * 300 + v_right * ((i - 6.5) * 44) + '0 0 6';
			e.angles_y = flat_y + 180;
			e.cn_phase_end = time + 1000;
			e.npc_state = 1;
			e.npc_radius = 60;
			me = self;
			self = e;
			CN_Setup (CN_MapSafeKind (i + 14 * crowd_lineno));	// each call: the next 14 precached kinds
			CN_Place ();
			self = me;
			i = i + 1;
		}
		e = find (e, classname, "npc_crowd");
	}
};

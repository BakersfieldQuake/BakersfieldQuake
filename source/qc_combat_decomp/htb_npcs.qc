/*
==============================================================================
HAIR TRANSPLANT BITCOIN ONLYFANS BAR (`N08_htb`, X = 108..114m, North side)
  - 2 video-matched pitchmen out front (`htb_guy1`, `htb_guy2`) with real
    video-sliced WAV voice clips & excited animated pitches
  - 4 rear clinic NPCs (`htb_clinic1..3` seated patients + `htb_clinic4` doctor)
  - Uses existing `soi6_*` entity fields to avoid adding globals
  - All shootable, killable/gibbable (using `_b.md3`), and auto-respawning
==============================================================================
*/

float htb_precached;
float htb_spawned;
float htb_voice_cd;
.float htb_cp_t;	// shooter: next allowed forced pitch (clip + centerprint) from hitting an HTB NPC

float HTB_ROLE_PITCH1 = 1;
float HTB_ROLE_PITCH2 = 2;
float HTB_ROLE_CLINIC = 3;

void() HTB_PrecacheAssets =
{
	if (htb_precached)
		return;
	htb_precached = TRUE;

	precache_model ("progs/htb_guy1_a.md3");
	precache_model ("progs/htb_guy1_b.md3");
	precache_model ("progs/htb_guy2_a.md3");
	precache_model ("progs/htb_guy2_b.md3");
	precache_model ("progs/htb_clinic1_a.md3");
	precache_model ("progs/htb_clinic1_b.md3");
	precache_model ("progs/htb_clinic2_a.md3");
	precache_model ("progs/htb_clinic2_b.md3");
	precache_model ("progs/htb_clinic3_a.md3");
	precache_model ("progs/htb_clinic3_b.md3");
	precache_model ("progs/htb_clinic4_a.md3");
	precache_model ("progs/htb_clinic4_b.md3");

	precache_sound ("htb_bar/guy1_1.wav");
	precache_sound ("htb_bar/guy1_2.wav");
	precache_sound ("htb_bar/guy1_3.wav");
	precache_sound ("htb_bar/guy1_4.wav");
	precache_sound ("htb_bar/guy2_1.wav");
	precache_sound ("htb_bar/guy2_2.wav");
	precache_sound ("htb_bar/guy2_3.wav");
};

string(float role, float idx) HTB_ClipSound =
{
	if (role == HTB_ROLE_PITCH1)
	{
		if (idx == 1) return "htb_bar/guy1_1.wav";
		if (idx == 2) return "htb_bar/guy1_2.wav";
		if (idx == 3) return "htb_bar/guy1_3.wav";
		return "htb_bar/guy1_4.wav";
	}
	if (idx == 1) return "htb_bar/guy2_1.wav";
	if (idx == 2) return "htb_bar/guy2_2.wav";
	return "htb_bar/guy2_3.wav";
};

string(float role, float idx) HTB_ClipQuote =
{
	if (role == HTB_ROLE_PITCH1)
	{
		if (idx == 1) return "Welcome to the Hair Transplant Bitcoin OnlyFans bar!";
		if (idx == 2) return "Have a drink, get a hair transplant, and start an OnlyFans!";
		if (idx == 3) return "100% FUE grafts while trading BTC at the bar!";
		return "Come inside for a cold drink and full spiky hairline!";
	}
	if (role == HTB_ROLE_PITCH2)
	{
		if (idx == 1) return "It's absolutely incredible, you won't believe the results!";
		if (idx == 2) return "GPU mining rigs + OnlyFans studio right inside!";
		return "Walk in balding, walk out rich with legendary hair!";
	}
	if (idx == 1) return "Doctor is prepping 4,000 Bitcoin-funded hair grafts!";
	if (idx == 2) return "Halfway to full Gon-style spiky hair!";
	if (idx == 3) return "Checking OnlyFans subs & Bitcoin gains with fresh new hair!";
	return "Steady hand on the implanter pen! Best bar on Soi 6!";
};

float() HTB_Customize =
{
	local vector v;
	local float dx, dy, rel, d, elapsed, f;

	dx = fabs (other.origin_x - self.origin_x);
	dy = fabs (other.origin_y - self.origin_y);
	if (dx > 2000 || dy > 2000 || (dx * dx + dy * dy) > 4000000)
		return FALSE;

	// Face the viewer's POSITION, in 3 degree steps. Facing his view angle (other.v_angle_y) changed this entity for him on
	// every frame he moved the mouse, so every NPC in range was re-sent to him each frame. Looking straight at the NPC the
	// two are the same angle.
	self.angles_y = floor ((vectoyaw (other.origin - self.origin) + 180) / 3 + 0.5) * 3;
	self.angles_x = 0;
	self.angles_z = 0;

	v = other.origin - self.origin;
	rel = vectoyaw (v) - self.soi6_yaw;
	rel = rel - 360 * floor (rel / 360);
	d = floor (rel / 45 + 0.5);
	if (d >= 8)
		d = d - 8;

	elapsed = time - self.soi6_anim_t;
	if (elapsed < 0)
		elapsed = 0;

	if (self.soi6_state == SOI6_DEAD)
	{
		f = floor (elapsed * 16);
		if (f > 5) f = 5;
		self.skin = f * 8 + d;
		return TRUE;
	}
	if (self.soi6_state == SOI6_GIB)
	{
		f = floor (elapsed * 18);
		if (f > 7) f = 7;
		self.skin = (6 + f) * 8 + d;
		return TRUE;
	}

	if (self.soi6_state == SOI6_IDLE)
		f = floor (elapsed * 14) % 6;
	else if (self.soi6_state == SOI6_DANCE)
		f = 6 + (floor (elapsed * 16) % 12);
	else if (self.soi6_state == SOI6_SCREAM)
		f = 26 + (floor (elapsed * 18) % 5);
	else
		f = 18 + (floor (elapsed * 16) % 8);

	self.skin = f * 8 + d;
	return TRUE;
};

void(entity ent, float st) HTB_SetState =
{
	if (ent.soi6_state == st)
		return;
	ent.soi6_state = st;
	ent.soi6_anim_t = time - random () * 0.20;
	if (st == SOI6_DEAD || st == SOI6_GIB)
	{
		ent.soi6_anim_t = time;
		setmodel (ent, ent.soi6_mdl_b);
	}
	else if (ent.model != ent.soi6_mdl_a)
	{
		setmodel (ent, ent.soi6_mdl_a);
		setsize (ent, '-12 -12 0', '12 12 58');
	}
};

void() HTB_Respawn =
{
	self.health = self.max_health;
	self.takedamage = DAMAGE_AIM;
	self.solid = SOLID_CORPSE;
	self.movetype = MOVETYPE_STEP;
	self.velocity = '0 0 0';
	self.soi6_yaw = self.soi6_home_yaw;
	self.soi6_state = -1;
	setorigin (self, self.soi6_apron + '0 0 4');
	setmodel (self, self.soi6_mdl_a);
	setsize (self, '-12 -12 0', '12 12 58');
	droptofloor ();
	HTB_SetState (self, SOI6_DANCE);
	self.soi6_state_t = time + 3 + random () * 3;
	self.nextthink = time + 0.15;
};

void(entity ent, entity pl, float force_talk) HTB_Talk =
{
	local float idx;

	if (!force_talk && time < ent.soi6_talk_t)
		return;
	if (!force_talk && time < htb_voice_cd)
		return;

	ent.soi6_talk_t = time + 5.5;
	htb_voice_cd = time + 3.2;

	if (ent.soi6_tier == HTB_ROLE_PITCH1)
	{
		idx = 1 + (floor (random () * 4) % 4);
		sound (ent, CHAN_VOICE, HTB_ClipSound (HTB_ROLE_PITCH1, idx), 1, ATTN_NORM);
		if (pl && (pl.flags & FL_CLIENT))
			centerprint (pl, HTB_ClipQuote (HTB_ROLE_PITCH1, idx));
	}
	else if (ent.soi6_tier == HTB_ROLE_PITCH2)
	{
		idx = 1 + (floor (random () * 3) % 3);
		sound (ent, CHAN_VOICE, HTB_ClipSound (HTB_ROLE_PITCH2, idx), 1, ATTN_NORM);
		if (pl && (pl.flags & FL_CLIENT))
			centerprint (pl, HTB_ClipQuote (HTB_ROLE_PITCH2, idx));
	}
	else if (pl && (pl.flags & FL_CLIENT))
	{
		centerprint (pl, HTB_ClipQuote (HTB_ROLE_CLINIC, ent.soi6_id));
	}
};

void(entity attacker, float damage) HTB_Pain =
{
	local vector dvec;

	if (self.health <= 0 || self.soi6_state == SOI6_DEAD || self.soi6_state == SOI6_GIB)
		return;

	self.velocity = '0 0 0';
	if (attacker && attacker != world)
	{
		dvec = attacker.origin - self.origin;
		dvec_z = 0;
		if (vlen (dvec) > 2)
			self.soi6_yaw = vectoyaw (dvec);
	}
	HTB_SetState (self, SOI6_SCREAM);
	self.soi6_state_t = time + 2.0;
	// the forced pitch restarted the clip and centerprinted the shooter on every hit (~10/s with a nailgun): once a second per shooter
	if (attacker != world)
	{
		if (time < attacker.htb_cp_t)
			return;
		attacker.htb_cp_t = time + 1;
	}
	HTB_Talk (self, attacker, TRUE);
};

void() HTB_Die =
{
	if (self.soi6_state == SOI6_DEAD || self.soi6_state == SOI6_GIB)
		return;

	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.velocity = '0 0 0';

	if (self.health < -35)
	{
		HTB_SetState (self, SOI6_GIB);
		Soi6_SpawnPlayerGibs ();
	}
	else
	{
		HTB_SetState (self, SOI6_DEAD);
	}
	self.soi6_respawn_t = time + 15;
	self.nextthink = time + 0.4;
};

void() HTB_Think =
{
	local entity p;
	local vector dvec;
	local float dist;

	if (self.soi6_state == SOI6_DEAD || self.soi6_state == SOI6_GIB)
	{
		if (time >= self.soi6_respawn_t)
		{
			HTB_Respawn ();
			return;
		}
		self.nextthink = time + 0.4;
		return;
	}

	self.nextthink = time + 0.18;
	p = Soi6_NearestPlayerFast (self, 220);

	if (p != world)
	{
		dvec = p.origin - self.origin;
		dvec_z = 0;
		dist = vlen (dvec);
		if (dist > 4 && self.soi6_tier != HTB_ROLE_CLINIC)
			self.soi6_yaw = vectoyaw (dvec);
		if (time >= self.soi6_talk_t && dist < 175)
		{
			HTB_SetState (self, SOI6_SCREAM);
			self.soi6_state_t = time + 2.8;
			HTB_Talk (self, p, FALSE);
		}
	}
	else if (time >= self.soi6_state_t)
	{
		self.soi6_yaw = self.soi6_home_yaw;
		if (self.soi6_state == SOI6_DANCE)
			HTB_SetState (self, SOI6_IDLE);
		else
			HTB_SetState (self, SOI6_DANCE);
		self.soi6_state_t = time + 3.0 + random () * 4.0;
	}
};

entity(string m_a, string m_b, vector org, float yaw_deg, float role, float cid, float hp) HTB_SpawnOne =
{
	local entity e, saved;

	e = spawn ();
	e.classname = "npc_htb";
	e.soi6_mdl_a = m_a;
	e.soi6_mdl_b = m_b;
	e.soi6_tier = role;
	e.soi6_id = cid;
	e.soi6_yaw = yaw_deg;
	e.soi6_home_yaw = yaw_deg;
	e.soi6_apron = org;
	e.health = hp;
	e.max_health = hp;
	e.takedamage = DAMAGE_AIM;
	e.solid = SOLID_CORPSE;
	e.movetype = MOVETYPE_STEP;
	e.effects = EF_NOSHADOW;
	e.th_pain = HTB_Pain;
	e.th_die = HTB_Die;
	e.customizeentityforclient = HTB_Customize;
	e.think = HTB_Think;
	e.nextthink = time + 0.2 + random () * 0.25;

	setmodel (e, m_a);
	setsize (e, '-12 -12 0', '12 12 58');
	setorigin (e, org + '0 0 6');
	e.soi6_state = -1;
	HTB_SetState (e, SOI6_DANCE);
	e.soi6_state_t = time + 2 + random () * 3;
	e.soi6_talk_t = time + 0.5 + random () * 1.5;

	saved = self;
	self = e;
	droptofloor ();
	self = saved;
	e.soi6_apron = e.origin;
	return e;
};

vector(float mx, float my, float mz_u) HTB_Pos =
{
	local vector v;
	v_x = mx * 39.37007874;
	v_y = my * 39.37007874;
	v_z = mz_u;
	return v;
};

void() HTB_SpawnBar =
{
	if (htb_spawned)
		return;
	htb_spawned = TRUE;
	HTB_PrecacheAssets ();

	// 2 Video-matched Pitchmen right out front of N08_htb (`X = 110.0m, 112.0m, Y = 2.25m`, facing South)
	HTB_SpawnOne ("progs/htb_guy1_a.md3", "progs/htb_guy1_b.md3",
		HTB_Pos (110.0, 2.25, 8), -90, HTB_ROLE_PITCH1, 1, 180);
	HTB_SpawnOne ("progs/htb_guy2_a.md3", "progs/htb_guy2_b.md3",
		HTB_Pos (112.0, 2.25, 8), -90, HTB_ROLE_PITCH2, 2, 180);

	// 4 Rear Hair-Transplant Clinic NPCs (3 seated patients + 1 doctor)
	HTB_SpawnOne ("progs/htb_clinic1_a.md3", "progs/htb_clinic1_b.md3",
		HTB_Pos (109.25, 15.50, 8), -90, HTB_ROLE_CLINIC, 1, 120);
	HTB_SpawnOne ("progs/htb_clinic2_a.md3", "progs/htb_clinic2_b.md3",
		HTB_Pos (111.00, 17.00, 8), -90, HTB_ROLE_CLINIC, 2, 120);
	HTB_SpawnOne ("progs/htb_clinic3_a.md3", "progs/htb_clinic3_b.md3",
		HTB_Pos (112.75, 15.50, 8), -90, HTB_ROLE_CLINIC, 3, 120);
	HTB_SpawnOne ("progs/htb_clinic4_a.md3", "progs/htb_clinic4_b.md3",
		HTB_Pos (111.75, 16.85, 8), 160, HTB_ROLE_CLINIC, 4, 150);

	print ("HTB_SpawnBar: spawned 2 pitchmen + 4 hair-transplant clinic NPCs at N08_htb.\n");
};

void(vector pos, float yaw_deg, float pitch_deg, string msg) HTB_TeleportView =
{
	setorigin (self, pos);
	self.velocity = '0 0 0';
	self.angles = '0 0 0';
	self.angles_y = yaw_deg;
	self.angles_x = pitch_deg;
	self.v_angle = self.angles;
	self.fixangle = TRUE;
	sprint (self, msg);
};

void() HTB_GotoBar =
{
	// Front street view: animated marquee + 2 pitchmen + bar entrance
	HTB_TeleportView (HTB_Pos (111.0, -3.5, 32), 90, -6, "HTB_GotoBar: outside Hair Transplant Bitcoin OnlyFans Bar.\n");
};

void() HTB_GotoInterior =
{
	// Zone 1 & 2 view: Bitcoin bar, dual-monitor OnlyFans desks, GPU mining racks
	HTB_TeleportView (HTB_Pos (110.7, 5.1, 32), 95, 2, "HTB_GotoInterior: inside Front Bitcoin Bar & Tech Floor.\n");
};

void() HTB_GotoClinic =
{
	// Zone 3 view: Rear hair-transplant clinic with 3 seated patients & doctor
	HTB_TeleportView (HTB_Pos (111.0, 13.4, 32), 90, 2, "HTB_GotoClinic: inside Rear Hair-Transplant Clinic.\n");
};

void() HTB_GotoUpstairs =
{
	// 2F upstairs room view above N08 (lighting + furnished room check)
	HTB_TeleportView (HTB_Pos (111.0, 11.2, 180), 245, 4, "HTB_GotoUpstairs: inside N08 2F upstairs room.\n");
};

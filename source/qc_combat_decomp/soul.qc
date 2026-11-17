//Decompiled code. Please respect the original copyright.

void() alt_death15 =
{
	self.alpha = -1;
	self.glow_color = 5;
	self.glow_size = 10;
	self.nextthink = (time + 0.15);
	self.think = SUB_Remove;
};

void() alt_death14 =
{
	self.alpha = 0.01;
	self.glow_color = 5;
	self.glow_size = 10;
	te_customflash(self.origin, 600, 0.7, '0.5 0.5 0.5');
	sendParticle("soulvanish", self.origin, VEC_ORIGIN, 1);
	self.nextthink = (time + 0.15);
	self.think = alt_death15;
};

void() alt_death13 =
{
	sound(self, CHAN_WEAPON, "soul/flash.wav", 0.6, 4);
	pointparticles(particleeffectnum(/*52287i*/"multigrenade_explosion_nodebris"), self.origin, VEC_ORIGIN, 1);
	pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
	sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
	self.alpha = 0.04;
	self.glow_color = 5;
	self.glow_size = 40;
	self.nextthink = (time + 0.2);
	self.think = alt_death14;
};

void() alt_death12 =
{
	self.alpha = 0.07;
	self.glow_color = 5;
	self.glow_size = 70;
	self.nextthink = (time + 0.2);
	self.think = alt_death13;
};

void() alt_death11 =
{
	self.alpha = 0.1;
	self.glow_color = 5;
	self.glow_size = 100;
	self.nextthink = (time + 0.2);
	self.think = alt_death12;
};

void() alt_death10 =
{
	self.alpha = 0.13;
	self.glow_color = 5;
	self.glow_size = 150;
	self.nextthink = (time + 0.2);
	self.think = alt_death11;
};

void() alt_death9 =
{
	self.alpha = 0.16;
	self.glow_color = 5;
	self.glow_size = 200;
	self.nextthink = (time + 0.2);
	self.think = alt_death10;
};

void() alt_death8 =
{
	self.alpha = 0.19;
	self.glow_color = 5;
	self.glow_size = 250;
	self.nextthink = (time + 0.2);
	self.think = alt_death9;
};

void() alt_death7 =
{
	self.alpha = 0.22;
	self.glow_color = 5;
	self.glow_size = 300;
	self.nextthink = (time + 0.2);
	self.think = alt_death8;
};

void() alt_death6 =
{
	self.alpha = 0.25;
	self.glow_color = 5;
	self.glow_size = 350;
	self.nextthink = (time + 0.2);
	self.think = alt_death7;
};

void() alt_death5 =
{
	self.alpha = 0.28;
	self.glow_color = 5;
	self.glow_size = 400;
	self.nextthink = (time + 0.2);
	self.think = alt_death6;
};

void() alt_death4 =
{
	self.alpha = 0.31;
	self.glow_color = 5;
	self.glow_size = 450;
	self.nextthink = (time + 0.2);
	self.think = alt_death5;
};

void() alt_death3 =
{
	self.alpha = 0.34;
	self.glow_color = 5;
	self.glow_size = 500;
	self.nextthink = (time + 0.2);
	self.think = alt_death4;
};

void() alt_death2 =
{
	self.alpha = 0.37;
	self.glow_color = 5;
	self.glow_size = 500;
	self.nextthink = (time + 0.2);
	self.think = alt_death3;
};

void() alt_death1 =
{
	self.velocity = '0 0 25';
	self.alpha = 0.4;
	self.glow_color = 5;
	self.glow_size = 500;
	self.nextthink = (time + 0.5);
	self.think = alt_death2;
};

void() alt_death006 =
{
	self.alpha = 0.4;
	self.colormod = '7 7 7';
	self.glow_color = 5;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	self.think = alt_death1;
};

void() alt_death005 =
{
	self.alpha = 0.4;
	self.colormod = '6 6 6';
	self.glow_color = 5;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	self.think = alt_death006;
};

void() alt_death004 =
{
	self.alpha = 0.4;
	self.colormod = '5 5 5';
	self.glow_color = 5;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = alt_death005;
};

void() alt_death003 =
{
	sound(self, CHAN_WEAPON, "soul/liftup.wav", 0.4, 1);
	self.alpha = 0.4;
	self.colormod = '4 4 4';
	self.glow_color = 5;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = alt_death004;
};

void() alt_death002 =
{
	self.alpha = 0.4;
	self.colormod = '3 3 3';
	self.glow_color = 5;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = alt_death003;
};

void() alt_death001 =
{
	self.alpha = 0.4;
	self.colormod = '2 2 2';
	self.glow_color = 5;
	self.glow_size = 110;
	self.nextthink = (time + 0.1);
	self.think = alt_death002;
};

void() alt_death000 =
{
	self.alpha = 0.4;
	self.glow_color = 5;
	self.glow_size = 20;
	self.nextthink = (time + 0.7);
	self.think = alt_death001;
};

void() wingsend =
{
	self.nextthink = (time + 0.01);
	self.think = SUB_Remove;
};

void() wings01 = [ 20, wings02 ]
{
	self.alpha = 0.05;
	self.glow_color = 5;
	self.glow_size = 20;
	self.nextthink = (time + 0.05);
};

void() wings02 = [ 21, wings03 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.07;
	self.glow_color = 5;
	self.glow_size = 60;
	self.nextthink = (time + 0.05);
};

void() wings03 = [ 22, wings04 ]
{
	if (((self.has_fired <= 1) || (random() < 0.4)))
	{
		sound(self, CHAN_VOICE, "soul/awake.wav", 0.6, 4);
	}
	self.alpha = 0.09;
	self.glow_color = 5;
	self.glow_size = 100;
	self.nextthink = (time + 0.05);
};

void() wings04 = [ 23, wings05 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.11;
	self.glow_color = 5;
	self.glow_size = 120;
	self.nextthink = (time + 0.05);
};

void() wings05 = [ 24, wings06 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	self.alpha = 0.13;
	self.glow_color = 5;
	self.glow_size = 160;
	self.nextthink = (time + 0.05);
};

void() wings06 = [ 25, wings07 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.15;
	self.glow_color = 5;
	self.glow_size = 200;
	self.nextthink = (time + 0.05);
};

void() wings07 = [ 26, wings08 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	self.alpha = 0.17;
	self.glow_color = 5;
	self.glow_size = 240;
	self.nextthink = (time + 0.05);
};

void() wings08 = [ 27, wings09 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	sound(self, CHAN_WEAPON, "soul/wingsflap.wav", 0.9, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.19;
	self.glow_color = 5;
	self.glow_size = 280;
	self.nextthink = (time + 0.05);
};

void() wings09 = [ 28, wings10 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	self.alpha = 0.21;
	self.glow_color = 5;
	self.glow_size = 320;
	self.nextthink = (time + 0.05);
};

void() wings10 = [ 29, wings11 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.23;
	self.glow_color = 5;
	self.glow_size = 360;
	self.nextthink = (time + 0.05);
};

void() wings11 = [ 30, wings12 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	self.alpha = 0.25;
	self.glow_color = 5;
	self.glow_size = 400;
	self.nextthink = (time + 0.05);
};

void() wings12 = [ 31, wings13 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.27;
	self.glow_color = 5;
	self.glow_size = 440;
	self.nextthink = (time + 0.05);
};

void() wings13 = [ 32, wings14 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	self.alpha = 0.29;
	self.glow_color = 5;
	self.glow_size = 444;
	self.nextthink = (time + 0.05);
};

void() wings14 = [ 33, wings15 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.31;
	self.nextthink = (time + 0.05);
};

void() wings15 = [ 34, wings16 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.33;
	self.nextthink = (time + 0.05);
};

void() wings16 = [ 20, wings17 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.35;
	self.nextthink = (time + 0.05);
};

void() wings17 = [ 21, wings18 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.37;
	self.nextthink = (time + 0.05);
};

void() wings18 = [ 22, wings19 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.39;
	self.nextthink = (time + 0.05);
};

void() wings19 = [ 23, wings20 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.41;
	self.nextthink = (time + 0.05);
};

void() wings20 = [ 24, wings21 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.43;
	self.nextthink = (time + 0.05);
};

void() wings21 = [ 25, wings22 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.45;
	self.nextthink = (time + 0.05);
};

void() wings22 = [ 26, wings23 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.47;
	self.nextthink = (time + 0.05);
};

void() wings23 = [ 27, wings24 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	sound(self, CHAN_WEAPON, "soul/wingsflap.wav", 1, 1);
	self.alpha = 0.49;
	self.nextthink = (time + 0.05);
};

void() wings24 = [ 28, wings25 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.51;
	self.nextthink = (time + 0.05);
};

void() wings25 = [ 29, wings26 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.53;
	self.nextthink = (time + 0.05);
};

void() wings26 = [ 30, wings27 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.velocity = '0 0 25';
	self.alpha = 0.55;
	self.nextthink = (time + 0.05);
};

void() wings27 = [ 31, wings28 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.57;
	self.nextthink = (time + 0.05);
};

void() wings28 = [ 74, wings29 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.6;
	self.nextthink = (time + 0.05);
};

void() wings29 = [ 75, wings30 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings30 = [ 76, wings31 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings31 = [ 35, wings32 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings32 = [ 36, wings33 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	sound(self, CHAN_VOICE, "soul/wingshot.wav", 1, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings33 = [ 37, wings34 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings34 = [ 38, wings35 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings35 = [ 39, wings36 ]
{
	local vector offang;
	local vector org;
	local vector dir;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = (self.origin + (v_right * -13)) + (v_up * 7);
	dir = (self.enemy.origin + '0 0 16') - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 320)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		LightningDamage(org, trace_endpos, self, 5);
	}
	self.nextthink = (time + 0.05);
};

void() wings36 = [ 40, wings37 ]
{
	local vector faceplayer1;
	local vector faceplayer2;
	local vector dir;
	local vector vtemp;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
	if (((self.has_fired >= 1) && (self.has_fired < 3)))
	{
		vtemp = self.enemy.origin + '0 0 10';
		dir = normalize((vtemp - self.origin));
		self.velocity = (dir * 110);
	}
};

void() wings37 = [ 41, wings38 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings38 = [ 42, wings39 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings39 = [ 43, wings40 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings40 = [ 44, wings41 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings41 = [ 45, wings42 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings42 = [ 46, wings43 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings43 = [ 47, wings44 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	sound(self, CHAN_WEAPON, "soul/wingsflap.wav", 1, 1);
	self.nextthink = (time + 0.05);
};

void() wings44 = [ 48, wings45 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings45 = [ 49, wings46 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings46 = [ 50, wings47 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings47 = [ 51, wings48 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings48 = [ 52, wings49 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings49 = [ 53, wings50 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings50 = [ 54, wings51 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings51 = [ 55, wings52 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings52 = [ 56, wings53 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings53 = [ 57, wings54 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings54 = [ 58, wings55 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings55 = [ 59, wings56 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings56 = [ 60, wings57 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings57 = [ 61, wings58 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings58 = [ 62, wings59 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	sound(self, CHAN_VOICE, "soul/wingshot.wav", 1, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() wings59 = [ 63, wings60 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings60 = [ 64, wings61 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings61 = [ 65, wings62 ]
{
	local vector org;
	local vector offang;
	local vector dir;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = ((self.origin + (v_right * 3)) + (v_up * -6)) + (v_forward * 20);
	dir = (self.enemy.origin + '0 0 16') - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 320)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		LightningDamage(org, trace_endpos, self, 5);
	}
	self.nextthink = (time + 0.05);
};

void() wings62 = [ 66, wings63 ]
{
	local vector dir;
	local vector vtemp;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
	if (((self.has_fired >= 1) && (self.has_fired < 3)))
	{
		vtemp = self.enemy.origin + '0 0 10';
		dir = normalize((vtemp - self.origin));
		self.velocity = (dir * 110);
		self.think = wings01;
		self.has_fired = (self.has_fired + 1);
	}
};

void() wings63 = [ 67, wings64 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings64 = [ 68, wings65 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	sound(self, CHAN_WEAPON, "soul/wingsflap.wav", 1, 1);
	self.nextthink = (time + 0.05);
};

void() wings65 = [ 69, wings66 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings66 = [ 70, wings67 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings67 = [ 71, wings68 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() wings68 = [ 72, wings69 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.56;
	self.nextthink = (time + 0.05);
};

void() wings69 = [ 73, wings70 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.52;
	self.nextthink = (time + 0.05);
};

void() wings70 = [ 0, wings71 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.48;
	self.nextthink = (time + 0.05);
};

void() wings71 = [ 1, wings72 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.44;
	self.glow_color = 5;
	self.glow_size = 420;
	self.nextthink = (time + 0.05);
};

void() wings72 = [ 2, wings73 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.4;
	self.glow_color = 5;
	self.glow_size = 400;
	self.nextthink = (time + 0.05);
};

void() wings73 = [ 3, wings74 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.36;
	self.nextthink = (time + 0.05);
};

void() wings74 = [ 4, wings75 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.32;
	self.nextthink = (time + 0.05);
};

void() wings75 = [ 5, wings76 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.28;
	self.nextthink = (time + 0.05);
};

void() wings76 = [ 6, wings77 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.24;
	self.nextthink = (time + 0.05);
};

void() wings77 = [ 7, wings78 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.2;
	self.nextthink = (time + 0.05);
};

void() wings78 = [ 8, wings79 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.16;
	self.nextthink = (time + 0.05);
};

void() wings79 = [ 9, wings80 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.12;
	self.nextthink = (time + 0.05);
};

void() wings80 = [ 10, wings81 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.08;
	self.nextthink = (time + 0.05);
};

void() wings81 = [ 11, wings82 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.04;
	self.nextthink = (time + 0.05);
};

void() wings82 = [ 12, wings83 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.01;
	self.nextthink = (time + 0.05);
};

void() wings83 = [ 13, wings84 ]
{
	if ((self.has_fired > 0))
	{
		te_customflash(self.origin, 600, 0.7, '0.5 0.5 0.5');
		sound(self, CHAN_WEAPON, "soul/flash.wav", 0.6, 4);
		particleeffectnum(/*52287i*/"multigrenade_explosion_nodebris");
		pointparticles(particleeffectnum(/*52287i*/"multigrenade_explosion_nodebris"), (self.origin - '0 0 16'), VEC_ORIGIN, 1);
		particleeffectnum(/*15151i*/"blood_monster_gib");
		pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), (self.origin - '0 0 16'), VEC_ORIGIN, 1);
		sendParticle("blood_corpse_gib", (self.origin - '0 0 16'), VEC_ORIGIN, 1);
	}
	self.alpha = -1;
	self.glow_color = 5;
	self.glow_size = 1;
	self.nextthink = (time + 0.03);
};

void() wings84 = [ 14, wings85 ]
{
	local vector org;
	local vector destin;
	local vector dir;
	local float zufall;
	local float souldmg;

	zufall = random();
	if ((zufall > 0.5))
	{
		destin = self.origin - '0 10 30';
	}
	else
	{
		destin = self.origin - '8 8 30';
	}
	org = self.origin + '0 0 -23';
	dir = destin - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 320)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		souldmg = rint((3.5 + (2 * random())));
		LightningDamage(org, trace_endpos, self, souldmg);
	}
	self.nextthink = (time + 0.05);
};

void() wings85 = [ 15, wings86 ]
{
	local vector org;
	local vector destin;
	local vector dir;
	local float zufall;
	local float souldmg;

	zufall = random();
	if ((zufall > 0.5))
	{
		destin = self.origin - '0 -10 30';
	}
	else
	{
		destin = self.origin - '-8 -8 30';
	}
	org = self.origin + '0 0 -23';
	dir = destin - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 320)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		souldmg = rint((3.5 + (2 * random())));
		LightningDamage(org, trace_endpos, self, souldmg);
	}
	self.nextthink = (time + 0.05);
};

void() wings86 = [ 16, wings87 ]
{
	local vector org;
	local vector destin;
	local vector dir;
	local float zufall;
	local float souldmg;

	zufall = random();
	if ((zufall > 0.5))
	{
		destin = self.origin - '10 0 30';
	}
	else
	{
		destin = self.origin - '8 -8 30';
	}
	org = self.origin + '0 0 -23';
	dir = destin - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 320)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		souldmg = rint((3.5 + (2 * random())));
		LightningDamage(org, trace_endpos, self, souldmg);
	}
	self.nextthink = (time + 0.05);
};

void() wings87 = [ 17, wings88 ]
{
	local vector org;
	local vector destin;
	local vector dir;
	local float zufall;
	local float souldmg;

	zufall = random();
	if ((zufall > 0.5))
	{
		destin = self.origin - '-10 0 30';
	}
	else
	{
		destin = self.origin - '-8 8 30';
	}
	org = self.origin + '0 0 -23';
	dir = destin - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 320)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		souldmg = rint((3.5 + (2 * random())));
		LightningDamage(org, trace_endpos, self, souldmg);
	}
	self.nextthink = (time + 0.05);
};

void() wings88 = [ 18, wingsend ]
{
	local vector org;
	local vector destin;
	local vector dir;
	local float souldmg;
	local entity item;

	destin = self.origin - '0 0 30';
	org = self.origin + '0 0 -23';
	dir = destin - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 320)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		souldmg = rint((3.5 + (2 * random())));
		LightningDamage(org, trace_endpos, self, souldmg);
	}
	self.nextthink = (time + 0.04);
	if ((self.has_fired > 0))
	{
		item = spawn();
		item.origin = (self.origin - '0 0 23');
		item.flags = FL_ITEM;
		item.solid = SOLID_TRIGGER;
		item.movetype = MOVETYPE_TOSS;
		item.classname = "item_artifact_invisibility";
		item.has_fired = 1;
		item.think = item_artifact_invisibility;
		item.nextthink = 0.000100;
	}
};

void() nowingsattack01 = [ 20, nowingsattack02 ]
{
	self.alpha = 0.05;
	self.glow_color = 5;
	self.glow_size = 20;
	self.nextthink = (time + 0.05);
};

void() nowingsattack02 = [ 21, nowingsattack03 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.07;
	self.glow_color = 5;
	self.glow_size = 60;
	self.nextthink = (time + 0.05);
};

void() nowingsattack03 = [ 22, nowingsattack04 ]
{
	sound(self, CHAN_VOICE, "soul/awake.wav", 0.6, 4);
	self.alpha = 0.09;
	self.glow_color = 5;
	self.glow_size = 100;
	self.nextthink = (time + 0.05);
};

void() nowingsattack04 = [ 23, nowingsattack05 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.11;
	self.glow_color = 5;
	self.glow_size = 120;
	self.nextthink = (time + 0.05);
};

void() nowingsattack05 = [ 24, nowingsattack06 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	self.alpha = 0.13;
	self.glow_color = 5;
	self.glow_size = 160;
	self.nextthink = (time + 0.05);
};

void() nowingsattack06 = [ 25, nowingsattack07 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.15;
	self.glow_color = 5;
	self.glow_size = 200;
	self.nextthink = (time + 0.05);
};

void() nowingsattack07 = [ 26, nowingsattack08 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	self.alpha = 0.17;
	self.glow_color = 5;
	self.glow_size = 240;
	self.nextthink = (time + 0.05);
};

void() nowingsattack08 = [ 27, nowingsattack09 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	sound(self, CHAN_WEAPON, "soul/wingsflap.wav", 0.9, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.19;
	self.glow_color = 5;
	self.glow_size = 280;
	self.nextthink = (time + 0.05);
};

void() nowingsattack09 = [ 28, nowingsattack10 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	self.alpha = 0.21;
	self.glow_color = 5;
	self.glow_size = 320;
	self.nextthink = (time + 0.05);
};

void() nowingsattack10 = [ 29, nowingsattack11 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.23;
	self.glow_color = 5;
	self.glow_size = 360;
	self.nextthink = (time + 0.05);
};

void() nowingsattack11 = [ 30, nowingsattack12 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	self.alpha = 0.25;
	self.glow_color = 5;
	self.glow_size = 400;
	self.nextthink = (time + 0.05);
};

void() nowingsattack12 = [ 31, nowingsattack13 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.27;
	self.glow_color = 5;
	self.glow_size = 440;
	self.nextthink = (time + 0.05);
};

void() nowingsattack13 = [ 32, nowingsattack14 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	self.alpha = 0.29;
	self.glow_color = 5;
	self.glow_size = 444;
	self.nextthink = (time + 0.05);
};

void() nowingsattack14 = [ 33, nowingsattack15 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.31;
	self.nextthink = (time + 0.05);
};

void() nowingsattack15 = [ 34, nowingsattack16 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.33;
	self.nextthink = (time + 0.05);
};

void() nowingsattack16 = [ 20, nowingsattack17 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.35;
	self.nextthink = (time + 0.05);
};

void() nowingsattack17 = [ 21, nowingsattack18 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.37;
	self.nextthink = (time + 0.05);
};

void() nowingsattack18 = [ 22, nowingsattack19 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.39;
	self.nextthink = (time + 0.05);
};

void() nowingsattack19 = [ 23, nowingsattack20 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.41;
	self.nextthink = (time + 0.05);
};

void() nowingsattack20 = [ 24, nowingsattack21 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.43;
	self.nextthink = (time + 0.05);
};

void() nowingsattack21 = [ 25, nowingsattack22 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.45;
	self.nextthink = (time + 0.05);
};

void() nowingsattack22 = [ 26, nowingsattack23 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.47;
	self.nextthink = (time + 0.05);
};

void() nowingsattack23 = [ 27, nowingsattack24 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	sound(self, CHAN_WEAPON, "soul/wingsflap.wav", 1, 1);
	self.alpha = 0.49;
	self.nextthink = (time + 0.05);
};

void() nowingsattack24 = [ 28, nowingsattack25 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.51;
	self.nextthink = (time + 0.05);
};

void() nowingsattack25 = [ 29, nowingsattack26 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.53;
	self.nextthink = (time + 0.05);
};

void() nowingsattack26 = [ 30, nowingsattack27 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.velocity = '0 0 25';
	self.alpha = 0.55;
	self.nextthink = (time + 0.05);
};

void() nowingsattack27 = [ 31, nowingsattack28 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.57;
	self.nextthink = (time + 0.05);
};

void() nowingsattack28 = [ 32, nowingsattack29 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.alpha = 0.6;
	self.nextthink = (time + 0.05);
};

void() nowingsattack29 = [ 33, nowingsattack30 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack30 = [ 34, nowingsattack31 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack31 = [ 20, nowingsattack32 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack32 = [ 21, nowingsattack33 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack33 = [ 22, nowingsattack34 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack34 = [ 23, nowingsattack35 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack35 = [ 24, nowingsattack36 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack36 = [ 25, nowingsattack37 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack37 = [ 26, nowingsattack38 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack38 = [ 27, nowingsattack39 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	sound(self, CHAN_WEAPON, "soul/wingsflap.wav", 0.9, 1);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack39 = [ 28, nowingsattack40 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack40 = [ 29, nowingsattack41 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack41 = [ 30, nowingsattack42 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack42 = [ 31, nowingsattack43 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack43 = [ 32, nowingsattack44 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack44 = [ 33, nowingsattack45 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack45 = [ 34, nowingsattack46 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack46 = [ 20, nowingsattack47 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack47 = [ 21, nowingsattack48 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack48 = [ 22, nowingsattack49 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack49 = [ 23, nowingsattack50 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack50 = [ 24, nowingsattack51 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack51 = [ 25, nowingsattack52 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack52 = [ 26, nowingsattack53 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack53 = [ 27, nowingsattack54 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	sound(self, CHAN_WEAPON, "soul/wingsflap.wav", 0.9, 1);
	self.nextthink = (time + 0.05);
};

void() nowingsattack54 = [ 28, nowingsattack55 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack55 = [ 29, nowingsattack56 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack56 = [ 30, nowingsattack57 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack57 = [ 31, nowingsattack58 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack58 = [ 32, nowingsattack59 ]
{
	local vector faceplayer1;
	local vector faceplayer2;

	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	self.angles = vectoangles(faceplayer2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack59 = [ 33, nowingsattack60 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack60 = [ 34, nowingsattack61 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack61 = [ 20, nowingsattack62 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack62 = [ 21, nowingsattack63 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack63 = [ 22, nowingsattack64 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack64 = [ 23, nowingsattack65 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack65 = [ 24, nowingsattack66 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack66 = [ 25, nowingsattack67 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack67 = [ 26, nowingsattack68 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack68 = [ 27, nowingsattack69 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	sound(self, CHAN_WEAPON, "soul/wingsflap.wav", 1, 1);
	self.nextthink = (time + 0.05);
};

void() nowingsattack69 = [ 28, nowingsattack70 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.nextthink = (time + 0.05);
};

void() nowingsattack70 = [ 29, nowingsattack71 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.56;
	self.nextthink = (time + 0.05);
};

void() nowingsattack71 = [ 30, nowingsattack72 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.52;
	self.glow_color = 5;
	self.glow_size = 420;
	self.nextthink = (time + 0.05);
};

void() nowingsattack72 = [ 31, nowingsattack73 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.48;
	self.glow_color = 5;
	self.glow_size = 400;
	self.nextthink = (time + 0.05);
};

void() nowingsattack73 = [ 32, nowingsattack74 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.44;
	self.nextthink = (time + 0.05);
};

void() nowingsattack74 = [ 33, nowingsattack75 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.4;
	self.nextthink = (time + 0.05);
};

void() nowingsattack75 = [ 34, nowingsattack76 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.36;
	self.nextthink = (time + 0.05);
};

void() nowingsattack76 = [ 20, nowingsattack77 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.32;
	self.nextthink = (time + 0.05);
};

void() nowingsattack77 = [ 21, nowingsattack78 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.28;
	self.nextthink = (time + 0.05);
};

void() nowingsattack78 = [ 22, nowingsattack79 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.24;
	self.nextthink = (time + 0.05);
};

void() nowingsattack79 = [ 23, nowingsattack80 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.2;
	self.nextthink = (time + 0.05);
};

void() nowingsattack80 = [ 24, nowingsattack81 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.16;
	self.nextthink = (time + 0.05);
};

void() nowingsattack81 = [ 25, nowingsattack82 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.12;
	self.nextthink = (time + 0.05);
};

void() nowingsattack82 = [ 26, nowingsattack83 ]
{
	sendParticle("soulwings", self.origin, VEC_ORIGIN, 2);
	self.alpha = 0.07;
	self.nextthink = (time + 0.05);
};

void() nowingsattack83 = [ 27, nowingsattack84 ]
{
	self.alpha = -1;
	self.glow_color = 5;
	self.glow_size = 1;
	self.nextthink = (time + 0.03);
};

void() nowingsattack84 = [ 28, nowingsattack85 ]
{
	local vector org;
	local vector destin;
	local vector dir;
	local float zufall;
	local float souldmg;

	zufall = random();
	if ((zufall > 0.5))
	{
		destin = self.origin - '0 10 30';
	}
	else
	{
		destin = self.origin - '8 8 30';
	}
	org = self.origin + '0 0 -23';
	dir = destin - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 320)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		souldmg = rint((3.5 + (2 * random())));
		LightningDamage(org, trace_endpos, self, souldmg);
	}
	self.nextthink = (time + 0.05);
};

void() nowingsattack85 = [ 29, nowingsattack86 ]
{
	local vector org;
	local vector destin;
	local vector dir;
	local float zufall;
	local float souldmg;

	zufall = random();
	if ((zufall > 0.5))
	{
		destin = self.origin - '0 -10 30';
	}
	else
	{
		destin = self.origin - '-8 -8 30';
	}
	org = self.origin + '0 0 -23';
	dir = destin - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 174)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		souldmg = rint((3.5 + (2 * random())));
		LightningDamage(org, trace_endpos, self, souldmg);
	}
	self.nextthink = (time + 0.05);
};

void() nowingsattack86 = [ 30, nowingsattack87 ]
{
	local vector org;
	local vector destin;
	local vector dir;
	local float zufall;
	local float souldmg;

	zufall = random();
	if ((zufall > 0.5))
	{
		destin = self.origin - '10 0 30';
	}
	else
	{
		destin = self.origin - '8 -8 30';
	}
	org = self.origin + '0 0 -23';
	dir = destin - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 174)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		souldmg = rint((3.5 + (2 * random())));
		LightningDamage(org, trace_endpos, self, souldmg);
	}
	self.nextthink = (time + 0.05);
};

void() nowingsattack87 = [ 31, nowingsattack88 ]
{
	local vector org;
	local vector destin;
	local vector dir;
	local float zufall;
	local float souldmg;

	zufall = random();
	if ((zufall > 0.5))
	{
		destin = self.origin - '-10 0 30';
	}
	else
	{
		destin = self.origin - '-8 8 30';
	}
	org = self.origin + '0 0 -23';
	dir = destin - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 320)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		souldmg = rint((3.5 + (2 * random())));
		LightningDamage(org, trace_endpos, self, souldmg);
	}
	self.nextthink = (time + 0.05);
};

void() nowingsattack88 = [ 32, wingsend ]
{
	local vector org;
	local vector destin;
	local vector dir;
	local float souldmg;

	destin = self.origin - '0 0 30';
	org = self.origin + '0 0 -23';
	dir = destin - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 320)), TRUE, self);
	WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
	WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
	WriteEntity(MSG_BROADCAST, self);
	WriteCoord(MSG_BROADCAST, org_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, trace_endpos_x);
	WriteCoord(MSG_BROADCAST, 0);
	WriteCoord(MSG_BROADCAST, 0);
	if ((autocvar_quadreplacer == 0))
	{
	}
	else
	{
		souldmg = rint((3.5 + (2 * random())));
		LightningDamage(org, trace_endpos, self, souldmg);
	}
	self.nextthink = (time + 0.04);
};

void(float zet) wings =
{
	local entity soulwings;
	local vector org;
	local vector faceplayer1;
	local vector faceplayer2;
	local vector dir;
	local vector vtemp;

	soulwings = spawn();
	soulwings.owner = self;
	soulwings.enemy = self.enemy;
	soulwings.movetype = MOVETYPE_FLY;
	soulwings.solid = 0;
	faceplayer1 = vectoangles((self.enemy.origin - self.origin));
	makevectors(faceplayer1);
	faceplayer2 = normalize(v_forward);
	soulwings.angles = vectoangles(faceplayer2);
	setmodel(soulwings, "progs/wings.mdl");
	setsize(soulwings, VEC_ORIGIN, VEC_ORIGIN);
	soulwings.touch = SUB_Null;
	soulwings.scale = 1.3;
	soulwings.alpha = 0.03;
	soulwings.colormod = '1.7 0.3 0.3';
	soulwings.effects = EF_FULLBRIGHT;
	org = self.origin;
	setorigin(soulwings, org);
	self.has_fired = 0;
	if ((zet == 27.451))
	{
		soulwings.think = wings01;
		soulwings.has_fired = 1;
		self.has_fired = 1;
		soulwings.movetype = MOVETYPE_NOCLIP;
		vtemp = self.enemy.origin + '0 0 10';
		dir = normalize((vtemp - soulwings.origin));
		soulwings.velocity = (dir * 80);
	}
	else
	{
		random();
		if ((random() > (0.5 + (autocvar_quadreplacer * 0.2))))
		{
			soulwings.think = nowingsattack01;
		}
		else
		{
			soulwings.think = wings01;
		}
	}
	soulwings.nextthink = (time + 0.05);
};

void(string modelname, float modelframe, float zet) soul =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_FLY;
	setmodel(self, modelname);
	self.solid = 0;
	setsize(self, VEC_ORIGIN, VEC_ORIGIN);
	self.frame = modelframe;
	if ((zet != 27.451))
	{
		alt_death000();
	}
	wings(zet);
	Gyro_Object_ClearPhysics(self);
};

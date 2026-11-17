//Decompiled code. Please respect the original copyright.

void() ghost_die1 = [ 0, ghost_die2 ]
{
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 40;
	self.nextthink = (time + 0.13);
	sound(self, CHAN_WEAPON, "ghost/ghost.wav", 1, 3);
};

void() ghost_die2 = [ 1, ghost_die3 ]
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 80;
	self.nextthink = (time + 0.17);
};

void() ghost_die3 = [ 2, ghost_die4 ]
{
	self.alpha = 0.35;
	self.glow_color = 75;
	self.glow_size = 120;
	self.nextthink = (time + 0.17);
};

void() ghost_die4 = [ 3, ghost_die5 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 160;
	self.nextthink = (time + 0.17);
};

void() ghost_die5 = [ 4, ghost_die6 ]
{
	self.alpha = 0.45;
	self.glow_color = 75;
	self.glow_size = 200;
	self.nextthink = (time + 0.17);
};

void() ghost_die6 = [ 5, ghost_die7 ]
{
	self.alpha = 0.5;
	self.glow_color = 75;
	self.glow_size = 250;
	self.nextthink = (time + 0.17);
};

void() ghost_die7 = [ 6, ghost_die8 ]
{
	self.alpha = 0.55;
	self.nextthink = (time + 0.17);
};

void() ghost_die8 = [ 7, ghost_die9 ]
{
	self.alpha = 0.6;
	self.glow_color = 75;
	self.glow_size = 300;
	self.nextthink = (time + 0.17);
};

void() ghost_die9 = [ 7, ghost_die10 ]
{
	self.alpha = 0.65;
	self.glow_color = 75;
	self.glow_size = 330;
	self.nextthink = (time + 0.25);
};

void() ghost_die10 = [ 7, ghost_die11 ]
{
	self.alpha = 0.65;
	self.glow_color = 75;
	self.glow_size = 290;
	self.nextthink = (time + 0.25);
};

void() ghost_die11 = [ 7, ghost_die11 ]
{
	self.alpha = 0.65;
	self.glow_color = 75;
	self.glow_size = 250;
	self.nextthink = (time + 4);
	self.think = SUB_Remove;
};

void() ghost_die0 =
{
	local vector v;
	local vector u;
	local vector o;
	local vector b;

	v_x = self.origin_x;
	u_x = v_x - 40;
	o_x = u_x + 80;
	self.origin_z = (self.origin_z + -15);
	self.velocity = '0 0 60';
	self.avelocity = '0 270 0';
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_NOCLIP;
	setmodel(self, "progs/ghost.mdl");
	self.solid = 0;
	setsize(self, VEC_ORIGIN, VEC_ORIGIN);
	te_particlesnow(u, o, '0 0 60', 35, 20);
	b_x = v_x;
	te_blood(b, '0 120 1000', 15);
	te_blood(b, '120 0 1000', 15);
	te_blood(b, '-120 0 1000', 15);
	te_blood(b, '0 -120 1000', 15);
	ghost_die1();
};

void() ghost_die =
{
	self.scale = 1;
	self.nextthink = (time + 0.1);
	self.think = ghost_die0;
	Gyro_Object_ClearPhysics(self);
};

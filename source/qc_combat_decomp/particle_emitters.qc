//Decompiled code. Please respect the original copyright.

float(entity to, float sendFlags) particle_emitter_sendtocsqc =
{
	WriteByte(MSG_ENTITY, ENT_PARTICLE_EMITTER);
	WriteByte(MSG_ENTITY, sendFlags);
	if ((sendFlags & 1))
	{
		WriteCoord(MSG_ENTITY, self.origin_x);
		WriteCoord(MSG_ENTITY, self.origin_y);
		WriteCoord(MSG_ENTITY, self.origin_z);
		WriteCoord(MSG_ENTITY, self.velocity_x);
		WriteCoord(MSG_ENTITY, self.velocity_y);
		WriteCoord(MSG_ENTITY, self.velocity_z);
		WriteCoord(MSG_ENTITY, self.count);
		WriteCoord(MSG_ENTITY, self.wait);
		WriteString(MSG_ENTITY, self.message);
	}
	return (TRUE);
};

void() particle_emitter_think =
{
	self.SendEntity = particle_emitter_sendtocsqc;
	self.think = SUB_Remove;
	self.nextthink = (time + 0.2);
};

void(string partName, vector partOrg, vector partVel, float amount, float spawntime) sendParticle =
{
	newmis = spawn();
	newmis.message = partName;
	setorigin(newmis, partOrg);
	setmodel(newmis, "progs/s_smoke.spr");
	newmis.alpha = 0.001;
	newmis.velocity = partVel;
	newmis.count = amount;
	newmis.wait = spawntime;
	newmis.think = particle_emitter_think;
	newmis.nextthink = time;
};

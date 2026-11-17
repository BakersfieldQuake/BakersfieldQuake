//Decompiled code. Please respect the original copyright.

void() checkPlayer =
{
	if ((DED_PLR == PLR_CNT))
	{
		DED_PLR = 0;
		respawn();
	}
};

void() revivePlayer =
{
	local entity findplr;

	findplr.owner = self;
	findplr = findradius(self.origin, 100);
	while (findplr)
	{
		if ((findplr.classname == "player"))
		{
			self.revivetimer = (self.revivetimer + 1);
			if ((self.revivetimer == 15))
			{
				DED_PLR = DED_PLR - 1;
				respawn();
				self.revivetimer = 0;
			}
		}
	}
};

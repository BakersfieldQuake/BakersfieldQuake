// written by mm_tools/build_megaman_yeet_vote.py (glow dimmed for combat clarity)

progs/mmy_rig_steel
{
	cull none
	{
		map progs/mmy_rig_steel
		rgbGen lightingDiffuse
	}
}

progs/mmy_fx
{
	cull none
	{
		map progs/mmy_fx
		blendfunc add
		rgbGen const ( 0.25 0.25 0.25 )
	}
}
